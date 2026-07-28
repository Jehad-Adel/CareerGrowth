"""Sync `knowledge_base/` into the database.

    uv run python -m app.cli.ingest_knowledge
    uv run python -m app.cli.ingest_knowledge --dry-run
    uv run python -m app.cli.ingest_knowledge --force

Run after editing the corpus. Safe to re-run: unchanged entries are not
re-embedded, so a second run costs nothing.

A CLI rather than a route on purpose. Ingestion writes the one table with no
owner, and the only way that stays safe is if no request can reach it.
"""

import argparse
import sys
from pathlib import Path

from app.ai import embeddings
from app.ai.loaders.knowledge_base import load_knowledge_base
from app.db import get_sessionmaker
from app.services import knowledge_service


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=knowledge_service.DEFAULT_ROOT,
        help="Corpus directory (default: knowledge_base/ at the repo root).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and report, touching neither the embedding API nor the database.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-embed every entry, ignoring content hashes.",
    )
    parser.add_argument(
        "--per-minute",
        type=int,
        default=embeddings.FREE_TIER_CONTENTS_PER_MINUTE,
        help=(
            "Embedding budget in contents per minute (default: %(default)s, the "
            "free tier's). Raise on a paid tier; 0 disables pacing."
        ),
    )
    args = parser.parse_args(argv)

    try:
        entries, skipped = load_knowledge_base(args.root)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"parsed {len(entries)} entries from {args.root}")
    if skipped:
        print(f"warning: {len(skipped)} file(s) produced no entries:", file=sys.stderr)
        for name in skipped:
            print(f"  - {name}", file=sys.stderr)

    if args.dry_run:
        by_category: dict[str, int] = {}
        for entry in entries:
            by_category[entry.category] = by_category.get(entry.category, 0) + 1
        for category, count in sorted(by_category.items()):
            print(f"  {count:4d}  {category}")
        return 0

    if not entries:
        # Wiping the corpus because a path was mistyped is not a thing this
        # should do quietly, and ingest's stale-entry sweep would do exactly
        # that.
        print("error: no entries parsed; refusing to sync an empty corpus", file=sys.stderr)
        return 1

    if args.per_minute > 0:
        # Said up front because the wait is the normal path, not a hang: 291
        # entries against the free tier's 100/minute takes about three
        # minutes, and a silent pause looks like a crash.
        minutes = len(entries) / args.per_minute
        print(
            f"pacing at {args.per_minute} contents/minute "
            f"(~{minutes:.0f} min if nothing is cached); safe to interrupt and re-run"
        )

    db = get_sessionmaker()()
    try:
        counts = knowledge_service.ingest(
            db, args.root, force=args.force, per_minute=args.per_minute
        )
    except KeyboardInterrupt:
        # Each batch was committed as it landed, so this is a pause, not a
        # loss. Saying so is the difference between re-running and panicking.
        print("\ninterrupted — everything embedded so far is saved; re-run to resume")
        return 130
    finally:
        db.close()

    print(
        f"done: {counts['written']} written, {counts['unchanged']} unchanged, "
        f"{counts['deleted']} removed"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

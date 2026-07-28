"""Ingest and retrieval for the shared `knowledge_base/` corpus.

The counterpart to `rag_service`, and the difference is ownership. That module
serves documents a single profile produced, and every query filters on
`profile_id` because a leak there is one user reading another's CV. This one
serves editorial content the team wrote, identical for everyone, so there is
nothing to filter — and nothing user-supplied ever enters it. Ingestion runs
from a CLI against files in the repo, never from a request.
"""

import hashlib
import time
from collections import deque
from pathlib import Path
from typing import Callable

from sqlalchemy import delete, func, select, tuple_
from sqlalchemy.orm import Session, defer

from app.ai import embeddings
from app.ai.loaders.knowledge_base import KnowledgeEntry, load_knowledge_base
from app.logging import get_logger
from app.models import KnowledgeChunk

log = get_logger(__name__)

# The corpus lives at the repo root, above the backend package. It is
# deliberately not in the Docker image — the build context is `backend/`, and
# the running API only reads the ingested rows out of Postgres. Ingestion runs
# from a checkout, where this path resolves; in a container it does not, and
# the CLI says so rather than syncing nothing.
DEFAULT_ROOT = Path(__file__).resolve().parents[3] / "knowledge_base"

TOP_K = 3
# Bounds how much curated text reaches the prompt. The personal context is
# what the user actually asked about; general guidance supplements it and must
# not crowd it out.
MAX_CONTEXT_CHARS = 4_000

# The embedding API is called in batches. Kept well under the per-minute
# budget so a single batch can never exhaust it outright, which would make the
# pacer's job impossible rather than merely slow.
EMBED_BATCH = 25

# A 429 is not a failure here, just an early arrival. Retries are bounded so a
# genuinely revoked key does not spin forever.
MAX_RATE_LIMIT_RETRIES = 5
# Added to the provider's own hint. Its clock and ours are not the same clock,
# and coming back a hair early costs another full window.
RETRY_GRACE_SECONDS = 1.0


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class _Pacer:
    """Keeps a bulk caller under a per-minute budget counted in *contents*.

    The free tier's limit is 100 contents per minute, so a run of 291 entries
    cannot finish faster than about three minutes no matter how it is batched.
    Waiting for the window is therefore the normal path, not the error path.

    A sliding window rather than a fixed one: spending the whole budget and
    sleeping a flat 60s would idle through most of a minute that had already
    partly elapsed.
    """

    def __init__(
        self,
        per_minute: int,
        sleep: Callable[[float], None] = time.sleep,
        now: Callable[[], float] = time.monotonic,
    ):
        # The clock is injected alongside sleep, not just sleep: a test that
        # stubs only sleep leaves this spinning forever, because the window it
        # is waiting on never moves.
        self.per_minute = per_minute
        self._sleep = sleep
        self._now = now
        self._spent: deque[tuple[float, int]] = deque()

    def take(self, count: int) -> float:
        """Block until `count` more contents fit in the window. Returns the wait."""
        if self.per_minute <= 0:
            return 0.0

        waited = 0.0
        while True:
            now = self._now()
            while self._spent and now - self._spent[0][0] >= 60.0:
                self._spent.popleft()

            used = sum(n for _, n in self._spent)
            # A batch larger than the whole budget can never fit; letting it
            # through and taking the 429 beats deadlocking on it.
            if not self._spent or used + count <= self.per_minute:
                self._spent.append((now, count))
                return waited

            # Wait for the oldest spend to age out of the window, which is the
            # soonest anything can change.
            delay = 60.0 - (now - self._spent[0][0])
            self._sleep(delay)
            waited += delay


def _embed_with_backoff(
    texts: list[str], sleep: Callable[[float], None] = time.sleep
) -> list[list[float]]:
    """Embed a batch, waiting out the quota if the provider says to.

    The pacer keeps us under the budget we know about; this covers the one we
    do not — another process on the same key, or a limit that is not the
    documented one.
    """
    for attempt in range(MAX_RATE_LIMIT_RETRIES):
        try:
            return embeddings.embed_documents(texts)
        except embeddings.RateLimited as exc:
            if attempt == MAX_RATE_LIMIT_RETRIES - 1:
                raise
            delay = exc.retry_after + RETRY_GRACE_SECONDS
            log.warning(
                "knowledge_rate_limited",
                sleeping_seconds=round(delay, 1),
                attempt=attempt + 1,
            )
            sleep(delay)
    raise AssertionError("unreachable")


def _existing_hashes(db: Session) -> dict[tuple[str, int], str]:
    rows = db.execute(
        select(
            KnowledgeChunk.source, KnowledgeChunk.chunk_index, KnowledgeChunk.content_hash
        )
    ).all()
    return {(source, index): digest for source, index, digest in rows}


def _existing_keys(db: Session) -> set[tuple[str, int]]:
    """Identity columns only — the stale sweep never looks at a hash."""
    return {
        (source, index)
        for source, index in db.execute(
            select(KnowledgeChunk.source, KnowledgeChunk.chunk_index)
        ).all()
    }


def ingest(
    db: Session,
    root: str | Path | None = None,
    *,
    force: bool = False,
    per_minute: int = embeddings.FREE_TIER_CONTENTS_PER_MINUTE,
) -> dict[str, int]:
    """Load the corpus from disk and sync it into the database.

    Idempotent by content hash: an entry whose text has not changed is left
    alone and never re-embedded, so re-running this after editing one file
    costs one file's worth of API calls rather than the corpus's.

    Entries that vanished from disk are deleted, so the table always reflects
    the files rather than accumulating whatever was ever true.

    Paced to stay inside the embedding quota, and each batch is committed as
    it lands. A run that dies anyway — network, a revoked key, Ctrl-C — leaves
    everything already embedded persisted, and the next run resumes from there
    rather than starting over.

    Args:
        force: re-embed everything, ignoring hashes. For a change in the
            embedding model or the entry rendering, where the text on disk is
            unchanged but its vector is no longer comparable.
        per_minute: contents-per-minute budget. Raise it on a paid tier; zero
            disables pacing.

    Returns counts of what happened, for the CLI to print.
    """
    entries, skipped = load_knowledge_base(root or DEFAULT_ROOT)
    if skipped:
        # Not fatal: one unreadable file must not block the other 78. It is
        # logged loudly because a silently dropped file is invisible until
        # someone notices the chat has stopped citing a whole topic.
        log.warning("knowledge_files_skipped", files=skipped, count=len(skipped))

    known = {} if force else _existing_hashes(db)
    seen: set[tuple[str, int]] = set()
    # (entry, chunk_index, content_hash). The hash is carried rather than
    # recomputed at write time — it is already known from the skip check.
    pending: list[tuple[KnowledgeEntry, int, str]] = []

    counts = {"total": len(entries), "unchanged": 0, "written": 0, "deleted": 0}

    # chunk_index is the entry's position within its own file, so editing one
    # file cannot renumber another.
    per_source: dict[str, int] = {}
    for entry in entries:
        index = per_source.get(entry.source, 0)
        per_source[entry.source] = index + 1
        key = (entry.source, index)
        seen.add(key)

        digest = _hash(entry.embed_text)
        if known.get(key) == digest:
            counts["unchanged"] += 1
            continue
        pending.append((entry, index, digest))

    pacer = _Pacer(per_minute)
    for start in range(0, len(pending), EMBED_BATCH):
        batch = pending[start : start + EMBED_BATCH]

        waited = pacer.take(len(batch))
        if waited:
            log.info("knowledge_paused_for_quota", seconds=round(waited, 1))

        vectors = _embed_with_backoff([entry.embed_text for entry, _, _ in batch])

        # Delete-then-insert rather than update: the row is identified by
        # (source, chunk_index) and every other column is being replaced.
        # One statement for the batch, not one per row.
        db.execute(
            delete(KnowledgeChunk).where(
                tuple_(KnowledgeChunk.source, KnowledgeChunk.chunk_index).in_(
                    [(entry.source, index) for entry, index, _ in batch]
                )
            )
        )
        db.add_all(
            KnowledgeChunk(
                category=entry.category,
                source=entry.source,
                chunk_index=index,
                title=entry.title,
                content=entry.text,
                content_hash=digest,
                embedding=vector,
            )
            for (entry, index, digest), vector in zip(batch, vectors)
        )
        # Committed per batch so an API failure halfway through leaves the
        # entries already embedded persisted, and the next run skips them.
        db.commit()
        counts["written"] += len(batch)
        log.info("knowledge_batch_written", written=counts["written"], of=len(pending))

    stale = _existing_keys(db) - seen
    if stale:
        db.execute(
            delete(KnowledgeChunk).where(
                tuple_(KnowledgeChunk.source, KnowledgeChunk.chunk_index).in_(
                    list(stale)
                )
            )
        )
        db.commit()
    counts["deleted"] = len(stale)

    log.info("knowledge_ingested", **counts)
    return counts


def retrieve(
    db: Session, query: str, k: int = TOP_K, vector: list[float] | None = None
) -> list[KnowledgeChunk]:
    """Top-k curated entries for this query.

    No profile filter, unlike `rag_service.retrieve` — see the module
    docstring. Nothing here belongs to a user.

    Args:
        vector: a pre-computed embedding of `query`, shared with the personal
            retrieval that runs alongside this one.
    """
    if not query.strip():
        return []

    # Checked before embedding: until the ingest CLI has run — a fresh deploy,
    # a fresh test database — there is nothing to rank, and paying the
    # embedding API on every chat turn to sort an empty table is pure waste.
    if not db.execute(select(KnowledgeChunk.id).limit(1)).first():
        return []

    if vector is None:
        vector = embeddings.embed_query(query)
    return list(
        db.execute(
            select(KnowledgeChunk)
            # 768 floats per row that nothing downstream reads.
            .options(defer(KnowledgeChunk.embedding))
            .order_by(KnowledgeChunk.embedding.cosine_distance(vector))
            .limit(k)
        ).scalars()
    )


def build_context(chunks: list[KnowledgeChunk]) -> str:
    """Render curated entries as delimited, labelled text for the prompt."""
    if not chunks:
        return ""

    parts: list[str] = []
    budget = MAX_CONTEXT_CHARS
    for chunk in chunks:
        body = chunk.content[:budget]
        if not body:
            break
        parts.append(f"[{chunk.category}: {chunk.title}]\n{body}")
        budget -= len(body)
        if budget <= 0:
            break
    return "\n\n".join(parts)


def corpus_size(db: Session) -> int:
    """How many curated entries are indexed. Zero means ingest never ran."""
    return db.execute(select(func.count(KnowledgeChunk.id))).scalar_one()

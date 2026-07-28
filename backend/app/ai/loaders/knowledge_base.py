"""Reader for the curated `knowledge_base/` corpus.

This is editorial content the team maintains by hand — ATS rules, CV writing
guidance, per-track roadmaps — not anything a user uploads. It is shared by
every profile, which is what separates it from the personal documents in
`rag_service`.

The corpus is JSON in four shapes, and this module's whole job is turning them
into retrieval units. Granularity is the decision that matters: one rule per
chunk, not one file per chunk. A file bundles a dozen unrelated rules, so
embedding it whole produces a vector that is close to everything and decisive
about nothing.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

# Retrieval reads whole entries, so an entry must not be long enough to crowd
# the prompt on its own. Curated rules run ~500 characters; this is a guard
# against a pathological one, not a routine path.
MAX_ENTRY_CHARS = 4_000

# Below this an entry carries a heading and nothing else, and only pollutes
# the results.
MIN_ENTRY_CHARS = 40


@dataclass(frozen=True)
class KnowledgeEntry:
    """One retrievable unit of curated knowledge."""

    # Folder name, e.g. "CV Writing". Doubles as the citation label.
    category: str
    # Path relative to the corpus root, so a bad entry can be traced back.
    source: str
    title: str
    text: str

    @property
    def embed_text(self) -> str:
        """What actually gets embedded — heading included.

        The category and title carry real retrieval signal ("ATS", "LinkedIn"),
        and a rule body often never repeats its own topic word.
        """
        return f"[{self.category}] {self.title}\n{self.text}"


def _clean(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _lines(*parts: str) -> str:
    return "\n".join(part for part in parts if part)


def _bullets(label: str, items: Any) -> str:
    """Render a list field as a labelled block. Empty string if absent."""
    if not isinstance(items, list) or not items:
        return ""
    rendered = [_clean(item) for item in items if _clean(item)]
    return f"{label}: {', '.join(rendered)}" if rendered else ""


def _rule_entries(payload: dict, category: str, source: str) -> Iterator[KnowledgeEntry]:
    """The `{file_metadata, rules}` shape — one entry per rule."""
    for rule in payload.get("rules", []):
        if not isinstance(rule, dict):
            continue
        name = _clean(rule.get("rule_name")) or _clean(rule.get("rule_id"))
        if not name:
            continue

        severity = _clean(rule.get("severity"))
        sub_category = _clean(rule.get("category"))
        heading = " / ".join(part for part in (sub_category, severity) if part)

        do = _clean(rule.get("do"))
        dont = _clean(rule.get("dont"))
        yield KnowledgeEntry(
            category=category,
            source=source,
            title=name,
            text=_lines(
                heading,
                _clean(rule.get("explanation")),
                f"Do: {do}" if do else "",
                f"Do not: {dont}" if dont else "",
                _bullets("ATS keywords", rule.get("ats_keywords")),
            ),
        )

    # Only one file carries this, but dropping it silently is how a corpus
    # quietly loses content nobody notices is gone.
    taxonomy = payload.get("action_verbs_taxonomy")
    if isinstance(taxonomy, dict):
        for group, verbs in taxonomy.items():
            block = _bullets("Verbs", verbs)
            if block:
                yield KnowledgeEntry(
                    category=category,
                    source=source,
                    title=f"Action verbs — {_clean(group).replace('_', ' ')}",
                    text=block,
                )


def _roadmap_url(value: Any) -> str:
    """The roadmap field is a bare URL in some files and an object in others."""
    if isinstance(value, dict):
        name = _clean(value.get("name"))
        url = _clean(value.get("url"))
        return _lines(f"Roadmap: {name}" if name else "", url)
    url = _clean(value)
    return f"Roadmap: {url}" if url else ""


def _topic_entries(payload: dict, category: str, source: str) -> Iterator[KnowledgeEntry]:
    """The learning-track shape — an overview entry plus a resources entry.

    Split in two because the two answer different questions: "what is this
    track and in what order" versus "what should I read". Merged, neither
    retrieves well.
    """
    topic = _clean(payload.get("topic")) or Path(source).stem

    overview = _lines(
        _clean(payload.get("description")),
        _roadmap_url(payload.get("roadmap")),
        _bullets("Learning order", payload.get("learning_order")),
        _bullets("Recommended projects", payload.get("recommended_projects")),
        _bullets("Career paths", payload.get("career_paths")),
    )
    if overview:
        yield KnowledgeEntry(
            category=category,
            source=source,
            title=f"{topic} — learning track",
            text=overview,
        )

    resources = payload.get("resources")
    if isinstance(resources, list) and resources:
        rendered = []
        for item in resources:
            if not isinstance(item, dict):
                continue
            name = _clean(item.get("name"))
            if not name:
                continue
            meta = ", ".join(
                part
                for part in (_clean(item.get("type")), _clean(item.get("level")))
                if part
            )
            url = _clean(item.get("url"))
            rendered.append(
                f"- {name}" + (f" ({meta})" if meta else "") + (f" — {url}" if url else "")
            )
        if rendered:
            yield KnowledgeEntry(
                category=category,
                source=source,
                title=f"{topic} — learning resources",
                text="\n".join(rendered),
            )


def _entries_from_payload(
    payload: Any, category: str, source: str
) -> Iterator[KnowledgeEntry]:
    if isinstance(payload, list):
        for item in payload:
            yield from _entries_from_payload(item, category, source)
        return
    if not isinstance(payload, dict):
        return
    if "rules" in payload or "action_verbs_taxonomy" in payload:
        yield from _rule_entries(payload, category, source)
    elif "topic" in payload:
        yield from _topic_entries(payload, category, source)
    # Any other shape yields nothing. Deliberate: a silently mangled entry in
    # a retrieval corpus is worse than a missing one, and `load` reports the
    # files that produced no entries so a new shape surfaces immediately.


def load_knowledge_base(root: str | Path) -> tuple[list[KnowledgeEntry], list[str]]:
    """Read every JSON file under `root`.

    Returns the entries and the list of files that yielded none — malformed
    JSON, or a shape this module does not know. The caller decides whether
    that is a warning or a failure.

    Raises:
        FileNotFoundError: `root` does not exist.
    """
    root_path = Path(root)
    if not root_path.is_dir():
        raise FileNotFoundError(f"Knowledge base directory not found: {root_path}")

    entries: list[KnowledgeEntry] = []
    skipped: list[str] = []

    for path in sorted(root_path.rglob("*.json")):
        relative = path.relative_to(root_path).as_posix()
        # The immediate folder is the category; files at the root get one
        # named after the corpus rather than an empty string.
        category = path.parent.name if path.parent != root_path else "General"

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            skipped.append(relative)
            continue

        found = [
            entry
            for entry in _entries_from_payload(payload, category, relative)
            if MIN_ENTRY_CHARS <= len(entry.embed_text)
        ]
        if not found:
            skipped.append(relative)
            continue

        entries.extend(
            KnowledgeEntry(
                category=entry.category,
                source=entry.source,
                title=entry.title,
                text=entry.text[:MAX_ENTRY_CHARS],
            )
            for entry in found
        )

    return entries, skipped

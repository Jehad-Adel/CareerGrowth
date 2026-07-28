"""The curated corpus: parsing on disk, and syncing into the database.

The loader tests run against fixtures written here rather than the real
`knowledge_base/`, so an editorial change to the corpus cannot turn these red.
One test does read the real directory — it asserts every file parses, which is
the thing an editorial change genuinely can break.
"""

import json
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.ai.loaders.knowledge_base import load_knowledge_base
from app.db import Base
from app.models import KnowledgeChunk
from app.services import knowledge_service

REAL_CORPUS = Path(__file__).resolve().parents[2] / "knowledge_base"

_RULES_FILE = {
    "file_metadata": {"category": "CV_Writing", "file_name": "mistakes.json"},
    "rules": [
        {
            "rule_id": "CV-ERR-001",
            "rule_name": "No typos",
            "category": "Quality Control",
            "severity": "Critical",
            "explanation": "Typos signal a lack of attention to detail and get CVs rejected.",
            "do": "Proofread before submitting anything.",
            "dont": "Do not submit with spelling errors.",
            "ats_keywords": ["Grammar", "Attention to Detail"],
        },
        {
            "rule_id": "CV-ERR-002",
            "rule_name": "No timeline gaps",
            "severity": "High",
            "explanation": "Unexplained gaps create uncertainty for recruiters and parsers.",
            "do": "Account for every year chronologically in month/year ranges.",
        },
    ],
}

_TOPIC_FILE = {
    "topic": "Docker",
    "description": "Docker packages applications and their dependencies into portable containers.",
    "roadmap": "https://roadmap.sh/docker",
    "resources": [
        {
            "name": "Docker Documentation",
            "url": "https://docs.docker.com/",
            "type": "documentation",
            "level": "beginner",
        }
    ],
}


def _corpus(tmp_path: Path, files: dict[str, object]) -> Path:
    root = tmp_path / "kb"
    for relative, payload in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")
    return root


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def _fake_embeddings(monkeypatch) -> None:
    """Deterministic vectors. The embedding API is never called in tests."""
    monkeypatch.setattr(
        knowledge_service.embeddings,
        "embed_documents",
        lambda texts: [[float(len(t) % 7)] * 8 for t in texts],
    )


def test_a_rules_file_yields_one_entry_per_rule(tmp_path):
    root = _corpus(tmp_path, {"CV Writing/mistakes.json": _RULES_FILE})
    entries, skipped = load_knowledge_base(root)

    assert not skipped
    assert [e.title for e in entries] == ["No typos", "No timeline gaps"]
    assert all(e.category == "CV Writing" for e in entries)
    assert entries[0].source == "CV Writing/mistakes.json"


def test_rule_text_carries_the_do_and_the_dont(tmp_path):
    root = _corpus(tmp_path, {"CV Writing/mistakes.json": _RULES_FILE})
    entries, _ = load_knowledge_base(root)

    text = entries[0].text
    assert "Proofread before submitting" in text
    assert "Do not: Do not submit with spelling errors." in text
    # The heading is in embed_text, not the body, so retrieval can match on
    # the category without the body repeating it.
    assert "[CV Writing] No typos" in entries[0].embed_text


def test_a_topic_file_splits_overview_from_resources(tmp_path):
    root = _corpus(tmp_path, {"Roadmaps/Docker.json": _TOPIC_FILE})
    entries, skipped = load_knowledge_base(root)

    assert not skipped
    assert [e.title for e in entries] == [
        "Docker — learning track",
        "Docker — learning resources",
    ]
    assert "roadmap.sh/docker" in entries[0].text
    assert "Docker Documentation (documentation, beginner)" in entries[1].text


def test_a_root_level_list_is_flattened(tmp_path):
    root = _corpus(tmp_path, {"Roadmaps/DevOps.json": [_TOPIC_FILE]})
    entries, skipped = load_knowledge_base(root)

    assert not skipped
    assert len(entries) == 2


def test_unreadable_and_unknown_files_are_reported_not_swallowed(tmp_path):
    root = _corpus(tmp_path, {"CV Writing/mistakes.json": _RULES_FILE})
    (root / "broken.json").write_text("{not json", encoding="utf-8")
    (root / "alien.json").write_text('{"shape": "unknown"}', encoding="utf-8")

    entries, skipped = load_knowledge_base(root)

    assert len(entries) == 2
    assert sorted(skipped) == ["alien.json", "broken.json"]


def test_a_missing_corpus_directory_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_knowledge_base(tmp_path / "nope")


def test_the_real_corpus_parses_completely():
    """Guards the corpus itself: a new file in a shape the loader does not
    know would otherwise disappear from the chat with no error anywhere."""
    if not REAL_CORPUS.is_dir():
        pytest.skip("knowledge_base/ is not present in this checkout")

    entries, skipped = load_knowledge_base(REAL_CORPUS)

    assert not skipped, f"files produced no entries: {skipped}"
    assert len(entries) > 100
    # Every category folder is represented.
    folders = {p.name for p in REAL_CORPUS.iterdir() if p.is_dir()}
    assert folders <= {e.category for e in entries}


def test_ingest_writes_every_entry(tmp_path, monkeypatch):
    _fake_embeddings(monkeypatch)
    root = _corpus(
        tmp_path,
        {"CV Writing/mistakes.json": _RULES_FILE, "Roadmaps/Docker.json": _TOPIC_FILE},
    )
    db = _session()

    counts = knowledge_service.ingest(db, root)

    assert counts == {"total": 4, "unchanged": 0, "written": 4, "deleted": 0}
    assert knowledge_service.corpus_size(db) == 4
    # chunk_index restarts per file, so editing one file cannot renumber another.
    indexes = {
        (c.source, c.chunk_index) for c in db.query(KnowledgeChunk).all()
    }
    assert indexes == {
        ("CV Writing/mistakes.json", 0),
        ("CV Writing/mistakes.json", 1),
        ("Roadmaps/Docker.json", 0),
        ("Roadmaps/Docker.json", 1),
    }


def test_reingesting_unchanged_content_embeds_nothing(tmp_path, monkeypatch):
    _fake_embeddings(monkeypatch)
    root = _corpus(tmp_path, {"CV Writing/mistakes.json": _RULES_FILE})
    db = _session()
    knowledge_service.ingest(db, root)

    calls: list[list[str]] = []
    monkeypatch.setattr(
        knowledge_service.embeddings,
        "embed_documents",
        lambda texts: calls.append(texts) or [[1.0] * 8 for _ in texts],
    )
    counts = knowledge_service.ingest(db, root)

    assert counts["unchanged"] == 2
    assert counts["written"] == 0
    assert calls == []


def test_force_reembeds_unchanged_content(tmp_path, monkeypatch):
    _fake_embeddings(monkeypatch)
    root = _corpus(tmp_path, {"CV Writing/mistakes.json": _RULES_FILE})
    db = _session()
    knowledge_service.ingest(db, root)

    counts = knowledge_service.ingest(db, root, force=True)

    assert counts["written"] == 2
    assert counts["unchanged"] == 0
    assert knowledge_service.corpus_size(db) == 2


def test_entries_deleted_from_disk_leave_the_table(tmp_path, monkeypatch):
    _fake_embeddings(monkeypatch)
    root = _corpus(
        tmp_path,
        {"CV Writing/mistakes.json": _RULES_FILE, "Roadmaps/Docker.json": _TOPIC_FILE},
    )
    db = _session()
    knowledge_service.ingest(db, root)

    (root / "Roadmaps" / "Docker.json").unlink()
    counts = knowledge_service.ingest(db, root)

    assert counts["deleted"] == 2
    assert knowledge_service.corpus_size(db) == 2
    assert {c.source for c in db.query(KnowledgeChunk).all()} == {
        "CV Writing/mistakes.json"
    }


def test_an_edited_rule_is_rewritten_in_place(tmp_path, monkeypatch):
    _fake_embeddings(monkeypatch)
    edited = json.loads(json.dumps(_RULES_FILE))
    root = _corpus(tmp_path, {"CV Writing/mistakes.json": _RULES_FILE})
    db = _session()
    knowledge_service.ingest(db, root)

    edited["rules"][0]["explanation"] = "Typos are the single fastest way to get filtered out."
    (root / "CV Writing" / "mistakes.json").write_text(
        json.dumps(edited), encoding="utf-8"
    )
    counts = knowledge_service.ingest(db, root)

    assert counts == {"total": 2, "unchanged": 1, "written": 1, "deleted": 0}
    assert knowledge_service.corpus_size(db) == 2
    row = (
        db.query(KnowledgeChunk)
        .filter_by(source="CV Writing/mistakes.json", chunk_index=0)
        .one()
    )
    assert "fastest way to get filtered out" in row.content


class _FakeClock:
    """A clock that only moves when something sleeps.

    Stubbing sleep alone is not enough: the pacer waits on a window measured
    against the clock, so a sleep that does not advance time spins forever.
    """

    def __init__(self) -> None:
        self.t = 0.0
        self.slept: list[float] = []

    def now(self) -> float:
        return self.t

    def sleep(self, seconds: float) -> None:
        self.slept.append(seconds)
        self.t += seconds


def _pacer(per_minute: int) -> tuple[knowledge_service._Pacer, _FakeClock]:
    clock = _FakeClock()
    return (
        knowledge_service._Pacer(per_minute, sleep=clock.sleep, now=clock.now),
        clock,
    )


def test_the_pacer_lets_batches_through_while_budget_remains():
    pacer, clock = _pacer(100)

    assert pacer.take(25) == 0
    assert pacer.take(25) == 0
    assert pacer.take(50) == 0
    assert clock.slept == []


def test_the_pacer_waits_for_the_window_to_slide():
    """The free tier counts *contents*, not requests: a batch of 50 texts
    spends 50 of the 100. Two batches exhaust it, and the third must wait —
    this is exactly the 429 that killed the first real run."""
    pacer, clock = _pacer(100)
    pacer.take(50)
    pacer.take(50)

    waited = pacer.take(50)

    assert waited == 60.0
    assert clock.slept == [60.0]


def test_the_window_slides_rather_than_resetting():
    """A fixed window would sleep a flat 60s after every exhaustion, idling
    through a minute that had already partly elapsed."""
    pacer, clock = _pacer(100)
    pacer.take(100)
    clock.t += 45.0

    assert pacer.take(100) == 15.0


def test_a_zero_budget_disables_pacing():
    pacer, clock = _pacer(0)

    assert pacer.take(10_000) == 0
    assert clock.slept == []


def test_a_batch_bigger_than_the_budget_does_not_deadlock():
    """It can never fit, so waiting for room is waiting forever. Taking the
    429 is the lesser failure."""
    pacer, _ = _pacer(10)

    assert pacer.take(50) == 0


def test_ingest_spends_the_budget_one_batch_at_a_time(tmp_path, monkeypatch):
    """The seam between ingest and the pacer: every batch is declared before
    it is embedded. What happens on exhaustion is the pacer's own tests."""
    _fake_embeddings(monkeypatch)
    rules = {
        "file_metadata": {},
        "rules": [
            {
                "rule_name": f"Rule {i}",
                "explanation": "A sufficiently long explanation to clear the minimum.",
                "do": "Do the thing that this rule is about.",
            }
            for i in range(9)
        ],
    }
    root = _corpus(tmp_path, {"CV Writing/many.json": rules})
    monkeypatch.setattr(knowledge_service, "EMBED_BATCH", 4)

    taken: list[int] = []

    class _RecordingPacer:
        def __init__(self, per_minute: int) -> None:
            taken.append(-per_minute)

        def take(self, count: int) -> float:
            taken.append(count)
            return 0.0

    monkeypatch.setattr(knowledge_service, "_Pacer", _RecordingPacer)
    db = _session()

    counts = knowledge_service.ingest(db, root, per_minute=4)

    assert counts["written"] == 9
    # Budget forwarded, then one take per batch, sized to the batch.
    assert taken == [-4, 4, 4, 1]


def test_a_rate_limited_batch_is_retried_after_the_providers_delay(monkeypatch):
    """A 429 is an early arrival, not a failure. Waiting it out is the whole
    point — the alternative is losing a run that was 90% paid for."""
    slept: list[float] = []
    attempts: list[int] = []

    def flaky(texts):
        attempts.append(1)
        if len(attempts) == 1:
            raise knowledge_service.embeddings.RateLimited("quota", 29.4)
        return [[1.0] * 8 for _ in texts]

    monkeypatch.setattr(knowledge_service.embeddings, "embed_documents", flaky)

    result = knowledge_service._embed_with_backoff(["a"], sleep=slept.append)

    assert result == [[1.0] * 8]
    assert len(attempts) == 2
    # The provider's hint, plus grace — undershooting earns another 429.
    assert slept == [29.4 + knowledge_service.RETRY_GRACE_SECONDS]


def test_persistent_rate_limiting_eventually_gives_up(monkeypatch):
    """A revoked key looks like a rate limit forever. Bounded so it surfaces."""
    calls: list[int] = []

    def always_limited(texts):
        calls.append(1)
        raise knowledge_service.embeddings.RateLimited("quota", 1.0)

    monkeypatch.setattr(
        knowledge_service.embeddings, "embed_documents", always_limited
    )

    with pytest.raises(knowledge_service.embeddings.RateLimited):
        knowledge_service._embed_with_backoff(["a"], sleep=lambda s: None)
    assert len(calls) == knowledge_service.MAX_RATE_LIMIT_RETRIES


def test_work_already_embedded_survives_a_failed_run(tmp_path, monkeypatch):
    """The batch commit is what makes a re-run cheap after a 429 kills the
    process partway through."""
    rules = {
        "file_metadata": {},
        "rules": [
            {
                "rule_name": f"Rule {i}",
                "explanation": "A sufficiently long explanation to clear the minimum.",
                "do": "Do the thing that this rule is about.",
            }
            for i in range(8)
        ],
    }
    root = _corpus(tmp_path, {"CV Writing/many.json": rules})
    monkeypatch.setattr(knowledge_service, "EMBED_BATCH", 4)
    db = _session()

    calls: list[int] = []

    def dies_on_the_second_batch(texts):
        calls.append(1)
        if len(calls) > 1:
            raise RuntimeError("network died")
        return [[float(len(t) % 7)] * 8 for t in texts]

    monkeypatch.setattr(
        knowledge_service.embeddings, "embed_documents", dies_on_the_second_batch
    )
    with pytest.raises(RuntimeError):
        knowledge_service.ingest(db, root, per_minute=0)

    assert knowledge_service.corpus_size(db) == 4

    # The re-run pays for the remaining four only.
    _fake_embeddings(monkeypatch)
    counts = knowledge_service.ingest(db, root, per_minute=0)
    assert counts["unchanged"] == 4
    assert counts["written"] == 4
    assert knowledge_service.corpus_size(db) == 8


def test_retrieval_short_circuits_on_an_empty_corpus(monkeypatch):
    """No embedding call when there is nothing to rank."""
    db = _session()
    monkeypatch.setattr(
        knowledge_service.embeddings,
        "embed_query",
        lambda text: pytest.fail("embedded a query against an empty corpus"),
    )

    assert knowledge_service.retrieve(db, "how do I write a CV") == []


def test_build_context_is_bounded_and_labelled(tmp_path, monkeypatch):
    _fake_embeddings(monkeypatch)
    root = _corpus(tmp_path, {"CV Writing/mistakes.json": _RULES_FILE})
    db = _session()
    knowledge_service.ingest(db, root)

    chunks = db.query(KnowledgeChunk).all()
    context = knowledge_service.build_context(chunks)

    assert "[CV Writing: No typos]" in context
    assert len(context) <= knowledge_service.MAX_CONTEXT_CHARS + 200
    assert knowledge_service.build_context([]) == ""

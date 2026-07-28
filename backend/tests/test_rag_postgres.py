"""Vector retrieval against a real Postgres.

SQLite has no pgvector operators, so `rag_service.retrieve` cannot be
exercised in the main suite. The property that matters most here — one
profile can never retrieve another's chunks — is exactly the kind of thing
that must be tested against the real query planner rather than a stand-in.

Everything runs inside a transaction that is always rolled back, so these
tests write nothing durable even when pointed at the live project.

Run with: uv run pytest -m pg
"""

import uuid

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import CareerProfile, DocumentChunk, KnowledgeChunk
from app.services import knowledge_service, rag_service

pytestmark = pytest.mark.pg

DIMS = rag_service.embeddings.DIMENSIONS


def _vec(seed: float) -> list[float]:
    """A unit vector that leans on one axis, so ordering is predictable."""
    v = [0.01] * DIMS
    v[int(seed) % DIMS] = 1.0
    norm = sum(x * x for x in v) ** 0.5
    return [x / norm for x in v]


@pytest.fixture
def db():
    settings = get_settings()
    url = settings.migration_database_url
    if not url or url.startswith("sqlite"):
        pytest.skip("needs a Postgres DATABASE_URL")

    engine = create_engine(url)
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    try:
        yield session
    finally:
        session.close()
        # Always roll back: these tests must leave no trace.
        transaction.rollback()
        connection.close()


@pytest.fixture
def profiles(db):
    made = []
    for _ in range(2):
        p = CareerProfile(user_id=uuid.uuid4(), email="t@example.com")
        db.add(p)
        made.append(p)
    db.flush()
    return made


def _stub_embeddings(monkeypatch, mapping: dict[str, float]):
    monkeypatch.setattr(
        rag_service.embeddings,
        "embed_documents",
        lambda texts: [_vec(mapping.get(t, 0)) for t in texts],
    )
    monkeypatch.setattr(
        rag_service.embeddings, "embed_query", lambda t: _vec(mapping.get(t, 0))
    )


def test_pgvector_extension_is_installed(db):
    version = db.execute(
        text("select extversion from pg_extension where extname='vector'")
    ).scalar()
    assert version, "pgvector is not installed; migration 0001 should have done it"


def test_the_hnsw_index_exists(db):
    found = db.execute(
        text(
            "select indexdef from pg_indexes "
            "where tablename='document_chunks' and indexname like '%hnsw%'"
        )
    ).scalar()
    assert found and "hnsw" in found.lower(), (
        "No HNSW index on document_chunks.embedding — every chat turn would "
        "sequentially scan the whole table."
    )


def test_retrieval_never_crosses_profiles(db, profiles, monkeypatch):
    """The security property. Filtering happens in SQL, not after top-k."""
    mine, theirs = profiles
    _stub_embeddings(monkeypatch, {"secret theirs": 1, "mine": 1, "query": 1})

    # Both sit at the same point in vector space, so only the profile filter
    # can separate them. A post-filter implementation would return nothing
    # or, worse, their row.
    rag_service.ingest(db, theirs.id, "cv", "secret theirs")
    rag_service.ingest(db, mine.id, "cv", "mine")

    hits = rag_service.retrieve(db, mine.id, "query")

    assert hits, "expected the caller's own chunk"
    assert all(c.profile_id == mine.id for c in hits)
    assert all("secret" not in c.content for c in hits)


def test_retrieval_orders_by_similarity(db, profiles, monkeypatch):
    mine, _ = profiles
    _stub_embeddings(
        monkeypatch, {"near text": 5, "far text": 300, "query": 5}
    )
    rag_service.ingest(db, mine.id, "cv", "far text", source_id=uuid.uuid4())
    rag_service.ingest(db, mine.id, "job_match", "near text", source_id=uuid.uuid4())

    hits = rag_service.retrieve(db, mine.id, "query", k=2)
    assert hits[0].content == "near text"


def test_retrieval_on_an_empty_corpus_returns_nothing(db, profiles, monkeypatch):
    mine, _ = profiles
    _stub_embeddings(monkeypatch, {"query": 1})
    assert rag_service.retrieve(db, mine.id, "query") == []


def test_embeddings_round_trip_at_the_declared_dimension(db, profiles, monkeypatch):
    mine, _ = profiles
    _stub_embeddings(monkeypatch, {"text": 2})
    rag_service.ingest(db, mine.id, "cv", "text")

    stored = db.query(DocumentChunk).filter_by(profile_id=mine.id).one()
    assert len(stored.embedding) == DIMS


# --- Curated corpus ---------------------------------------------------------
#
# The shared knowledge_base/ corpus. Same reason for living here: ordering by
# `<=>` needs the real operator. The property that matters is the mirror image
# of the one above — this corpus has no owner, so retrieval must reach every
# row regardless of who is asking.


def _stub_knowledge_embeddings(monkeypatch, mapping: dict[str, float]):
    monkeypatch.setattr(
        knowledge_service.embeddings,
        "embed_documents",
        lambda texts: [_vec(mapping.get(t, 0)) for t in texts],
    )
    monkeypatch.setattr(
        knowledge_service.embeddings, "embed_query", lambda t: _vec(mapping.get(t, 0))
    )


def _add_guide(db, title: str, seed: float, category: str = "ATS") -> None:
    db.add(
        KnowledgeChunk(
            category=category,
            source=f"{category}/{title}.json",
            chunk_index=0,
            title=title,
            content=f"Body of {title}.",
            content_hash=title,
            embedding=_vec(seed),
        )
    )
    db.flush()


def test_the_knowledge_hnsw_index_exists(db):
    found = db.execute(
        text(
            "select indexdef from pg_indexes "
            "where tablename='knowledge_chunks' and indexname like '%hnsw%'"
        )
    ).scalar()
    assert found and "hnsw" in found.lower(), (
        "No HNSW index on knowledge_chunks.embedding — every chat turn would "
        "sequentially scan the whole corpus."
    )


def test_knowledge_retrieval_orders_by_similarity(db, monkeypatch):
    _stub_knowledge_embeddings(monkeypatch, {"query": 5})
    _add_guide(db, "near", seed=5)
    _add_guide(db, "far", seed=300)

    hits = knowledge_service.retrieve(db, "query", k=2)

    assert hits[0].title == "near"


def test_knowledge_retrieval_is_shared_across_profiles(db, profiles, monkeypatch):
    """The inverse of the isolation guarantee above: this corpus belongs to
    nobody, so every caller must see the same rows. A stray profile filter
    here would silently return nothing for everyone."""
    _stub_knowledge_embeddings(monkeypatch, {"query": 7})
    _add_guide(db, "shared", seed=7)

    first = knowledge_service.retrieve(db, "query")
    second = knowledge_service.retrieve(db, "query")

    assert [c.title for c in first] == ["shared"]
    assert [c.title for c in second] == ["shared"]


def test_knowledge_retrieval_does_not_load_embeddings(db, monkeypatch):
    """Deferred on purpose: 768 floats per row that nothing downstream reads."""
    from sqlalchemy import inspect as sa_inspect

    _stub_knowledge_embeddings(monkeypatch, {"query": 9})
    _add_guide(db, "deferred", seed=9)
    db.expire_all()

    hit = knowledge_service.retrieve(db, "query")[0]

    assert "embedding" in sa_inspect(hit).unloaded
    assert hit.content  # the column that is actually used loaded fine

"""Embeddings for the RAG corpus.

Model choice, and why the dimensionality is what it is:

`text-embedding-004` is retired and 404s. `gemini-embedding-001` returns 3072
dimensions by default, which pgvector cannot index — both ivfflat and hnsw cap
at 2000 dimensions for the `vector` type. The model supports Matryoshka
truncation, so we ask for 768: indexable, cheaper to store, and the quality
loss at 768 is small by design.

Truncated Matryoshka vectors are NOT unit length (a 768-slice of a normalized
3072-vector measured ~0.58 here), so they are re-normalized below. Skipping
that silently degrades cosine similarity rather than failing, which is the
worst kind of bug to inherit.
"""

import math
from functools import lru_cache

from google import genai
from google.genai import errors, types

from app.config import get_settings

MODEL = "gemini-embedding-001"
DIMENSIONS = 768

# The free tier allows 100 *contents* per minute, not 100 requests — a batch
# of 50 texts spends 50 of them. Exported so a bulk caller can pace itself;
# nothing here enforces it, because blocking on a quota is right for an
# ingest and wrong for a user waiting on a reply.
FREE_TIER_CONTENTS_PER_MINUTE = 100

# Google's task types. Asymmetric retrieval works better when the corpus and
# the query are embedded with different intents.
_DOCUMENT = "RETRIEVAL_DOCUMENT"
_QUERY = "RETRIEVAL_QUERY"

# Used when the provider says it is rate limited but sends no RetryInfo.
_FALLBACK_RETRY_AFTER = 30.0


class RateLimited(RuntimeError):
    """The embedding quota is exhausted.

    Separated from every other provider failure because it is the one that is
    worth waiting out rather than reporting: the call is not wrong, just early.
    """

    def __init__(self, message: str, retry_after: float) -> None:
        super().__init__(message)
        # The provider's own hint, in seconds. Honoured rather than guessed —
        # backing off less than asked earns another 429.
        self.retry_after = retry_after


@lru_cache
def _client() -> genai.Client:
    settings = get_settings()
    if not settings.google_api_key:
        raise RuntimeError(
            "GOOGLE_API_KEY is not set. Copy .env.example to .env and fill it in."
        )
    return genai.Client(api_key=settings.google_api_key)


def _normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in vector))
    if norm == 0:
        return vector
    return [x / norm for x in vector]


def _retry_after(error: errors.ClientError) -> float:
    """Seconds the provider asked us to wait, from its RetryInfo detail.

    The value is buried in `details.error.details[]`, tagged by `@type`, and
    formatted as a Go duration string ("29.35s"). Absent or unparseable, the
    fallback applies — the point is to wait roughly the right amount, not to
    parse Google's error envelope perfectly.
    """
    try:
        details = error.details["error"]["details"]
    except (TypeError, KeyError, IndexError):
        return _FALLBACK_RETRY_AFTER

    for detail in details:
        if not str(detail.get("@type", "")).endswith("RetryInfo"):
            continue
        raw = str(detail.get("retryDelay", "")).removesuffix("s")
        try:
            return max(float(raw), 0.0)
        except ValueError:
            break
    return _FALLBACK_RETRY_AFTER


def _embed(texts: list[str], task_type: str) -> list[list[float]]:
    if not texts:
        return []
    try:
        response = _client().models.embed_content(
            model=MODEL,
            contents=texts,
            config=types.EmbedContentConfig(
                output_dimensionality=DIMENSIONS, task_type=task_type
            ),
        )
    except errors.ClientError as exc:
        if exc.code == 429:
            raise RateLimited(
                "The embedding quota is exhausted.", _retry_after(exc)
            ) from exc
        raise
    return [_normalize(list(e.values)) for e in response.embeddings]


def embed_documents(texts: list[str]) -> list[list[float]]:
    """Embed corpus chunks for storage."""
    return _embed(texts, _DOCUMENT)


def embed_query(text: str) -> list[float]:
    """Embed a single search query."""
    return _embed([text], _QUERY)[0]

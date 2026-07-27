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
from google.genai import types

from app.config import get_settings

MODEL = "gemini-embedding-001"
DIMENSIONS = 768

# Google's task types. Asymmetric retrieval works better when the corpus and
# the query are embedded with different intents.
_DOCUMENT = "RETRIEVAL_DOCUMENT"
_QUERY = "RETRIEVAL_QUERY"


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


def _embed(texts: list[str], task_type: str) -> list[list[float]]:
    if not texts:
        return []
    response = _client().models.embed_content(
        model=MODEL,
        contents=texts,
        config=types.EmbedContentConfig(
            output_dimensionality=DIMENSIONS, task_type=task_type
        ),
    )
    return [_normalize(list(e.values)) for e in response.embeddings]


def embed_documents(texts: list[str]) -> list[list[float]]:
    """Embed corpus chunks for storage."""
    return _embed(texts, _DOCUMENT)


def embed_query(text: str) -> list[float]:
    """Embed a single search query."""
    return _embed([text], _QUERY)[0]

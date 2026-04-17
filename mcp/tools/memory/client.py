"""
ChromaDB client and SentenceTransformer embedding management.

Provides singleton access to:
- ChromaDB HttpClient (connects to the chromadb container)
- SentenceTransformer model for generating embeddings locally

The embedding model is loaded once at module-level and reused across requests.
"""

import os
from functools import lru_cache

import chromadb
from sentence_transformers import SentenceTransformer

_EMBEDDING_MODEL_NAME = "intfloat/multilingual-e5-small"
_COLLECTION_NAME = "agent_memory"

CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))


@lru_cache(maxsize=1)
def _get_embedding_model() -> SentenceTransformer:
    """Load the SentenceTransformer model (cached singleton)."""
    return SentenceTransformer(_EMBEDDING_MODEL_NAME)


@lru_cache(maxsize=1)
def _get_chroma_client() -> chromadb.HttpClient:
    """Create a persistent HttpClient to the ChromaDB server (cached singleton)."""
    return chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)


# DBの初期化
def get_collection() -> chromadb.Collection:
    """Get or create the agent memory collection.

    Returns a ChromaDB collection configured for cosine similarity.
    We do NOT pass an embedding_function because we generate embeddings
    ourselves via SentenceTransformer and send raw vectors.
    """
    client = _get_chroma_client()
    return client.get_or_create_collection(
        name=_COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def embed_texts(texts: list[str], is_query: bool = False) -> list[list[float]]:
    """Generate embeddings for a list of texts using the local model.
    Applies the appropriate prefix (query: or passage:) for the E5 model.
    """
    prefix = "query: " if is_query else "passage: "
    prefixed_texts = [prefix + text for text in texts]

    model = _get_embedding_model()
    embeddings = model.encode(prefixed_texts, normalize_embeddings=True)
    return embeddings.tolist()

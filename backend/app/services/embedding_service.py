from functools import lru_cache
from typing import Any

from app.core.config import settings


@lru_cache
def get_embedding_model() -> Any:
    """Load the embedding model on first use."""
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(settings.embedding_model)


def generate_embeddings(text: str) -> list:
    """Generate embeddings for text."""
    model = get_embedding_model()
    embedding = model.encode(text)
    return embedding.tolist()


def generate_batch_embeddings(texts: list[str]) -> list[list]:
    """Generate embeddings for multiple texts."""
    model = get_embedding_model()
    embeddings = model.encode(texts)
    return [e.tolist() for e in embeddings]

import hashlib
from functools import lru_cache
from typing import Any

from app.core.config import settings


@lru_cache
def get_qdrant_client() -> Any:
    """Create the Qdrant client on first use."""
    from qdrant_client import QdrantClient

    return QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key,
    )


def ensure_collection_exists():
    """Ensure Qdrant collection exists."""
    from qdrant_client.models import Distance, VectorParams

    client = get_qdrant_client()
    try:
        client.get_collection(settings.qdrant_collection)
    except Exception:
        client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=VectorParams(
                size=settings.embedding_dimension, distance=Distance.COSINE
            ),
        )


def add_document_chunk(
    chunk_id: str, vector: list, metadata: dict, text: str
):
    """Add a document chunk to Qdrant."""
    from qdrant_client.models import PointStruct

    ensure_collection_exists()
    client = get_qdrant_client()
    point = PointStruct(
        id=int(hashlib.md5(chunk_id.encode()).hexdigest()[:16], 16),
        vector=vector,
        payload={"chunk_id": chunk_id, "text": text, **metadata},
    )
    client.upsert(
        collection_name=settings.qdrant_collection,
        points=[point],
    )


def search_similar(vector: list, limit: int = 5) -> list:
    """Search for similar vectors in Qdrant."""
    ensure_collection_exists()
    client = get_qdrant_client()
    response = client.query_points(
        collection_name=settings.qdrant_collection,
        query=vector,
        limit=limit,
    )
    return response.points


def delete_document_chunks(document_id: int):
    """Delete all chunks of a document."""
    ensure_collection_exists()
    client = get_qdrant_client()
    client.delete(
        collection_name=settings.qdrant_collection,
        points_selector=None,
    )

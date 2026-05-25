from app.core.config import settings


def chunk_text(text: str, chunk_size: int = None, overlap: int = None) -> list[str]:
    """Split text into chunks with optional overlap."""
    if chunk_size is None:
        chunk_size = settings.chunk_size
    if overlap is None:
        overlap = settings.chunk_overlap

    chunks = []
    start = 0
    
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
    
    return chunks


def chunk_document(text: str) -> list[dict]:
    """Chunk document and return with metadata."""
    chunks = chunk_text(text)
    result = []
    
    for i, chunk in enumerate(chunks):
        result.append({
            "index": i,
            "content": chunk,
            "word_count": len(chunk.split()),
        })
    
    return result

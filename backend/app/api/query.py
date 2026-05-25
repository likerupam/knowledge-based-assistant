from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_token
from app.models.models import User, Query, SearchLog, DocumentChunk
from app.schemas.schemas import QueryRequest, QueryResponse, SearchResultItem
from app.services.embedding_service import generate_embeddings
from app.services.llm_service import LLMConfigurationError, generate_rag_answer
from app.services.qdrant_service import search_similar
from app.services.cache_service import cache_get, cache_set
import json
import time

router = APIRouter(prefix="/api/query", tags=["query"])


@router.post("/search", response_model=QueryResponse)
def search_knowledge_base(
    request: QueryRequest,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db),
):
    """Search the knowledge base and get results."""
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    # Check cache
    cache_key = f"search:{user_id}:{request.query_text}"
    cached_result = cache_get(cache_key)
    if cached_result:
        return json.loads(cached_result)
    
    start_time = time.time()
    
    # Generate embedding for query
    query_embedding = generate_embeddings(request.query_text)
    
    # Search in Qdrant
    search_results = search_similar(query_embedding, limit=request.top_k)
    
    # Extract and format results
    sources = []
    for citation_id, result in enumerate(search_results, start=1):
        payload = result.payload
        chunk = db.query(DocumentChunk).filter(
            DocumentChunk.qdrant_point_id == payload.get("chunk_id")
        ).first()
        
        if chunk:
            sources.append({
                "citation_id": citation_id,
                "document_id": chunk.document_id,
                "filename": payload.get("filename", "Unknown"),
                "chunk_index": chunk.chunk_index,
                "content": payload.get("text", ""),
                "similarity_score": result.score,
            })
    
    # Generate a grounded answer from retrieved chunks
    try:
        response_text, tokens_used = generate_rag_answer(request.query_text, sources)
    except LLMConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        if type(exc).__module__.startswith("openai"):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"OpenAI API error: {exc}",
            ) from exc
        raise
    
    db_query = Query(
        user_id=user.id,
        query_text=request.query_text,
        response_text=response_text,
        tokens_used=tokens_used,
    )
    db.add(db_query)
    
    # Log search
    response_time_ms = int((time.time() - start_time) * 1000)
    search_log = SearchLog(
        user_id=user.id,
        query=request.query_text,
        results_count=len(sources),
        response_time_ms=response_time_ms,
    )
    db.add(search_log)
    db.commit()
    
    result = QueryResponse(
        query_text=request.query_text,
        response_text=response_text,
        sources=sources,
        created_at=db_query.created_at,
    )
    
    # Cache result
    cache_set(cache_key, result.model_dump_json(), ttl=3600)
    
    return result


@router.get("/history")
def get_query_history(
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db),
):
    """Get query history for the current user."""
    queries = db.query(Query).filter(Query.user_id == int(user_id)).order_by(Query.created_at.desc()).all()
    return queries

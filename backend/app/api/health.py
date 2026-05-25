from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@router.get("/")
def root():
    """Root endpoint."""
    return {
        "name": "Knowledge Base Assistant",
        "version": "1.0.0",
        "description": "API for knowledge base semantic search",
    }

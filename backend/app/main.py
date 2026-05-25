from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health, auth, documents, query
from app.core.config import settings
from app.core.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize application resources."""
    if settings.create_tables_on_startup:
        Base.metadata.create_all(bind=engine)
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    fastapi_app = FastAPI(
        title="Knowledge Base Assistant",
        description="Semantic search and retrieval system with vector database",
        version="1.0.0",
        lifespan=lifespan,
    )
    @fastapi_app.get("/health")
    async def health_check():
        return {"status": "healthy"}


    fastapi_app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    fastapi_app.include_router(health.router)
    fastapi_app.include_router(auth.router)
    fastapi_app.include_router(documents.router)
    fastapi_app.include_router(query.router)

    return fastapi_app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

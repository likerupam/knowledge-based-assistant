from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_token
from app.models.models import Document, DocumentChunk, User
from app.schemas.schemas import DocumentResponse, DocumentChunkResponse
from app.services.document_service import extract_text
from app.services.chunking_service import chunk_document
from app.services.embedding_service import generate_batch_embeddings
from app.services.qdrant_service import add_document_chunk
import hashlib
import os

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db),
):
    """Upload and process a document."""
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    file_path = f"./uploads/{file.filename}"
    os.makedirs("./uploads", exist_ok=True)
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Extract text
    document_type = file.filename.split(".")[-1].lower()
    text = extract_text(file_path, document_type)
    
    # Calculate content hash
    content_hash = hashlib.md5(text.encode()).hexdigest()
    
    # Check if document already exists
    existing_doc = db.query(Document).filter(
        Document.content_hash == content_hash
    ).first()
    if existing_doc:
        if existing_doc.chunk_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document already exists",
            )
        # Previous upload did not finish indexing; allow retry
        db.delete(existing_doc)
        db.commit()
    
    # Create document record
    db_document = Document(
        user_id=user.id,
        filename=file.filename,
        document_type=document_type,
        file_path=file_path,
        content_hash=content_hash,
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    
    # Chunk and embed
    chunks = chunk_document(text)
    embeddings = generate_batch_embeddings([chunk["content"] for chunk in chunks])
    
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        chunk_id = f"{db_document.id}_chunk_{i}"
        
        db_chunk = DocumentChunk(
            document_id=db_document.id,
            chunk_index=i,
            content=chunk["content"],
            qdrant_point_id=chunk_id,
        )
        db.add(db_chunk)
        
        # Add to Qdrant
        add_document_chunk(
            chunk_id=chunk_id,
            vector=embedding,
            metadata={"document_id": db_document.id, "filename": file.filename},
            text=chunk["content"],
        )
    
    db_document.chunk_count = len(chunks)
    db.commit()
    
    return {
        "message": "Document uploaded and processed successfully",
        "document_id": db_document.id,
        "chunks_created": len(chunks),
    }


@router.get("/", response_model=list[DocumentResponse])
def list_documents(
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db),
):
    """List all documents for the current user."""
    documents = db.query(Document).filter(Document.user_id == int(user_id)).all()
    return documents


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: int,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db),
):
    """Get a specific document."""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == int(user_id),
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    
    return document


@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db),
):
    """Delete a document."""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == int(user_id),
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    
    db.delete(document)
    db.commit()
    
    return {"message": "Document deleted successfully"}

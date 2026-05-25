from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    documents = relationship("Document", back_populates="owner")
    queries = relationship("Query", back_populates="user")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    filename = Column(String, index=True)
    document_type = Column(String)  # pdf, txt, sql, log
    file_path = Column(String)
    content_hash = Column(String, unique=True, index=True)
    chunk_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    owner = relationship("User", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    chunk_index = Column(Integer)
    content = Column(Text)
    qdrant_point_id = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    document = relationship("Document", back_populates="chunks")


class Query(Base):
    __tablename__ = "queries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    query_text = Column(Text)
    response_text = Column(Text)
    tokens_used = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="queries")


class SearchLog(Base):
    __tablename__ = "search_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    query = Column(Text)
    results_count = Column(Integer)
    response_time_ms = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

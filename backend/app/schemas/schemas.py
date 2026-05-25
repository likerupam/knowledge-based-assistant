from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    full_name: str


class UserCreate(UserBase):
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentCreate(BaseModel):
    filename: str
    document_type: str  # pdf, txt, sql, log


class DocumentResponse(BaseModel):
    id: int
    filename: str
    document_type: str
    chunk_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentChunkResponse(BaseModel):
    id: int
    chunk_index: int
    content: str

    class Config:
        from_attributes = True


class QueryRequest(BaseModel):
    query_text: str
    top_k: int = 5


class QueryResponse(BaseModel):
    query_text: str
    response_text: str
    sources: list[dict]
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class SearchResultItem(BaseModel):
    document_id: int
    filename: str
    chunk_index: int
    content: str
    similarity_score: float

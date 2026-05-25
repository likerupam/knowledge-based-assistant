# Knowledge Base Assistant - Architecture & Flow Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [High-Level Architecture](#high-level-architecture)
3. [Component Architecture](#component-architecture)
4. [Data Flow](#data-flow)
5. [API Endpoints](#api-endpoints)
6. [Database Schema](#database-schema)
7. [Authentication & Security](#authentication--security)
8. [Service Layer Details](#service-layer-details)
9. [Deployment Architecture](#deployment-architecture)
10. [Configuration](#configuration)

---

## System Overview

**Knowledge Base Assistant** is a semantic search and retrieval system built with FastAPI that enables intelligent document ingestion, chunking, embedding generation, and similarity-based retrieval using vector databases. It uses Retrieval-Augmented Generation (RAG) to provide context-aware answers from uploaded documents.

### Key Capabilities
- **Document Upload & Processing**: Support for PDF, TXT, SQL, DOCX, and LOG files
- **Semantic Search**: Vector-based similarity search using Qdrant
- **Intelligent Chunking**: Configurable text chunking with overlap
- **RAG-Based Answers**: Context-aware responses using OpenAI API
- **Caching**: Redis-backed result caching for performance
- **Multi-tenant**: User-isolated documents and queries
- **JWT Authentication**: Secure token-based authentication
- **Search History**: Track and retrieve user queries

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                            │
│                     (Frontend Applications)                     │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP/REST
┌────────────────────────▼────────────────────────────────────────┐
│                    API LAYER (FastAPI)                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Routes: /api/auth, /api/documents, /api/query, /health  │   │
│  │  Middleware: CORS, JWT Authentication                    │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
┌────────▼──────┐ ┌──────▼──────┐ ┌─────▼────────┐
│ SERVICE LAYER │ │SERVICE LAYER│ │SERVICE LAYER │
│               │ │             │ │              │
│ Auth Service  │ │Document &   │ │Query & LLM   │
│ - JWT Token   │ │Embedding    │ │Services      │
│ - Password    │ │- Extract    │ │- Embedding   │
│   Hash        │ │- Chunk      │ │- Search      │
│               │ │- Embed      │ │- RAG Answer  │
└───────────────┘ └─────────────┘ └──────────────┘
         │               │               │
         └───────────────┼───────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
┌────────▼──────┐ ┌──────▼──────┐ ┌─────▼────────┐
│  DATA LAYER   │ │  VECTOR DB  │ │  CACHE LAYER │
│               │ │             │ │              │
│ PostgreSQL    │ │  Qdrant     │ │  Redis       │
│  - Users      │ │  - Vectors  │ │  - Results   │
│  - Documents  │ │  - Metadata │ │  - Sessions  │
│  - Chunks     │ │  - Scoring  │ │              │
│  - Queries    │ │             │ │              │
└───────────────┘ └─────────────┘ └──────────────┘
```

---

## Component Architecture

### Core Components

#### 1. **API Router Layer** (`/app/api/`)
- **health.py**: Health check endpoints
- **auth.py**: User registration, login, and token management
- **documents.py**: Document upload, listing, and deletion
- **query.py**: Semantic search and query processing

#### 2. **Service Layer** (`/app/services/`)
- **embedding_service.py**: Generates vector embeddings using Sentence Transformers
- **qdrant_service.py**: Vector database operations and similarity search
- **document_service.py**: File text extraction (PDF, TXT, SQL, LOG, DOCX)
- **chunking_service.py**: Text splitting with configurable chunk size and overlap
- **llm_service.py**: OpenAI integration for RAG-based answer generation
- **cache_service.py**: Redis caching operations

#### 3. **Core Layer** (`/app/core/`)
- **config.py**: Centralized configuration from environment variables
- **database.py**: SQLAlchemy database setup and session management
- **security.py**: JWT token creation/verification, password hashing

#### 4. **Data Layer** (`/app/models/`)
- **models.py**: SQLAlchemy ORM models for database schema

#### 5. **Schema Layer** (`/app/schemas/`)
- **schemas.py**: Pydantic models for request/response validation

---

## Data Flow

### 1. Document Upload & Processing Flow

```
User Upload File
      │
      ▼
POST /api/documents/upload
      │
      ├─ Verify JWT Token
      ├─ Get User from Database
      │
      ▼
Save File to Disk (/uploads/)
      │
      ▼
Extract Text Based on File Type
  (PDF → text, TXT → text, SQL → text, LOG → text, DOCX → text)
      │
      ▼
Calculate Content Hash (MD5)
      │
      ├─ Check for Duplicates in DB
      └─ If exists → Return Error
      │
      ▼
Create Document Record in PostgreSQL
      │
      ├─ document_id
      ├─ user_id
      ├─ filename
      ├─ document_type
      ├─ file_path
      ├─ content_hash
      └─ created_at
      │
      ▼
Chunk Text Using Chunking Service
      │
      ├─ Split by chunk_size (default: 1024)
      ├─ Overlap by chunk_overlap (default: 128)
      └─ Generate list of chunks
      │
      ▼
Generate Batch Embeddings
      │
      ├─ Load Sentence Transformer Model (all-MiniLM-L6-v2)
      ├─ Encode each chunk → 384-dimensional vector
      └─ Return list of embeddings
      │
      ▼
Store in Qdrant Vector DB (for each chunk)
      │
      ├─ Create PointStruct:
      │  ├─ id: hash(chunk_id)
      │  ├─ vector: 384-dim embedding
      │  ├─ payload:
      │  │  ├─ chunk_id: "doc_id_chunk_index"
      │  │  ├─ text: chunk content
      │  │  ├─ document_id
      │  │  └─ filename
      │  └─ Upsert into collection
      │
      ▼
Store Chunk Records in PostgreSQL
      │
      ├─ chunk_id (primary key)
      ├─ document_id (foreign key)
      ├─ chunk_index
      ├─ content
      ├─ qdrant_point_id
      └─ created_at
      │
      ▼
Update Document with chunk_count
      │
      ▼
Return Success Response
  {
    "message": "Document uploaded and processed successfully",
    "document_id": 123,
    "chunks_created": 45
  }
```

### 2. Query & Search Flow

```
User Query
      │
      ▼
POST /api/query/search
      │
      ├─ Verify JWT Token
      ├─ Get User from Database
      │
      ▼
Check Redis Cache
      │
      ├─ cache_key = "search:{user_id}:{query_text}"
      ├─ If cached → Return cached result
      └─ If not cached → Continue
      │
      ▼
Generate Query Embedding
      │
      ├─ Load Sentence Transformer Model
      ├─ Encode query text → 384-dimensional vector
      └─ Store embedding
      │
      ▼
Search Similar Vectors in Qdrant
      │
      ├─ Query with embedding vector
      ├─ Limit: top_k results (default: 5)
      ├─ Use COSINE similarity distance
      └─ Return: [PointStruct with scores]
      │
      ▼
Extract and Enrich Results
      │
      ├─ For each result:
      │  ├─ Get payload (chunk_id, text, filename, document_id)
      │  ├─ Query PostgreSQL for DocumentChunk
      │  ├─ Get chunk_index and full metadata
      │  └─ Create source object with citation_id and similarity_score
      │
      ▼
Format Context from Retrieved Chunks
      │
      ├─ Build context string from all sources
      ├─ Respect max context size (default: 12,000 chars)
      ├─ Add source citations: [1] Source: filename, chunk N
      └─ Truncate if exceeds limit
      │
      ▼
Generate RAG Answer Using OpenAI
      │
      ├─ Call OpenAI Chat Completion API
      ├─ Model: gpt-4o-mini (configurable)
      ├─ Temperature: 0.2 (low randomness)
      ├─ Max tokens: 700
      ├─ System prompt: "Answer only from provided sources"
      ├─ User prompt: Question + Context + Sources
      └─ Get response + token usage
      │
      ▼
Store Query Record in PostgreSQL
      │
      ├─ query_id
      ├─ user_id
      ├─ query_text
      ├─ response_text
      ├─ tokens_used
      └─ created_at
      │
      ▼
Store Search Log in PostgreSQL
      │
      ├─ search_log_id
      ├─ user_id
      ├─ query
      ├─ results_count
      ├─ response_time_ms
      └─ created_at
      │
      ▼
Cache Result in Redis
      │
      ├─ cache_key = "search:{user_id}:{query_text}"
      ├─ cache_value = QueryResponse JSON
      ├─ TTL: 3600 seconds (1 hour)
      └─ Stored
      │
      ▼
Return Response
  {
    "query_text": "What is...",
    "response_text": "Based on the sources...",
    "sources": [
      {
        "citation_id": 1,
        "document_id": 123,
        "filename": "doc.pdf",
        "chunk_index": 5,
        "content": "chunk text...",
        "similarity_score": 0.92
      }
    ],
    "created_at": "2024-01-01T12:00:00"
  }
```

### 3. Authentication Flow

```
User Registration
      │
      ▼
POST /api/auth/register
  {
    "email": "user@example.com",
    "password": "password123",
    "full_name": "John Doe"
  }
      │
      ├─ Validate email format
      ├─ Check if user already exists
      │
      ▼
Hash Password with Bcrypt
      │
      ├─ Run through pwd_context.hash()
      └─ Store hashed_password
      │
      ▼
Create User Record in PostgreSQL
      │
      ├─ user_id (auto-increment)
      ├─ email (unique)
      ├─ hashed_password
      ├─ full_name
      ├─ is_active (default: True)
      └─ created_at
      │
      ▼
Return User Info (without password)

─────────────────────────────────────────

User Login
      │
      ▼
POST /api/auth/login
  {
    "email": "user@example.com",
    "password": "password123"
  }
      │
      ├─ Query User by email
      ├─ If not found → 401 Unauthorized
      │
      ▼
Verify Password
      │
      ├─ Use pwd_context.verify()
      ├─ If mismatch → 401 Unauthorized
      └─ If match → Continue
      │
      ▼
Generate JWT Access Token
      │
      ├─ Payload: { "sub": user_id }
      ├─ Expiration: access_token_expire_minutes (default: 30 min)
      ├─ Algorithm: HS256
      ├─ Secret: settings.secret_key
      └─ Encoded with JWT
      │
      ▼
Return Token
  {
    "access_token": "eyJhbGc...",
    "token_type": "bearer"
  }

─────────────────────────────────────────

Verify Token (on each request)
      │
      ▼
Dependency: verify_token()
      │
      ├─ Extract "Authorization: Bearer <token>" header
      ├─ Decode JWT using secret_key and HS256
      ├─ Check if expired (compare with exp claim)
      ├─ Extract user_id from "sub" claim
      │
      ├─ If invalid/expired → 401 Unauthorized
      └─ If valid → Return user_id
      │
      ▼
Add user_id to request context for route handler
```

---

## API Endpoints

### Authentication Endpoints

#### `POST /api/auth/register`
Register a new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "full_name": "John Doe"
}
```

**Response (201):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "created_at": "2024-01-01T12:00:00"
}
```

#### `POST /api/auth/login`
Login and receive JWT access token.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### `GET /api/auth/me`
Get current authenticated user information.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "created_at": "2024-01-01T12:00:00"
}
```

### Document Endpoints

#### `POST /api/documents/upload`
Upload and process a document (PDF, TXT, SQL, DOCX, LOG).

**Request:**
- Multipart form-data with file
- Headers: `Authorization: Bearer <access_token>`

**Response (200):**
```json
{
  "message": "Document uploaded and processed successfully",
  "document_id": 123,
  "chunks_created": 45
}
```

#### `GET /api/documents/`
List all documents for the authenticated user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
[
  {
    "id": 123,
    "filename": "employee_handbook.pdf",
    "document_type": "pdf",
    "chunk_count": 45,
    "created_at": "2024-01-01T12:00:00",
    "updated_at": "2024-01-01T12:00:00"
  }
]
```

#### `GET /api/documents/{document_id}`
Get a specific document by ID.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "id": 123,
  "filename": "employee_handbook.pdf",
  "document_type": "pdf",
  "chunk_count": 45,
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-01T12:00:00"
}
```

#### `DELETE /api/documents/{document_id}`
Delete a document and its associated chunks.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "message": "Document deleted successfully"
}
```

### Query Endpoints

#### `POST /api/query/search`
Perform semantic search on uploaded documents and get RAG-based answer.

**Request:**
```json
{
  "query_text": "What is the company's remote work policy?",
  "top_k": 5
}
```

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "query_text": "What is the company's remote work policy?",
  "response_text": "Based on the employee handbook, the company offers... [1] [2]",
  "sources": [
    {
      "citation_id": 1,
      "document_id": 123,
      "filename": "employee_handbook.pdf",
      "chunk_index": 12,
      "content": "Remote work policy section...",
      "similarity_score": 0.95
    },
    {
      "citation_id": 2,
      "document_id": 124,
      "filename": "hr_policies.pdf",
      "chunk_index": 8,
      "content": "Work from home guidelines...",
      "similarity_score": 0.87
    }
  ],
  "created_at": "2024-01-01T12:00:00"
}
```

#### `GET /api/query/history`
Get query history for the authenticated user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
[
  {
    "id": 456,
    "user_id": 1,
    "query_text": "What is the company's remote work policy?",
    "response_text": "Based on the employee handbook...",
    "tokens_used": 287,
    "created_at": "2024-01-01T12:00:00"
  }
]
```

### Health Endpoints

#### `GET /health`
Health check endpoint for service monitoring.

**Response (200):**
```json
{
  "status": "healthy"
}
```

---

## Database Schema

### Users Table
```sql
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  email VARCHAR UNIQUE NOT NULL,
  hashed_password VARCHAR NOT NULL,
  full_name VARCHAR NOT NULL,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Purpose:** Store user accounts, credentials, and metadata.

### Documents Table
```sql
CREATE TABLE documents (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id),
  filename VARCHAR NOT NULL,
  document_type VARCHAR NOT NULL,
  file_path VARCHAR NOT NULL,
  content_hash VARCHAR UNIQUE NOT NULL,
  chunk_count INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Purpose:** Track uploaded documents with metadata and deduplication via content_hash.

### DocumentChunk Table
```sql
CREATE TABLE document_chunks (
  id SERIAL PRIMARY KEY,
  document_id INTEGER NOT NULL REFERENCES documents(id),
  chunk_index INTEGER NOT NULL,
  content TEXT NOT NULL,
  qdrant_point_id VARCHAR UNIQUE NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Purpose:** Store individual text chunks from documents with references to their Qdrant vector representations.

### Queries Table
```sql
CREATE TABLE queries (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id),
  query_text TEXT NOT NULL,
  response_text TEXT NOT NULL,
  tokens_used INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Purpose:** Log user queries and AI-generated responses for audit and analytics.

### SearchLogs Table
```sql
CREATE TABLE search_logs (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id),
  query TEXT NOT NULL,
  results_count INTEGER NOT NULL,
  response_time_ms INTEGER NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Purpose:** Track search performance metrics and usage patterns.

### Entity Relationships
```
Users (1) ──── (Many) Documents
         └──── (Many) Queries
         └──── (Many) SearchLogs

Documents (1) ──── (Many) DocumentChunk
```

---

## Authentication & Security

### JWT Token-Based Authentication

**Token Structure:**
- **Header:** `{"alg": "HS256", "typ": "JWT"}`
- **Payload:** `{"sub": "user_id", "exp": timestamp}`
- **Signature:** HMAC-SHA256 signed with `secret_key`

**Flow:**
1. User logs in with credentials
2. Password verified against bcrypt hash
3. JWT token generated with user_id and expiration
4. Token sent to client in response
5. Client includes token in `Authorization: Bearer <token>` header
6. On each request, server verifies token validity and extracts user_id

### Password Security
- **Algorithm:** Bcrypt with configurable rounds
- **Storage:** Only hashed passwords stored in database
- **Verification:** Plain text compared with hash during login

### Configuration (Security Parameters)
- **Secret Key:** `SECRET_KEY` environment variable (change in production)
- **Algorithm:** HS256 (HMAC with SHA-256)
- **Expiration:** `ACCESS_TOKEN_EXPIRE_MINUTES` (default: 30 minutes)
- **CORS:** Configurable origins via `CORS_ORIGINS` setting

---

## Service Layer Details

### 1. Embedding Service (`embedding_service.py`)

**Model:** Sentence Transformers (all-MiniLM-L6-v2)
- **Dimensions:** 384
- **Purpose:** Convert text to dense vectors for semantic search

**Key Functions:**
```python
generate_embeddings(text: str) -> list
  # Single text → 384-dim vector

generate_batch_embeddings(texts: list[str]) -> list[list]
  # Multiple texts → Multiple vectors (optimized for batching)
```

**Lazy Loading:** Model loaded on first use and cached with `@lru_cache`

### 2. Qdrant Service (`qdrant_service.py`)

**Vector Database:** Qdrant (semantic vector search)
- **Collection:** "documents" (configurable)
- **Distance Metric:** COSINE similarity
- **Vector Dimension:** 384 (matches embedding model)

**Key Functions:**
```python
ensure_collection_exists()
  # Create Qdrant collection if not exists

add_document_chunk(chunk_id, vector, metadata, text)
  # Upsert point into Qdrant with vector and payload

search_similar(vector, limit=5) -> list
  # Search for similar vectors, return top-k results

delete_document_chunks(document_id)
  # Delete all chunks of a document
```

**Point Structure:**
```json
{
  "id": "hash(chunk_id) as int64",
  "vector": [0.123, 0.456, ...],  // 384 dimensions
  "payload": {
    "chunk_id": "doc_id_chunk_index",
    "text": "chunk content",
    "document_id": 123,
    "filename": "doc.pdf"
  }
}
```

### 3. Document Service (`document_service.py`)

**File Type Support:**
- PDF → PyPDF2
- TXT, SQL, LOG → Plain text file reading
- DOCX → python-docx

**Key Functions:**
```python
extract_text(file_path, document_type) -> str
  # Dispatcher function selecting appropriate extractor

extract_text_from_pdf(file_path) -> str
  # Iterate through pages, extract text

extract_text_from_txt/sql/log(file_path) -> str
  # Read UTF-8 encoded files
```

### 4. Chunking Service (`chunking_service.py`)

**Chunking Strategy:** Sliding window with overlap

**Parameters:**
- `chunk_size`: Default 1024 characters
- `chunk_overlap`: Default 128 characters

**Algorithm:**
```
for start in range(0, len(text), chunk_size - overlap):
  end = min(start + chunk_size, len(text))
  chunk = text[start:end]
  chunks.append(chunk)
```

**Key Functions:**
```python
chunk_text(text, chunk_size, overlap) -> list[str]
  # Return list of overlapping text chunks

chunk_document(text) -> list[dict]
  # Return chunks with metadata (index, word_count)
```

### 5. LLM Service (`llm_service.py`)

**LLM Provider:** OpenAI (gpt-4o-mini by default)

**RAG (Retrieval-Augmented Generation) Process:**
1. Retrieve relevant chunks from vector DB
2. Format them with citations
3. Send to LLM with question and context
4. Generate grounded answer based on sources only

**Key Functions:**
```python
_format_context(sources: list[dict]) -> str
  # Build context string with source citations
  # Respect max context size (12,000 chars default)

generate_rag_answer(question, sources) -> tuple[str, int]
  # Return (answer_text, tokens_used)
  # System prompt ensures answer is grounded in sources
```

**System Prompt:**
> "You are a knowledge base assistant. Answer only from the provided sources. If the sources do not contain enough information, say so clearly. Cite supporting facts with source markers like [1] or [2]. Keep the answer clear and direct."

**Configuration:**
- **Model:** `gpt-4o-mini` (configurable via `OPENAI_MODEL`)
- **Temperature:** 0.2 (low randomness, factual)
- **Max Tokens:** 700 (configurable via `LLM_MAX_TOKENS`)
- **Max Context:** 12,000 characters (configurable via `RAG_MAX_CONTEXT_CHARS`)

### 6. Cache Service (`cache_service.py`)

**Cache Backend:** Redis

**Key Functions:**
```python
cache_get(key: str) -> str
  # Retrieve value from cache, return None if not found

cache_set(key: str, value: str, ttl: int = 3600)
  # Store value with TTL (time-to-live)

cache_delete(key: str)
  # Delete specific cache key

cache_clear_pattern(pattern: str)
  # Delete all keys matching pattern (e.g., "search:user_1:*")
```

**Cache Keys:**
- Search results: `search:{user_id}:{query_text}`
- Session data: `session:{user_id}:*`
- Default TTL: 3600 seconds (1 hour)

---

## Deployment Architecture

### Docker Compose Setup

**Services:**

1. **PostgreSQL** (postgres:15-alpine)
   - Port: 5432
   - Volume: postgres_data (persistent)
   - Health check: pg_isready

2. **Redis** (redis:7-alpine)
   - Port: 6379
   - Volume: redis_data (persistent)
   - Health check: redis-cli ping

3. **Qdrant** (qdrant/qdrant:latest)
   - Port: 6333
   - Volume: qdrant_data (persistent)
   - Health check: HTTP /health

4. **Backend** (FastAPI application)
   - Port: 8000
   - Depends on: postgres, redis, qdrant (conditional startup)
   - Environment: All service URLs and API keys
   - Volume: ./uploads/ (uploaded documents)
   - Health check: HTTP /health

**Networking:**
- All services connected via Docker internal network
- Backend communicates with services using container names (postgres, redis, qdrant)
- Only backend (8000) and direct service ports exposed to host

### Kubernetes Deployment

**Namespace:** knowledge-base

**Kubernetes Resources:**

1. **ConfigMap** (kb-config)
   - DATABASE_URL
   - REDIS_URL
   - QDRANT_URL
   - ENVIRONMENT

2. **Secret** (kb-secrets)
   - SECRET_KEY (JWT secret)
   - POSTGRES credentials

3. **PersistentVolumeClaims:**
   - postgres-pvc: 10Gi
   - redis-pvc: 2Gi
   - qdrant-pvc: 10Gi

4. **Deployments:**
   - PostgreSQL (1 replica)
   - Redis (1 replica)
   - Qdrant (1 replica)
   - Backend (configurable replicas)

5. **Services:**
   - ClusterIP services for internal communication
   - Backend service exposed (NodePort or LoadBalancer)

### Infrastructure Stack

```
┌─────────────────────────────────────────┐
│        Load Balancer (Optional)         │
└────────────────────┬────────────────────┘
                     │
┌────────────────────▼────────────────────┐
│     Kubernetes Cluster / Docker Host    │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │  Backend Service (FastAPI)        │  │
│  │  Port: 8000 / 30000 (K8s)         │  │
│  └─────────────┬─────────────────────┘  │
│                │                        │
│  ┌─────────────┼─────────────────────┐  │
│  │             │                     │  │
│  ▼             ▼                     ▼  │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│ │PostgreSQL│ │  Redis   │ │ Qdrant   │ │
│ │  :5432   │ │  :6379   │ │  :6333   │ │
│ │  10Gi    │ │  2Gi     │ │  10Gi    │ │
│ └──────────┘ └──────────┘ └──────────┘ │
│                                         │
│  └─────────────────────────────────────┘
│
└─────────────────────────────────────────┘
```

---

## Configuration

All configuration is managed through environment variables loaded via Pydantic `BaseSettings`.

### Configuration File
- **Location:** `backend/.env` (referenced from config.py)
- **Template:** `backend/.env.example`

### Environment Variables

#### Database
- `DATABASE_URL`: PostgreSQL connection string
  - Default: `postgresql://user:password@localhost:5432/knowledge_base`

#### Redis
- `REDIS_URL`: Redis connection string
  - Default: `redis://localhost:6379/0`

#### Qdrant
- `QDRANT_URL`: Qdrant API URL
  - Default: `http://localhost:6333`
- `QDRANT_API_KEY`: Optional API key for Qdrant (if secured)
- `QDRANT_COLLECTION`: Collection name for vectors
  - Default: `documents`

#### JWT & Security
- `SECRET_KEY`: JWT signing secret (CHANGE IN PRODUCTION)
  - Default: `your-secret-key-change-in-production`
- `ALGORITHM`: JWT algorithm
  - Default: `HS256`
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time
  - Default: `30`

#### API
- `CORS_ORIGINS`: Allowed CORS origins (JSON list)
  - Default: `["*"]` (allow all)
- `CREATE_TABLES_ON_STARTUP`: Auto-create tables on app start
  - Default: `true`

#### OpenAI & LLM
- `OPENAI_API_KEY`: OpenAI API key (required for RAG)
- `OPENAI_MODEL`: Model to use
  - Default: `gpt-4o-mini`
- `LLM_TEMPERATURE`: Temperature for response randomness (0-2)
  - Default: `0.2` (low randomness, factual)
- `LLM_MAX_TOKENS`: Maximum tokens in LLM response
  - Default: `700`
- `RAG_MAX_CONTEXT_CHARS`: Maximum characters of context to send to LLM
  - Default: `12000`

#### Embeddings
- `EMBEDDING_MODEL`: Sentence Transformer model name
  - Default: `sentence-transformers/all-MiniLM-L6-v2`
- `EMBEDDING_DIMENSION`: Vector dimensions
  - Default: `384`

#### Chunking
- `CHUNK_SIZE`: Text chunk size in characters
  - Default: `1024`
- `CHUNK_OVERLAP`: Overlap between consecutive chunks
  - Default: `128`

#### Environment
- `ENVIRONMENT`: Environment name (development/production)
  - Default: `development`
- `DEBUG`: Debug mode flag
  - Default: `true`
  - Set to `false`, `release`, `prod`, or `production` to disable

### Example .env File

```env
# Database
DATABASE_URL=postgresql://user:password@postgres:5432/knowledge_base

# Redis
REDIS_URL=redis://redis:6379/0

# Qdrant
QDRANT_URL=http://qdrant:6333
QDRANT_COLLECTION=documents

# JWT & Security
SECRET_KEY=your-production-secret-key-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API
CORS_ORIGINS=["http://localhost:3000", "https://yourdomain.com"]
CREATE_TABLES_ON_STARTUP=true

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.2
LLM_MAX_TOKENS=700
RAG_MAX_CONTEXT_CHARS=12000

# Embeddings
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384

# Chunking
CHUNK_SIZE=1024
CHUNK_OVERLAP=128

# Environment
ENVIRONMENT=production
DEBUG=false
```

---

## Sequence Diagrams

### Document Upload Sequence

```
User          Browser        FastAPI Backend    PostgreSQL    Qdrant
 │                │                  │               │          │
 ├─ Select File──>│                  │               │          │
 │                │                  │               │          │
 ├─ Click Upload─>│──POST /upload───>│               │          │
 │                │                  │               │          │
 │                │                  ├─ Extract Text │          │
 │                │                  │               │          │
 │                │                  ├─ Create Doc──>│          │
 │                │                  │               │          │
 │                │                  ├─ Chunk Text   │          │
 │                │                  │               │          │
 │                │                  ├─ Generate Embeddings     │
 │                │                  │               │          │
 │                │                  ├──────── Store Chunks ───>│
 │                │                  │               │          │
 │                │                  ├─ Save Chunks─>│          │
 │                │                  │               │          │
 │                │<──200 Response───│               │          │
 │<─ Show Success─│                  │               │          │
```

### Query & Search Sequence

```
User          Browser        FastAPI Backend    PostgreSQL    Qdrant    OpenAI
 │                │                  │               │          │         │
 ├─ Type Query──>│                  │               │          │         │
 │                │                  │               │          │         │
 ├─ Submit────────>POST /search─────>│               │          │         │
 │                │                  │               │          │         │
 │                │                  ├─ Check Cache   │          │         │
 │                │                  │               │          │         │
 │                │                  ├─ Generate Embedding      │         │
 │                │                  │               │          │         │
 │                │                  ├─ Search Similar────────>│         │
 │                │                  │<─── Results ──────────│         │
 │                │                  │               │          │         │
 │                │                  ├─ Query Chunks│          │         │
 │                │                  │<─ Chunk Data─│          │         │
 │                │                  │               │          │         │
 │                │                  ├─ Format Context        │         │
 │                │                  │               │          │         │
 │                │                  ├─ Generate Answer────────────────>│
 │                │                  │<─ AI Response─────────────────│
 │                │                  │               │          │         │
 │                │                  ├─ Store Query─>│          │         │
 │                │                  ├─ Store Log───>│          │         │
 │                │                  ├─ Cache Result │          │         │
 │                │                  │               │          │         │
 │                │<──200 Response───│               │          │         │
 │<─ Show Answer ─│                  │               │          │         │
 │ with Sources   │                  │               │          │         │
```

### Authentication Sequence

```
User          Browser        FastAPI Backend    PostgreSQL
 │                │                  │               │
 ├─ Enter Email──>│                  │               │
 ├─ Enter Pass───>│                  │               │
 │                │                  │               │
 ├─ Click Login──>│──POST /login────>│               │
 │                │                  │               │
 │                │                  ├─ Query User──>│
 │                │                  │<─ User Data ─│
 │                │                  │               │
 │                │                  ├─ Verify Password
 │                │                  │               │
 │                │                  ├─ Generate JWT Token
 │                │                  │               │
 │                │<──200 + Token────│               │
 │<─ Store Token ─│                  │               │
 │                │                  │               │
 ├─ Make Request─>│ (include token)  │               │
 │                │──GET /documents─>│               │
 │                │ + Authorization  │               │
 │                │                  ├─ Verify Token │
 │                │                  ├─ Extract User ID
 │                │                  ├─ Query Docs──>│
 │                │                  │<─ Docs List ─│
 │                │<──200 + Docs─────│               │
 │<─ Display Docs─│                  │               │
```

---

## Performance Considerations

### Caching Strategy
- **Query Results:** Cached in Redis for 1 hour
- **Cache Key:** `search:{user_id}:{query_text}` (exact match required)
- **Hit Rate:** Improves for repeated searches
- **Manual Invalidation:** Can clear patterns when documents updated

### Vector Search Optimization
- **Index:** Qdrant automatically indexes vectors with HNSW
- **Similarity Metric:** COSINE distance (efficient for embeddings)
- **Batch Operations:** Embeddings generated in batch for efficiency
- **Lazy Loading:** Sentence Transformer model loaded once and cached

### Database Optimization
- **Indexes:** Created on user_id, content_hash (deduplication), qdrant_point_id
- **Foreign Keys:** Referential integrity maintained
- **Connection Pooling:** SQLAlchemy manages pool (default 5-10 connections)

### LLM Efficiency
- **Context Truncation:** Limited to 12,000 characters to reduce token usage
- **Temperature:** Set to 0.2 for consistency and reduced randomness
- **Max Tokens:** Capped at 700 to control costs

---

## Error Handling

### HTTP Status Codes

| Code | Scenario |
|------|----------|
| 200 | Success |
| 201 | Resource created |
| 400 | Bad request (validation error, duplicate document) |
| 401 | Unauthorized (invalid token, wrong credentials) |
| 404 | Not found (document doesn't exist) |
| 503 | Service unavailable (OpenAI not configured) |

### Common Error Responses

**Authentication Error:**
```json
{
  "detail": "Invalid authentication credentials"
}
```

**Duplicate Document:**
```json
{
  "detail": "Document already exists"
}
```

**Unsupported File Type:**
```json
{
  "detail": "Unsupported document type: xyz"
}
```

**LLM Not Configured:**
```json
{
  "detail": "OPENAI_API_KEY is not configured"
}
```

---

## Future Enhancement Possibilities

1. **Multi-modal Search:** Support for images, tables, code snippets
2. **Document Versioning:** Track document updates and maintain history
3. **Advanced Chunking:** Semantic chunking, document structure-aware splitting
4. **Multi-language Support:** Multilingual embeddings and LLM responses
5. **Real-time Updates:** WebSocket support for live search results
6. **Analytics Dashboard:** Search trends, popular queries, performance metrics
7. **Fine-tuning:** Custom embedding models per use case
8. **Hybrid Search:** Combine vector search with keyword/BM25 search
9. **Document Access Control:** Granular permissions (private/shared documents)
10. **Batch Processing:** Async document upload and processing with job status

---

## Summary

The Knowledge Base Assistant is a production-ready semantic search system with:

- **Modular Architecture:** Clear separation of concerns (API, services, data layers)
- **Scalable Design:** Stateless backend, distributed vector DB, cached results
- **Secure:** JWT authentication, password hashing, SQL injection prevention
- **Flexible Configuration:** All parameters configurable via environment variables
- **Multi-tenancy:** User-isolated documents and queries
- **Production Ready:** Health checks, error handling, logging hooks
- **Cloud Native:** Docker and Kubernetes deployment ready

The system enables intelligent document ingestion, semantic search, and context-aware AI-powered answers using retrieval-augmented generation (RAG).


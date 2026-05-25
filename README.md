# Knowledge Base Assistant

**Knowledge Base Assistant** is a semantic search and retrieval system built with FastAPI that enables intelligent document ingestion, chunking, embedding generation, and similarity-based retrieval using vector databases. It uses Retrieval-Augmented Generation (RAG) to provide context-aware answers from uploaded documents.

## Architecture

```
Documents (PDF/TXT/SQL/Logs)
    ↓
Chunking (split into smaller pieces)
    ↓
Embeddings (convert text → vectors)
    ↓
Store in Qdrant (vector DB)
    ↓
Query → embedding → similarity search → results
```

## Tech Stack

- **Backend**: FastAPI (Python)
- **Vector DB**: Qdrant
- **Cache**: Redis
- **Database**: PostgreSQL
- **Embeddings**: Sentence Transformers
- **Containerization**: Docker
- **Orchestration**: Kubernetes

## Project Structure

```
knowledge-base-assistant/
├── backend/
│   ├── app/
│   │   ├── api/              # API routes
│   │   ├── models/           # Database models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic
│   │   ├── core/             # Configuration and security
│   │   └── main.py           # FastAPI app entry point
│   ├── requirements.txt
│   └── .env.example
├── docker/
│   ├── Dockerfile.backend
│   └── docker-compose.yml
├── kubernetes/
│   ├── manifest.yml          # All k8s resources
│   └── postgres-statefulset.yml
└── README.md
```

## Features

### Authentication & Authorization
- JWT-based authentication
- User registration and login
- Secure token management

### Document Management
- Support for PDF, TXT, SQL, and LOG files
- Automatic text extraction
- Document deduplication via content hash
- Chunk tracking and management

### Semantic Search
- Vector embeddings using Sentence Transformers
- Similarity-based search with Qdrant
- Result caching with Redis
- Search history tracking

### API Endpoints

#### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get token
- `GET /api/auth/me` - Get current user info

#### Documents
- `POST /api/documents/upload` - Upload and process document
- `GET /api/documents/` - List user documents
- `GET /api/documents/{document_id}` - Get document details
- `DELETE /api/documents/{document_id}` - Delete document

#### Query
- `POST /api/query/search` - Semantic search query
- `GET /api/query/history` - Get search history

## Installation

### Prerequisites
- Docker and Docker Compose (for containerized setup)
- Python 3.11+ (for local development)
- Kubernetes cluster (for K8s deployment)

### Local Development

1. **Clone repository**
```bash
git clone <repository-url>
cd knowledge-base-assistant
```

2. **Setup environment**
```bash
cd backend
cp .env.example .env
```

3. **Install dependencies**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements-api.txt
```

4. **Run the FastAPI app locally**
```bash
CREATE_TABLES_ON_STARTUP=false PYTHONPATH=backend uvicorn app.main:app --reload
```

Use `CREATE_TABLES_ON_STARTUP=false` when Postgres is not running locally yet.

5. **Run with Docker Compose**
```bash
docker-compose up -d
```

6. **Access the API**
- API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

## Docker Deployment

### Build and run all services

```bash
docker-compose up -d
```

### Services
- **Backend**: http://localhost:8000
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379
- **Qdrant**: http://localhost:6333

## Kubernetes Deployment

### Prerequisites
- Running Kubernetes cluster
- kubectl configured

### Deploy

```bash
# Create namespace and deploy all resources
kubectl apply -f kubernetes/manifest.yml

# Verify deployment
kubectl get pods -n knowledge-base
kubectl get svc -n knowledge-base
```

### Access Service

```bash
# Get LoadBalancer IP
kubectl get svc backend -n knowledge-base

# Port forward (if using ClusterIP)
kubectl port-forward svc/backend 8000:80 -n knowledge-base
```

### Scale Deployment

```bash
# Manual scaling
kubectl scale deployment backend --replicas=3 -n knowledge-base

# Check HPA status
kubectl get hpa -n knowledge-base
```

## Usage Examples

### 1. Register User
```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123",
    "full_name": "John Doe"
  }'
```

### 2. Login
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

### 3. Upload Document
```bash
curl -X POST "http://localhost:8000/api/documents/upload" \
  -H "Authorization: Bearer <token>" \
  -F "file=@document.pdf"
```

### 4. Search
```bash
curl -X POST "http://localhost:8000/api/query/search" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "What is machine learning?",
    "top_k": 5
  }'
```

## Real API Data Sample

The repository includes a small fetcher that pulls public incident data from
Cloudflare and GitHub Statuspage APIs, then creates knowledge-base-ready text
documents:

```bash
python3 sample_documents/fetch_cloud_status_data.py
```

Generated files are written to `sample_documents/generated/`:

- `real_cloud_status_incidents.txt` - raw incident summaries from the APIs
- `real_cloud_status_insights.txt` - operational insights tied to TechCorp-style cloud platform docs

After generating them, run the normal sample upload script:

```bash
./sample_documents/upload_samples.sh
```

Useful insight queries:

- Which cloud components appear most vulnerable based on recent public incidents?
- How should TechCorp update its incident escalation matrix based on real status data?
- What operational risks could affect TechCorp customer retention or SLA commitments?
- Compare the public incident durations with TechCorp's 99.99% uptime target.

## Configuration

### Environment Variables

Key environment variables (see `.env.example`):

```
DATABASE_URL=postgresql://user:password@postgres:5432/knowledge_base
REDIS_URL=redis://redis:6379/0
QDRANT_URL=http://qdrant:6333
SECRET_KEY=your-secret-key-change-in-production
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
CHUNK_SIZE=1024
CHUNK_OVERLAP=128
```

## Development

### Run locally with auto-reload
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Check code quality
```bash
# Format
black app/

# Lint
flake8 app/
```

## Performance Considerations

- **Caching**: Search results cached for 1 hour in Redis
- **Chunk Size**: Default 1024 tokens with 128 token overlap
- **Batch Processing**: Embeddings processed in batches
- **Auto-scaling**: K8s HPA configured for CPU-based scaling (70% threshold)

## Monitoring & Logging

- Search query logs stored in PostgreSQL
- Response times tracked
- Document processing metrics available
- Health checks on all services

## Contributing

1. Create a feature branch
2. Make changes
3. Test locally with Docker Compose
4. Submit pull request

## License

MIT

## Support

For issues, questions, or suggestions, please open an issue in the repository.

# FastAPI, Uvicorn, JWT, And What We Configured

This note explains the backend concepts we touched while setting up the first FastAPI layer of the Knowledge Based Assistant project.

It is written for a beginner, so it starts from the basics and then connects those basics to the exact project changes.

## FastAPI

FastAPI is the Python framework we are using to build the backend API.

An API is a set of URLs that other programs can call. For example:

```text
GET /health
POST /api/auth/register
POST /api/auth/login
POST /api/documents/upload
POST /api/query/search
```

Each URL points to Python code. When someone visits or calls that URL, FastAPI runs the matching Python function and returns a response, usually JSON.

Example:

```python
@router.get("/health")
def health_check():
    return {"status": "healthy"}
```

This means:

```text
When someone calls GET /health,
run health_check(),
return {"status": "healthy"}.
```

## Uvicorn

Uvicorn is the server that runs the FastAPI app.

FastAPI is the application code. Uvicorn is the thing that actually listens for web requests.

The request flow looks like this:

```text
Browser / frontend / curl
        |
        v
     Uvicorn
        |
        v
     FastAPI app
        |
        v
   Your Python functions
```

When we run:

```bash
uvicorn app.main:app --reload
```

we are saying:

```text
Start a web server.
Look inside app/main.py.
Find the variable named app.
Serve that FastAPI app.
Restart automatically when code changes.
```

In this project, the local command is:

```bash
CREATE_TABLES_ON_STARTUP=false PYTHONPATH=backend uvicorn app.main:app --reload
```

Breaking that down:

```bash
CREATE_TABLES_ON_STARTUP=false
```

This tells the app not to create database tables when starting. We use this while PostgreSQL is not running yet.

```bash
PYTHONPATH=backend
```

This tells Python:

```text
The backend folder is where imports should start from.
```

```bash
uvicorn
```

This starts the web server.

```bash
app.main:app
```

This means:

```python
from app.main import app
```

The first `app.main` points to:

```text
backend/app/main.py
```

The second `app` is the FastAPI object inside that file:

```python
app = create_app()
```

```bash
--reload
```

This means:

```text
Restart the server automatically when code changes.
```

This is useful during development.

## JWT

JWT stands for JSON Web Token.

It is a compact string used to prove that a user is logged in.

A normal login flow looks like this:

```text
1. User sends email and password.
2. Backend checks if the password is correct.
3. Backend creates a JWT.
4. Frontend stores that JWT.
5. Future requests include the JWT.
6. Backend reads the JWT and knows which user is making the request.
```

Example login response:

```json
{
  "access_token": "very.long.encoded.string",
  "token_type": "bearer"
}
```

Then the frontend sends future requests like this:

```http
Authorization: Bearer very.long.encoded.string
```

The JWT usually contains encoded information like:

```json
{
  "sub": "123",
  "exp": "expiry time"
}
```

`sub` means subject. In our app, it stores the user id.

So if the JWT contains:

```json
{
  "sub": "5"
}
```

the backend understands:

```text
This request belongs to user with id 5.
```

Important detail:

```text
A JWT is not encrypted by default.
It is encoded and signed.
```

That means the backend can verify:

```text
Did our server create this token?
Was it changed by someone?
Has it expired?
```

The signing uses a secret key from settings:

```python
secret_key: str = "your-secret-key-change-in-production"
```

In production, this should be changed to a strong private value.

## What We Configured

The project already had a FastAPI backend, but some pieces made it hard to start cleanly during early setup.

### App Startup

Before, `main.py` created database tables immediately when the file was imported:

```python
Base.metadata.create_all(bind=engine)
```

That meant even importing the app required PostgreSQL to be reachable.

That is inconvenient during early setup because routes like `/health` and `/docs` should work even while we are still configuring services.

So we moved table creation into FastAPI startup:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.create_tables_on_startup:
        Base.metadata.create_all(bind=engine)
    yield
```

Now we can control it with:

```bash
CREATE_TABLES_ON_STARTUP=false
```

That lets us start the API shell before the database is ready.

### App Factory

We added an app factory:

```python
def create_app() -> FastAPI:
    fastapi_app = FastAPI(...)
    ...
    return fastapi_app


app = create_app()
```

This keeps app setup organized.

It also makes the app easier to test later.

### Auth Fix

There was a bug in the auth file.

The route used:

```python
Depends(verify_token)
```

but `verify_token` was not imported.

We fixed the import.

There was also a mismatch between the README and actual login endpoint.

The README showed login using JSON:

```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

But the code expected separate query parameters.

We changed login to use a JSON body with this schema:

```python
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
```

Now login works like a normal API login endpoint.

### Lazy Loading

Some services were loading heavy dependencies immediately when the app started.

For example, the embedding service loaded the AI model right away:

```python
model = SentenceTransformer(settings.embedding_model)
```

That can be slow and may download model files.

But we do not need embeddings just to start FastAPI or open `/docs`.

So we changed it to load only when needed:

```python
@lru_cache
def get_embedding_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(settings.embedding_model)
```

Now the model loads only when we call document upload or search features.

We used the same idea for:

```text
Redis
Qdrant
PDF parsing
DOCX parsing
```

This keeps the app lightweight during initial setup.

## Requirements Files

The original `requirements.txt` included everything:

```text
FastAPI
Database
Redis
Qdrant
OpenAI
Sentence Transformers
Torch
PDF/DOCX tools
```

That is fine eventually, but for "configure FastAPI first," it is heavy.

`sentence-transformers` pulls in `torch`, which is a large machine learning dependency.

So we added:

```text
backend/requirements-api.txt
```

This installs only what we need to start the API:

```text
fastapi
uvicorn
sqlalchemy
psycopg2
pydantic
auth libraries
httpx for testing
```

Then `requirements.txt` still exists for the full app.

The beginner-friendly local flow is:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements-api.txt
CREATE_TABLES_ON_STARTUP=false PYTHONPATH=backend uvicorn app.main:app --reload
```

## Short Version

FastAPI is the backend framework.

Uvicorn is the server that runs FastAPI.

JWT is the login token used to prove a user is authenticated.

We configured the project so the API can start cleanly before PostgreSQL, Redis, Qdrant, and embeddings are fully wired up.

That gives us a stable foundation before adding database setup, auth testing, document upload, and semantic search.


# Local Qdrant, Redis, Docker, And Why No API Key Is Needed

This note explains how we are using Qdrant and Redis locally without creating cloud accounts or using API tokens.

It also explains what Docker is doing for us in this project.

## The Short Version

We are using these services:

```text
FastAPI  = our Python backend API
Postgres = normal database for users, documents, and query records
Redis    = fast cache
Qdrant   = vector database for semantic search
```

For now, we are running Redis and Qdrant locally through Docker.

That means:

```text
No Redis Cloud account needed.
No Qdrant Cloud account needed.
No API key needed.
No token needed.
```

They run on your own machine as local services.

## What Is Qdrant?

Qdrant is a vector database.

A normal database stores data like this:

```text
id: 1
filename: employee_handbook.txt
created_at: 2026-05-16
```

A vector database stores mathematical representations of meaning.

For example, text like:

```text
How do employees request leave?
```

can be converted into a list of numbers called an embedding:

```text
[0.12, -0.44, 0.83, ...]
```

That list of numbers represents the meaning of the sentence.

Qdrant stores those vectors and can answer:

```text
Which saved document chunks are closest in meaning to this query?
```

This is what enables semantic search.

Semantic search means:

```text
Search by meaning, not only by exact words.
```

Example:

```text
Query: "vacation policy"
```

Qdrant may find document chunks that say:

```text
Employees may apply for annual leave...
```

Even though the exact word "vacation" may not appear.

## What Is Redis?

Redis is a very fast in-memory data store.

In this project, Redis is used as a cache.

A cache stores temporary results so the app does not have to repeat expensive work.

Example:

```text
User asks: "What is the password policy?"
Backend searches Qdrant and prepares results.
Backend saves the result in Redis.
```

If the same user asks the same question again soon, the backend can read from Redis instead of doing all the work again.

This makes responses faster and reduces repeated processing.

## Why We Do Not Need API Keys Locally

An API key is usually needed when you use someone else's hosted service.

For example:

```text
Qdrant Cloud
Redis Cloud
OpenAI API
```

Those services live on the internet and belong to an external provider.

The provider needs to know:

```text
Who are you?
Are you allowed to use this service?
Should your account be billed?
```

That is why cloud services use API keys.

But local Docker services run on your own machine.

When we use local Qdrant, our app talks to:

```env
QDRANT_URL=http://qdrant:6333
QDRANT_API_KEY=
```

There is no token because the service is not protected by a cloud account.

When we use local Redis, our app talks to:

```env
REDIS_URL=redis://redis:6379/0
```

Again, no token is needed for our local development setup.

## What Is Docker?

Docker lets us run software in containers.

A container is like a small packaged environment that includes everything a service needs to run.

Instead of manually installing Postgres, Redis, and Qdrant on your laptop one by one, Docker can run them for us.

Without Docker, you might need to install:

```text
PostgreSQL manually
Redis manually
Qdrant manually
Correct versions manually
System dependencies manually
```

With Docker, we define the services in one file:

```text
docker-compose.yml
```

Then Docker starts them.

## What Is Docker Compose?

Docker Compose is a tool for running multiple Docker containers together.

Our app needs several services:

```text
backend
postgres
redis
qdrant
```

Docker Compose reads `docker-compose.yml` and starts all of them as a group.

In this project, the file contains:

```yaml
services:
  postgres:
    image: postgres:15-alpine

  redis:
    image: redis:7-alpine

  qdrant:
    image: qdrant/qdrant:latest

  backend:
    build:
      context: .
      dockerfile: docker/Dockerfile.backend
```

This means:

```text
Start a Postgres container.
Start a Redis container.
Start a Qdrant container.
Build and start our backend container.
```

## What Docker Is Doing In Our Project

Docker Compose creates a private network for the project.

Inside that network, containers can talk to each other using service names.

That is why our backend can use:

```env
DATABASE_URL=postgresql://user:password@postgres:5432/knowledge_base
REDIS_URL=redis://redis:6379/0
QDRANT_URL=http://qdrant:6333
```

Notice these names:

```text
postgres
redis
qdrant
```

Those are not internet domains.

They are Docker Compose service names.

So when the backend says:

```text
http://qdrant:6333
```

it means:

```text
Talk to the container named qdrant on port 6333.
```

When the backend says:

```text
redis://redis:6379/0
```

it means:

```text
Talk to the container named redis on port 6379.
```

This is why we do not need public URLs or API keys for local Redis/Qdrant.

Everything is running inside the same local Docker environment.

## Docker Ports

In `docker-compose.yml`, Qdrant has:

```yaml
ports:
  - "6333:6333"
```

This means:

```text
Expose Qdrant's internal port 6333 to your machine's port 6333.
```

So from your machine, you can access local Qdrant at:

```text
http://localhost:6333
```

But from inside the backend container, the backend accesses Qdrant at:

```text
http://qdrant:6333
```

Both point to the same Qdrant service, just from different places.

Redis has:

```yaml
ports:
  - "6379:6379"
```

So Redis is available locally on:

```text
localhost:6379
```

And inside Docker on:

```text
redis:6379
```

## Docker Volumes

Containers can be deleted and recreated.

If data only lived inside the container, deleting the container could delete the data.

Docker volumes solve this.

Our Compose file has:

```yaml
volumes:
  postgres_data:
  redis_data:
  qdrant_data:
```

These volumes store data outside the temporary container filesystem.

That means:

```text
Postgres data survives container restarts.
Redis data can survive container restarts.
Qdrant vector data survives container restarts.
```

## How The Search Flow Uses Qdrant

When a document is uploaded:

```text
1. Backend extracts text from the document.
2. Backend splits the text into smaller chunks.
3. Backend turns each chunk into an embedding vector.
4. Backend stores the vector in Qdrant.
5. Backend stores normal metadata in Postgres.
```

When a user searches:

```text
1. User sends a question.
2. Backend turns the question into an embedding vector.
3. Backend asks Qdrant for similar vectors.
4. Qdrant returns matching document chunks.
5. Backend returns those chunks as search results.
```

Qdrant is powerful because it can compare meaning at scale.

Instead of searching exact words, it searches vector similarity.

## How The Search Flow Uses Redis

Redis helps avoid repeated work.

When a user searches:

```text
1. Backend creates a cache key from the user id and query text.
2. Backend checks Redis for an existing result.
3. If Redis has it, backend returns the cached result.
4. If Redis does not have it, backend searches Qdrant.
5. Backend stores the result in Redis for next time.
```

This makes repeated searches faster.

## Local Vs Cloud

Local Qdrant:

```text
Runs on your machine
No account
No token
Good for learning and development
URL: http://qdrant:6333 inside Docker
URL: http://localhost:6333 from your machine
```

Qdrant Cloud:

```text
Runs on Qdrant's servers
Needs an account
Needs an API key
Good for production or shared deployments
URL: https://your-cluster-url.qdrant.io
```

Local Redis:

```text
Runs on your machine
No account
No token in our dev setup
Good for development
URL: redis://redis:6379/0 inside Docker
```

Redis Cloud:

```text
Runs on Redis provider's servers
Needs an account
Usually needs a password or token
Good for production or managed hosting
```

## Where Tokens Would Go If We Used Cloud

For Qdrant Cloud, the token would go in:

```text
backend/.env
```

Example:

```env
QDRANT_URL=https://your-cluster-url.qdrant.io
QDRANT_API_KEY=your_qdrant_api_key_here
QDRANT_COLLECTION=documents
```

But for our current local setup:

```env
QDRANT_URL=http://qdrant:6333
QDRANT_API_KEY=
QDRANT_COLLECTION=documents
```

Do not commit real tokens to GitHub.

Real secrets belong in local `.env` files or deployment secret managers.

## Commands We Will Use

To start the local services:

```bash
docker compose up -d
```

To see running containers:

```bash
docker compose ps
```

To see logs:

```bash
docker compose logs
```

To stop services:

```bash
docker compose down
```

To stop services and delete stored volumes:

```bash
docker compose down -v
```

Be careful with `down -v`.

It removes stored data.

## Why Docker Is Powerful

Docker is powerful because it makes complex setup repeatable.

Instead of saying:

```text
Install Postgres.
Install Redis.
Install Qdrant.
Configure ports.
Create databases.
Match versions.
Hope your machine is set up correctly.
```

we can say:

```bash
docker compose up -d
```

Docker then starts the services using the project configuration.

This makes development easier because every machine can run nearly the same environment.

## Summary

We are using local Qdrant and local Redis through Docker.

No Qdrant account is needed right now.

No Redis account is needed right now.

No API key is needed for local Qdrant or Redis in this project.

Docker Compose starts all required services and lets them communicate using service names like `qdrant`, `redis`, and `postgres`.

Qdrant powers semantic search.

Redis speeds things up by caching repeated search results.


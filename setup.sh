#!/bin/bash
# Quick setup script for Knowledge Base Assistant

set -e

echo "🚀 Knowledge Base Assistant - Setup Script"
echo "==========================================="

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Compose."
    exit 1
fi

echo "✅ Docker and Docker Compose found"

# Create .env file if it doesn't exist
if [ ! -f backend/.env ]; then
    echo "📝 Creating .env file from template..."
    cp backend/.env.example backend/.env
    echo "⚠️  Please update backend/.env with your actual configuration"
fi

# Pull Docker images
echo "🐳 Pulling Docker images..."
docker-compose pull

# Build and start containers
echo "🏗️  Building and starting services..."
docker-compose up -d

echo ""
echo "✅ Setup complete!"
echo ""
echo "📍 Service URLs:"
echo "   - API:     http://localhost:8000"
echo "   - Docs:    http://localhost:8000/docs"
echo "   - Postgres: localhost:5432"
echo "   - Redis:   localhost:6379"
echo "   - Qdrant:  http://localhost:6333"
echo ""
echo "📚 Next steps:"
echo "   1. Review backend/.env file"
echo "   2. Go to http://localhost:8000/docs for API documentation"
echo "   3. Create a user account"
echo "   4. Upload documents and start searching!"
echo ""
echo "🛑 To stop services: docker-compose down"

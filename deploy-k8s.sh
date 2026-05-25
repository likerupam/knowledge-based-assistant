#!/bin/bash
# Kubernetes deployment script

set -e

echo "☸️  Knowledge Base Assistant - Kubernetes Deployment"
echo "===================================================="

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install kubectl."
    exit 1
fi

# Check if cluster is accessible
echo "🔍 Checking Kubernetes cluster..."
kubectl cluster-info > /dev/null || exit 1
echo "✅ Kubernetes cluster is accessible"

# Build Docker image
echo "🐳 Building Docker image..."
docker build -t knowledge-base-backend:latest -f docker/Dockerfile.backend .

# Deploy to Kubernetes
echo "📦 Deploying to Kubernetes..."
kubectl apply -f kubernetes/manifest.yml

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🔍 Checking pod status..."
sleep 5
kubectl get pods -n knowledge-base

echo ""
echo "📍 Service URL:"
kubectl get svc backend -n knowledge-base

echo ""
echo "🛑 To remove deployment: kubectl delete namespace knowledge-base"

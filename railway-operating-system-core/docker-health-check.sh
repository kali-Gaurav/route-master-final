#!/bin/bash
# Docker Health Check Script
# Verifies all services are running correctly

echo "==================================="
echo "Railway OS - Health Check"
echo "==================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running"
    exit 1
fi

echo "✓ Docker is running"

# Check if containers are running
CONTAINERS=$(docker-compose ps -q)
if [ -z "$CONTAINERS" ]; then
    echo "❌ No containers are running"
    echo "   Run: make up"
    exit 1
fi

echo "✓ Containers are running"
echo ""

# Check individual services
echo "Service Status:"
echo "---------------"

# PostgreSQL
if docker-compose exec -T postgres pg_isready > /dev/null 2>&1; then
    echo "✓ PostgreSQL: Healthy"
else
    echo "❌ PostgreSQL: Unhealthy"
fi

# Redis
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo "✓ Redis: Healthy"
else
    echo "❌ Redis: Unhealthy"
fi

# Backend
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✓ Backend: Healthy"
else
    echo "❌ Backend: Unhealthy"
fi

# Frontend
if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "✓ Frontend: Healthy"
else
    echo "❌ Frontend: Unhealthy"
fi

echo ""
echo "==================================="
echo "Health check complete!"
echo "==================================="

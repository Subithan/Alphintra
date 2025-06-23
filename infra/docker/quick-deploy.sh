#!/bin/bash

# Quick deployment script - start working services first
echo "🚀 Quick Alphintra Deployment"
echo "=============================="

# Start infrastructure services first (they work)
echo "📦 Starting infrastructure services..."
docker-compose -f docker-compose.base.yml --env-file .env.dev up -d

echo "⏳ Waiting for infrastructure to be ready..."
sleep 30

# Start working application services
echo "🏗️  Starting working application services..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml --env-file .env.dev up -d auth-service broker-simulator

# Check status
echo "📊 Checking service status..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml --env-file .env.dev ps

echo ""
echo "✅ Quick deployment completed!"
echo "🌐 Working services are now available"
echo ""
echo "🔧 To add remaining services one by one:"
echo "   docker-compose -f docker-compose.yml -f docker-compose.dev.yml --env-file .env.dev up -d strategy-engine"
echo "   docker-compose -f docker-compose.yml -f docker-compose.dev.yml --env-file .env.dev up -d trading-api"
echo "   docker-compose -f docker-compose.yml -f docker-compose.dev.yml --env-file .env.dev up -d broker-connector"
echo "   docker-compose -f docker-compose.yml -f docker-compose.dev.yml --env-file .env.dev up -d gateway"
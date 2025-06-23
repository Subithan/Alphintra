#!/bin/bash

# Docker Compose Build Debug Script
# This script helps debug build issues step by step

echo "🔍 Alphintra Docker Build Debug Script"
echo "======================================="

# Function to check if a service builds successfully
test_service_build() {
    local service=$1
    echo ""
    echo "🧪 Testing $service build..."
    
    if docker-compose -f docker-compose.yml -f docker-compose.dev.yml --env-file .env.dev build $service; then
        echo "✅ $service: BUILD SUCCESS"
        return 0
    else
        echo "❌ $service: BUILD FAILED"
        return 1
    fi
}

# Test each service individually
echo "Testing each service individually..."

# Infrastructure services (should work)
echo ""
echo "📦 Testing Infrastructure Services..."
infrastructure_services=("postgres" "timescaledb" "redis-master" "kafka" "prometheus" "grafana")

for service in "${infrastructure_services[@]}"; do
    if docker-compose -f docker-compose.base.yml --env-file .env.dev build $service 2>/dev/null; then
        echo "✅ $service: OK"
    else
        echo "⚠️  $service: May need to be pulled"
    fi
done

# Application services (may have issues)
echo ""
echo "🏗️  Testing Application Services..."
application_services=("gateway" "auth-service" "trading-api" "strategy-engine" "broker-connector" "broker-simulator")

failed_services=()
for service in "${application_services[@]}"; do
    if test_service_build $service; then
        echo "✅ $service: Ready"
    else
        failed_services+=($service)
    fi
done

# Summary
echo ""
echo "📊 Build Test Summary:"
echo "======================"

if [ ${#failed_services[@]} -eq 0 ]; then
    echo "🎉 All services build successfully!"
    echo ""
    echo "🚀 Ready to run full deployment:"
    echo "   docker-compose -f docker-compose.yml -f docker-compose.dev.yml --env-file .env.dev up -d"
else
    echo "❌ Failed services: ${failed_services[*]}"
    echo ""
    echo "🔧 Next steps:"
    echo "1. Fix dependency issues in failed services"
    echo "2. Re-run this debug script"
    echo "3. Once all services pass, run full deployment"
fi

echo ""
echo "💡 Useful commands:"
echo "   - Test single service: docker-compose build <service-name>"
echo "   - View service logs: docker-compose logs <service-name>"
echo "   - Clean build cache: docker-compose build --no-cache <service-name>"
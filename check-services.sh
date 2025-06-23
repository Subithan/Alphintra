#!/bin/bash

# Alphintra Trading Platform - Service Status Checker
# This script checks the status of all infrastructure services

echo "🚀 Alphintra Trading Platform - Infrastructure Status Check"
echo "================================================================"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if a service is responding
check_service() {
    local service_name=$1
    local url=$2
    local expected_status=${3:-200}
    
    echo -n "Checking $service_name... "
    
    if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "$expected_status"; then
        echo -e "${GREEN}✓ HEALTHY${NC}"
        return 0
    else
        echo -e "${RED}✗ UNHEALTHY${NC}"
        return 1
    fi
}

# Function to check database connectivity
check_database() {
    local db_name=$1
    local container=$2
    local user=$3
    local database=$4
    
    echo -n "Checking $db_name... "
    
    if docker exec "$container" pg_isready -U "$user" -d "$database" >/dev/null 2>&1; then
        echo -e "${GREEN}✓ CONNECTED${NC}"
        return 0
    else
        echo -e "${RED}✗ DISCONNECTED${NC}"
        return 1
    fi
}

# Function to check Kafka topics
check_kafka_topics() {
    echo -n "Checking Kafka topics... "
    
    topics=$(docker exec alphintra-kafka kafka-topics --list --bootstrap-server localhost:9092 2>/dev/null | wc -l)
    
    if [ "$topics" -gt 0 ]; then
        echo -e "${GREEN}✓ $topics TOPICS AVAILABLE${NC}"
        return 0
    else
        echo -e "${RED}✗ NO TOPICS FOUND${NC}"
        return 1
    fi
}

echo "📊 Container Status:"
echo "-------------------"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" --filter "name=alphintra-"
echo ""

echo "🔍 Service Health Checks:"
echo "-------------------------"

# Database checks
check_database "PostgreSQL" "alphintra-postgres" "alphintra" "alphintra"
check_database "TimescaleDB" "alphintra-timescaledb" "timescale" "timescaledb"

# Redis check
echo -n "Checking Redis... "
if docker exec alphintra-redis redis-cli -a redis123 ping >/dev/null 2>&1; then
    echo -e "${GREEN}✓ CONNECTED${NC}"
else
    echo -e "${RED}✗ DISCONNECTED${NC}"
fi

# Kafka checks
check_kafka_topics

# Service endpoint checks
check_service "MLflow" "http://localhost:5001/health" "200"
check_service "MinIO" "http://localhost:9001/minio/health/live" "200"
check_service "Grafana" "http://localhost:3000/api/health" "200"
check_service "Prometheus" "http://localhost:9090/-/healthy" "200"
check_service "Jaeger" "http://localhost:16686/" "200"

echo ""
echo "📋 Service URLs:"
echo "----------------"
echo -e "${BLUE}MLflow:${NC}     http://localhost:5001"
echo -e "${BLUE}MinIO:${NC}      http://localhost:9001 (admin/admin123)"
echo -e "${BLUE}Grafana:${NC}    http://localhost:3000 (admin/admin)"
echo -e "${BLUE}Prometheus:${NC} http://localhost:9090"
echo -e "${BLUE}Jaeger:${NC}     http://localhost:16686"
echo -e "${BLUE}PostgreSQL:${NC} localhost:5432 (alphintra/alphintra123)"
echo -e "${BLUE}TimescaleDB:${NC} localhost:5433 (timescale/timescale123)"
echo -e "${BLUE}Redis:${NC}      localhost:6379 (password: redis123)"
echo -e "${BLUE}Kafka:${NC}      localhost:9092"
echo ""

echo "🗃️ Database Tables Status:"
echo "---------------------------"
echo -n "PostgreSQL tables: "
postgres_tables=$(docker exec alphintra-postgres psql -U alphintra -d alphintra -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | tr -d ' ')
if [ "$postgres_tables" -gt 0 ]; then
    echo -e "${GREEN}$postgres_tables tables created${NC}"
else
    echo -e "${RED}No tables found${NC}"
fi

echo -n "TimescaleDB hypertables: "
timescale_tables=$(docker exec alphintra-timescaledb psql -U timescale -d timescaledb -t -c "SELECT COUNT(*) FROM timescaledb_information.hypertables;" 2>/dev/null | tr -d ' ')
if [ "$timescale_tables" -gt 0 ]; then
    echo -e "${GREEN}$timescale_tables hypertables created${NC}"
else
    echo -e "${RED}No hypertables found${NC}"
fi

echo ""
echo "📈 Kafka Topics:"
echo "----------------"
docker exec alphintra-kafka kafka-topics --list --bootstrap-server localhost:9092 2>/dev/null | while read topic; do
    echo -e "${GREEN}✓${NC} $topic"
done

echo ""
echo "🔧 Quick Commands:"
echo "------------------"
echo "View logs:        docker logs <container_name>"
echo "Restart service:  docker-compose restart <service_name>"
echo "Stop all:         docker-compose down"
echo "Start all:        docker-compose up -d"
echo "Database shell:   docker exec -it alphintra-postgres psql -U alphintra -d alphintra"
echo "Redis shell:      docker exec -it alphintra-redis redis-cli -a redis123"
echo "Kafka shell:      docker exec -it alphintra-kafka bash"
echo ""

echo "✅ Infrastructure Status Check Complete!"
echo "Ready to start application services."
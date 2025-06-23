#!/bin/bash
# Alphintra Trading Platform - Local Development Deployment
# Quick deployment using Docker Compose for development and testing

set -e  # Exit on error

# Colors
RED='\033[31m'
GREEN='\033[32m'
YELLOW='\033[33m'
BLUE='\033[34m'
CYAN='\033[36m'
RESET='\033[0m'

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${RESET}"
}

success() {
    echo -e "${GREEN}✅ $1${RESET}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${RESET}"
}

error() {
    echo -e "${RED}❌ $1${RESET}"
    exit 1
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites for local deployment..."
    
    if ! command -v docker &> /dev/null; then
        error "Docker is required but not installed"
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is required but not installed"
    fi
    
    # Check if Docker is running
    if ! docker info &> /dev/null; then
        error "Docker is not running. Please start Docker Desktop"
    fi
    
    success "Prerequisites satisfied"
}

# Create environment file
create_env_file() {
    log "Creating environment configuration..."
    
    cat > .env.local << EOF
# Alphintra Local Development Environment
COMPOSE_PROJECT_NAME=alphintra-local
ENVIRONMENT=development

# Database Configuration
POSTGRES_DB=alphintra_dev
POSTGRES_USER=alphintra
POSTGRES_PASSWORD=dev_password_123
DATABASE_URL=postgresql://alphintra:dev_password_123@postgres:5432/alphintra_dev

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=kafka:9092

# API Configuration
API_PORT=8080
JWT_SECRET=dev_jwt_secret_key_123

# Trading Configuration
TRADING_MODE=simulation
MAX_POSITION_SIZE=10000
RISK_LIMIT=50000

# Market Data Configuration
MARKET_DATA_SOURCE=simulation
ENABLE_PAPER_TRADING=true

# AI/ML Configuration
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
GOOGLE_API_KEY=your_google_key_here

# Monitoring Configuration
GRAFANA_ADMIN_PASSWORD=admin123
PROMETHEUS_RETENTION=7d

# Logging
LOG_LEVEL=INFO
ENABLE_DEBUG_LOGS=true
EOF
    
    success "Environment file created"
}

# Create Docker Compose file
create_docker_compose() {
    log "Creating Docker Compose configuration..."
    
    cat > docker-compose.local.yml << 'EOF'
services:
  # Core Infrastructure
  postgres:
    image: postgres:14-alpine
    container_name: alphintra-postgres
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./infrastructure/database/init:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 30s
      timeout: 10s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: alphintra-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 5

  kafka:
    image: confluentinc/cp-kafka:latest
    container_name: alphintra-kafka
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: "true"
    volumes:
      - kafka_data:/var/lib/kafka/data

  zookeeper:
    image: confluentinc/cp-zookeeper:latest
    container_name: alphintra-zookeeper
    ports:
      - "2181:2181"
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    volumes:
      - zookeeper_data:/var/lib/zookeeper/data

  # Trading Services (using Python image with volume mounts)
  trading-engine:
    image: python:3.11-slim
    container_name: alphintra-trading-engine
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      kafka:
        condition: service_started
    ports:
      - "8081:8080"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - KAFKA_BOOTSTRAP_SERVERS=${KAFKA_BOOTSTRAP_SERVERS}
      - TRADING_MODE=${TRADING_MODE}
      - LOG_LEVEL=${LOG_LEVEL}
    volumes:
      - ./src/core/trading:/app
    working_dir: /app
    command: bash -c "pip install -r requirements.txt && python main.py"
    restart: unless-stopped

  market-data-engine:
    image: python:3.11-slim
    container_name: alphintra-market-data
    depends_on:
      - redis
      - kafka
    ports:
      - "8082:8080"
    environment:
      - REDIS_URL=${REDIS_URL}
      - KAFKA_BOOTSTRAP_SERVERS=${KAFKA_BOOTSTRAP_SERVERS}
      - MARKET_DATA_SOURCE=${MARKET_DATA_SOURCE}
      - LOG_LEVEL=${LOG_LEVEL}
    volumes:
      - ./src/core/market-data:/app
    working_dir: /app
    command: bash -c "pip install -r requirements.txt && python main.py"
    restart: unless-stopped

  risk-engine:
    image: python:3.11-slim
    container_name: alphintra-risk-engine
    depends_on:
      - postgres
      - redis
    ports:
      - "8083:8080"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - MAX_POSITION_SIZE=${MAX_POSITION_SIZE}
      - RISK_LIMIT=${RISK_LIMIT}
      - LOG_LEVEL=${LOG_LEVEL}
    volumes:
      - ./src/core/risk:/app
    working_dir: /app
    command: bash -c "pip install -r requirements.txt && python main.py"
    restart: unless-stopped

  # AI/ML Services
  llm-analyzer:
    image: python:3.11-slim
    container_name: alphintra-llm-analyzer
    depends_on:
      - redis
      - postgres
    ports:
      - "8084:8080"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - LOG_LEVEL=${LOG_LEVEL}
    volumes:
      - ./src/advanced-ai/market-analysis:/app
    working_dir: /app
    command: bash -c "pip install -r requirements.txt && python main.py"
    restart: unless-stopped

  # API Gateway
  api-gateway:
    image: python:3.11-slim
    container_name: alphintra-api-gateway
    depends_on:
      - trading-engine
      - market-data-engine
      - risk-engine
    ports:
      - "${API_PORT}:8080"
    environment:
      - TRADING_ENGINE_URL=http://trading-engine:8080
      - MARKET_DATA_URL=http://market-data-engine:8080
      - RISK_ENGINE_URL=http://risk-engine:8080
      - LLM_ANALYZER_URL=http://llm-analyzer:8080
      - JWT_SECRET=${JWT_SECRET}
      - LOG_LEVEL=${LOG_LEVEL}
    volumes:
      - ./infrastructure/api-gateway:/app
    working_dir: /app
    command: bash -c "pip install -r requirements.txt && python main.py"
    restart: unless-stopped

  # Web Dashboard
  web-dashboard:
    image: node:18-alpine
    container_name: alphintra-dashboard
    depends_on:
      - api-gateway
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:${API_PORT}
      - REACT_APP_ENVIRONMENT=${ENVIRONMENT}
    volumes:
      - ./src/web:/app
    working_dir: /app
    command: sh -c "npm install && npm start"
    restart: unless-stopped

  # Monitoring Stack
  prometheus:
    image: prom/prometheus:latest
    container_name: alphintra-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./infrastructure/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=${PROMETHEUS_RETENTION}'
      - '--web.enable-lifecycle'
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: alphintra-grafana
    depends_on:
      - prometheus
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana_data:/var/lib/grafana
      - ./infrastructure/monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./infrastructure/monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
    restart: unless-stopped

  # Documentation Server
  docs:
    image: nginx:alpine
    container_name: alphintra-docs
    ports:
      - "8000:80"
    volumes:
      - ./docs:/usr/share/nginx/html:ro
      - ./infrastructure/nginx/docs.conf:/etc/nginx/conf.d/default.conf:ro
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  kafka_data:
  zookeeper_data:
  prometheus_data:
  grafana_data:

networks:
  default:
    name: alphintra-network
EOF
    
    success "Docker Compose configuration created"
}

# Create monitoring configuration
create_monitoring_config() {
    log "Creating monitoring configurations..."
    
    # Create monitoring directory
    mkdir -p infrastructure/monitoring/grafana/{dashboards,datasources}
    
    # Prometheus configuration
    cat > infrastructure/monitoring/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'alphintra-trading-engine'
    static_configs:
      - targets: ['trading-engine:8080']
    metrics_path: '/metrics'
    scrape_interval: 5s

  - job_name: 'alphintra-market-data'
    static_configs:
      - targets: ['market-data-engine:8080']
    metrics_path: '/metrics'
    scrape_interval: 5s

  - job_name: 'alphintra-risk-engine'
    static_configs:
      - targets: ['risk-engine:8080']
    metrics_path: '/metrics'
    scrape_interval: 5s

  - job_name: 'alphintra-api-gateway'
    static_configs:
      - targets: ['api-gateway:8080']
    metrics_path: '/metrics'
    scrape_interval: 5s

  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
EOF

    # Grafana datasource
    cat > infrastructure/monitoring/grafana/datasources/prometheus.yml << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF

    success "Monitoring configuration created"
}

# Create database initialization
create_db_init() {
    log "Creating database initialization scripts..."
    
    mkdir -p infrastructure/database/init
    
    cat > infrastructure/database/init/001_init_schema.sql << 'EOF'
-- Alphintra Trading Platform Database Schema
-- Development/Local Environment

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS trading;
CREATE SCHEMA IF NOT EXISTS risk;
CREATE SCHEMA IF NOT EXISTS market_data;
CREATE SCHEMA IF NOT EXISTS compliance;
CREATE SCHEMA IF NOT EXISTS ai;

-- Trading tables
CREATE TABLE IF NOT EXISTS trading.orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(4) NOT NULL CHECK (side IN ('BUY', 'SELL')),
    quantity DECIMAL(18,8) NOT NULL,
    order_type VARCHAR(20) NOT NULL,
    price DECIMAL(18,8),
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    account_id VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS trading.executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID REFERENCES trading.orders(id),
    venue VARCHAR(20) NOT NULL,
    execution_price DECIMAL(18,8) NOT NULL,
    execution_quantity DECIMAL(18,8) NOT NULL,
    execution_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    commission DECIMAL(18,8) DEFAULT 0
);

CREATE TABLE IF NOT EXISTS trading.positions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id VARCHAR(50) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    quantity DECIMAL(18,8) NOT NULL DEFAULT 0,
    average_price DECIMAL(18,8),
    unrealized_pnl DECIMAL(18,8) DEFAULT 0,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(account_id, symbol)
);

-- Market data tables
CREATE TABLE IF NOT EXISTS market_data.quotes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    symbol VARCHAR(20) NOT NULL,
    bid DECIMAL(18,8) NOT NULL,
    ask DECIMAL(18,8) NOT NULL,
    last DECIMAL(18,8),
    volume BIGINT DEFAULT 0,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Risk tables
CREATE TABLE IF NOT EXISTS risk.limits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id VARCHAR(50) NOT NULL,
    limit_type VARCHAR(50) NOT NULL,
    limit_value DECIMAL(18,8) NOT NULL,
    current_value DECIMAL(18,8) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_orders_symbol_status ON trading.orders(symbol, status);
CREATE INDEX IF NOT EXISTS idx_orders_account_created ON trading.orders(account_id, created_at);
CREATE INDEX IF NOT EXISTS idx_positions_account ON trading.positions(account_id);
CREATE INDEX IF NOT EXISTS idx_quotes_symbol_timestamp ON market_data.quotes(symbol, timestamp);

-- Insert sample data for development
INSERT INTO trading.positions (account_id, symbol, quantity, average_price) VALUES
('dev-account-1', 'AAPL', 100, 150.00),
('dev-account-1', 'GOOGL', 10, 2800.00),
('dev-account-1', 'MSFT', 50, 300.00)
ON CONFLICT (account_id, symbol) DO NOTHING;

INSERT INTO risk.limits (account_id, limit_type, limit_value) VALUES
('dev-account-1', 'MAX_POSITION_SIZE', 10000),
('dev-account-1', 'MAX_DAILY_LOSS', 5000),
('dev-account-1', 'MAX_LEVERAGE', 3.0)
ON CONFLICT DO NOTHING;
EOF

    success "Database initialization created"
}

# Start services
start_services() {
    log "Starting Alphintra services..."
    
    # Load environment
    export $(cat .env.local | grep -v '^#' | xargs)
    
    # Start services (no build needed - using base images)
    docker-compose -f docker-compose.local.yml up -d
    
    success "Services started"
}

# Wait for services
wait_for_services() {
    log "Waiting for services to be ready..."
    
    # Wait for database
    echo "Waiting for PostgreSQL..."
    timeout=60
    while ! docker exec alphintra-postgres pg_isready -U alphintra >/dev/null 2>&1; do
        timeout=$((timeout - 1))
        if [ $timeout -eq 0 ]; then
            error "PostgreSQL failed to start"
        fi
        sleep 1
    done
    
    # Wait for Redis
    echo "Waiting for Redis..."
    timeout=30
    while ! docker exec alphintra-redis redis-cli ping >/dev/null 2>&1; do
        timeout=$((timeout - 1))
        if [ $timeout -eq 0 ]; then
            error "Redis failed to start"
        fi
        sleep 1
    done
    
    # Wait for API Gateway
    echo "Waiting for API Gateway..."
    timeout=60
    while ! curl -f http://localhost:8080/health >/dev/null 2>&1; do
        timeout=$((timeout - 1))
        if [ $timeout -eq 0 ]; then
            warning "API Gateway may not be ready yet"
            break
        fi
        sleep 2
    done
    
    success "Core services are ready"
}

# Show status
show_status() {
    log "Checking service status..."
    
    echo -e "\n${CYAN}Docker Container Status:${RESET}"
    docker-compose -f docker-compose.local.yml ps
    
    echo -e "\n${CYAN}Service Health Checks:${RESET}"
    
    # Check API Gateway
    if curl -f http://localhost:8080/health >/dev/null 2>&1; then
        echo -e "✅ API Gateway: ${GREEN}Healthy${RESET}"
    else
        echo -e "❌ API Gateway: ${RED}Unhealthy${RESET}"
    fi
    
    # Check Database
    if docker exec alphintra-postgres pg_isready -U alphintra >/dev/null 2>&1; then
        echo -e "✅ PostgreSQL: ${GREEN}Healthy${RESET}"
    else
        echo -e "❌ PostgreSQL: ${RED}Unhealthy${RESET}"
    fi
    
    # Check Redis
    if docker exec alphintra-redis redis-cli ping >/dev/null 2>&1; then
        echo -e "✅ Redis: ${GREEN}Healthy${RESET}"
    else
        echo -e "❌ Redis: ${RED}Unhealthy${RESET}"
    fi
    
    success "Status check complete"
}

# Create sample Dockerfiles
create_dockerfiles() {
    log "Creating sample Dockerfiles..."
    
    # Trading Engine Dockerfile
    mkdir -p src/core/trading
    cat > src/core/trading/Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Start application
CMD ["python", "main.py"]
EOF

    # Create basic requirements.txt
    cat > src/core/trading/requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
redis==5.0.1
kafka-python==2.0.2
prometheus-client==0.19.0
pydantic==2.5.0
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
asyncpg==0.29.0
aioredis==2.0.1
pandas==2.1.4
numpy==1.25.2
requests==2.31.0
httpx==0.25.2
EOF

    # Create similar structure for other services
    for service in "market-data" "risk"; do
        mkdir -p "src/core/$service"
        cp "src/core/trading/Dockerfile" "src/core/$service/"
        cp "src/core/trading/requirements.txt" "src/core/$service/"
    done
    
    # LLM Analyzer Dockerfile
    mkdir -p src/advanced-ai/market-analysis
    cp src/core/trading/Dockerfile src/advanced-ai/market-analysis/
    cat > src/advanced-ai/market-analysis/requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn==0.24.0
openai==1.6.1
anthropic==0.8.1
google-generativeai==0.3.2
transformers==4.36.2
torch==2.1.2
sentence-transformers==2.2.2
spacy==3.7.2
feedparser==6.0.10
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
redis==5.0.1
prometheus-client==0.19.0
pandas==2.1.4
numpy==1.25.2
requests==2.31.0
aiohttp==3.9.1
EOF

    success "Dockerfiles created"
}

# Main function
main() {
    echo -e "${CYAN}========================================${RESET}"
    echo -e "${CYAN}  ⚡ Alphintra Local Deployment${RESET}"
    echo -e "${CYAN}========================================${RESET}"
    echo ""
    
    local start_time=$(date +%s)
    
    check_prerequisites
    create_env_file
    create_docker_compose
    create_monitoring_config
    create_db_init
    start_services
    wait_for_services
    show_status
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    local minutes=$((duration / 60))
    local seconds=$((duration % 60))
    
    echo ""
    echo -e "${GREEN}🎉 Alphintra local deployment complete!${RESET}"
    echo -e "${GREEN}⏱️  Deployment time: ${minutes}m ${seconds}s${RESET}"
    echo ""
    echo -e "${CYAN}🌐 Access URLs:${RESET}"
    echo -e "  📊 Trading Dashboard: ${GREEN}http://localhost:3000${RESET}"
    echo -e "  🔌 API Gateway:       ${GREEN}http://localhost:8080${RESET}"
    echo -e "  📈 Monitoring:        ${GREEN}http://localhost:3001${RESET} (admin/admin123)"
    echo -e "  📋 Documentation:     ${GREEN}http://localhost:8000${RESET}"
    echo -e "  🗄️  Database:          ${GREEN}localhost:5432${RESET} (alphintra/dev_password_123)"
    echo ""
    echo -e "${CYAN}🔧 Useful Commands:${RESET}"
    echo -e "  View logs:     ${YELLOW}docker-compose -f docker-compose.local.yml logs -f${RESET}"
    echo -e "  Stop services: ${YELLOW}docker-compose -f docker-compose.local.yml down${RESET}"
    echo -e "  Restart:       ${YELLOW}docker-compose -f docker-compose.local.yml restart${RESET}"
    echo ""
}

# Error handling
trap 'error "Local deployment failed on line $LINENO"' ERR

# Run main function
main "$@"
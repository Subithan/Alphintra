# alphintra Trading Platform Makefile

.PHONY: help build up down logs clean test lint format install dev prod restart status health

# Default target
help:
	@echo "alphintra Trading Platform - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  make install    - Install development dependencies"
	@echo "  make dev        - Start development environment"
	@echo "  make build      - Build all Docker images"
	@echo "  make up         - Start all services"
	@echo "  make down       - Stop all services"
	@echo "  make restart    - Restart all services"
	@echo "  make logs       - Show logs from all services"
	@echo "  make status     - Show status of all services"
	@echo "  make health     - Check health of all services"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  make test       - Run all tests"
	@echo "  make lint       - Run linting on all code"
	@echo "  make format     - Format all code"
	@echo ""
	@echo "Production:"
	@echo "  make prod       - Start production environment"
	@echo "  make deploy     - Deploy to production"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean      - Clean up Docker resources"
	@echo "  make reset      - Reset entire environment"
	@echo "  make backup     - Backup databases"
	@echo "  make restore    - Restore from backup"

# Development commands
install:
	@echo "Installing development dependencies..."
	@if command -v python3 >/dev/null 2>&1; then \
		python3 -m pip install --upgrade pip; \
		python3 -m pip install pre-commit black flake8 pytest; \
		pre-commit install; \
	else \
		echo "Python 3 not found. Please install Python 3 first."; \
	fi
	@if command -v docker >/dev/null 2>&1; then \
		echo "Docker is available"; \
	else \
		echo "Docker not found. Please install Docker first."; \
	fi
	@if command -v docker-compose >/dev/null 2>&1; then \
		echo "Docker Compose is available"; \
	else \
		echo "Docker Compose not found. Please install Docker Compose first."; \
	fi

dev:
	@echo "Starting development environment..."
	@if [ -f docker-compose.dev.yml ]; then \
		docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d; \
	else \
		docker-compose up -d; \
	fi
	@echo "Development environment started!"
	@echo "Services available at:"
	@echo "  - API Gateway: http://localhost:8080"
	@echo "  - Grafana: http://localhost:3001 (admin/admin123)"
	@echo "  - Prometheus: http://localhost:9090"
	@echo "  - MLflow: http://localhost:5000"

build:
	@echo "Building all Docker images..."
	docker-compose build --parallel
	@echo "Build completed!"

up:
	@echo "Starting all services..."
	docker-compose up -d
	@echo "All services started!"
	@make status

down:
	@echo "Stopping all services..."
	docker-compose down
	@echo "All services stopped!"

restart:
	@echo "Restarting all services..."
	docker-compose restart
	@echo "All services restarted!"

logs:
	@echo "Showing logs from all services..."
	docker-compose logs -f

status:
	@echo "Service Status:"
	@docker-compose ps

health:
	@echo "Checking service health..."
	@echo "Gateway Health:"
	@curl -s http://localhost:8080/actuator/health | jq . || echo "Gateway not responding"
	@echo "\nAuth Service Health:"
	@curl -s http://localhost:8001/health | jq . || echo "Auth Service not responding"
	@echo "\nTrading API Health:"
	@curl -s http://localhost:8002/health | jq . || echo "Trading API not responding"
	@echo "\nStrategy Engine Health:"
	@curl -s http://localhost:8003/health | jq . || echo "Strategy Engine not responding"
	@echo "\nBroker Connector Health:"
	@curl -s http://localhost:8005/health | jq . || echo "Broker Connector not responding"
	@echo "\nBroker Simulator Health:"
	@curl -s http://localhost:8006/health | jq . || echo "Broker Simulator not responding"

# Testing and quality
test:
	@echo "Running all tests..."
	@echo "Testing Auth Service..."
	@cd src/backend/auth-service && python -m pytest tests/ -v || true
	@echo "Testing Trading API..."
	@cd src/backend/trading-api && python -m pytest tests/ -v || true
	@echo "Testing Strategy Engine..."
	@cd src/backend/strategy-engine && python -m pytest tests/ -v || true
	@echo "Testing Broker Connector..."
	@cd src/backend/broker-connector && python -m pytest tests/ -v || true
	@echo "Testing Broker Simulator..."
	@cd src/backend/broker-simulator && python -m pytest tests/ -v || true
	@echo "Testing Gateway..."
	@cd src/backend/gateway && ./mvnw test || true

lint:
	@echo "Running linting..."
	@echo "Linting Python code..."
	@find src/backend -name "*.py" -not -path "*/venv/*" -not -path "*/__pycache__/*" | xargs flake8 --max-line-length=88 --extend-ignore=E203,W503 || true
	@echo "Linting Java code..."
	@cd src/backend/gateway && ./mvnw checkstyle:check || true

format:
	@echo "Formatting code..."
	@echo "Formatting Python code..."
	@find src/backend -name "*.py" -not -path "*/venv/*" -not -path "*/__pycache__/*" | xargs black --line-length=88 || true
	@echo "Formatting Java code..."
	@cd src/backend/gateway && ./mvnw spotless:apply || true

# Production commands
prod:
	@echo "Starting production environment..."
	@if [ -f docker-compose.prod.yml ]; then \
		docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d; \
	else \
		echo "Production configuration not found. Using default configuration."; \
		docker-compose up -d; \
	fi
	@echo "Production environment started!"

deploy:
	@echo "Deploying to production..."
	@echo "Building production images..."
	@docker-compose -f docker-compose.yml -f docker-compose.prod.yml build
	@echo "Starting production services..."
	@docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
	@echo "Production deployment completed!"

# Maintenance commands
clean:
	@echo "Cleaning up Docker resources..."
	docker-compose down -v --remove-orphans
	docker system prune -f
	docker volume prune -f
	@echo "Cleanup completed!"

reset:
	@echo "Resetting entire environment..."
	@echo "WARNING: This will delete all data. Press Ctrl+C to cancel, or wait 10 seconds to continue..."
	@sleep 10
	docker-compose down -v --remove-orphans
	docker system prune -af
	docker volume prune -f
	@echo "Environment reset completed!"

backup:
	@echo "Creating database backups..."
	@mkdir -p backups
	@echo "Backing up PostgreSQL..."
	@docker-compose exec -T postgres pg_dump -U alphintra alphintra > backups/postgres_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "Backing up TimescaleDB..."
	@docker-compose exec -T timescaledb pg_dump -U timescale timescaledb > backups/timescaledb_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "Backing up Redis..."
	@docker-compose exec -T redis redis-cli --rdb - > backups/redis_$(shell date +%Y%m%d_%H%M%S).rdb
	@echo "Backup completed! Files saved in backups/ directory"

restore:
	@echo "Available backups:"
	@ls -la backups/ || echo "No backups found"
	@echo "To restore, run:"
	@echo "  docker-compose exec -T postgres psql -U alphintra alphintra < backups/postgres_YYYYMMDD_HHMMSS.sql"
	@echo "  docker-compose exec -T timescaledb psql -U timescale timescaledb < backups/timescaledb_YYYYMMDD_HHMMSS.sql"

# Service-specific commands
gateway-logs:
	docker-compose logs -f gateway

auth-logs:
	docker-compose logs -f auth-service

trading-logs:
	docker-compose logs -f trading-api

strategy-logs:
	docker-compose logs -f strategy-engine

broker-logs:
	docker-compose logs -f broker-connector

simulator-logs:
	docker-compose logs -f broker-simulator

db-logs:
	docker-compose logs -f postgres timescaledb

infra-logs:
	docker-compose logs -f redis kafka zookeeper

monitoring-logs:
	docker-compose logs -f prometheus grafana mlflow

# Database commands
db-shell:
	@echo "Connecting to PostgreSQL..."
	docker-compose exec postgres psql -U alphintra alphintra

tsdb-shell:
	@echo "Connecting to TimescaleDB..."
	docker-compose exec timescaledb psql -U timescale timescaledb

redis-shell:
	@echo "Connecting to Redis..."
	docker-compose exec redis redis-cli

# Monitoring commands
prometheus:
	@echo "Opening Prometheus..."
	@open http://localhost:9090 || echo "Visit http://localhost:9090"

grafana:
	@echo "Opening Grafana..."
	@open http://localhost:3001 || echo "Visit http://localhost:3001 (admin/admin123)"

mlflow:
	@echo "Opening MLflow..."
	@open http://localhost:5000 || echo "Visit http://localhost:5000"

# Development helpers
shell:
	@echo "Available shells:"
	@echo "  make gateway-shell    - Gateway container shell"
	@echo "  make auth-shell       - Auth service shell"
	@echo "  make trading-shell    - Trading API shell"
	@echo "  make strategy-shell   - Strategy engine shell"
	@echo "  make broker-shell     - Broker connector shell"
	@echo "  make simulator-shell  - Broker simulator shell"

gateway-shell:
	docker-compose exec gateway /bin/bash

auth-shell:
	docker-compose exec auth-service /bin/bash

trading-shell:
	docker-compose exec trading-api /bin/bash

strategy-shell:
	docker-compose exec strategy-engine /bin/bash

broker-shell:
	docker-compose exec broker-connector /bin/bash

simulator-shell:
	docker-compose exec broker-simulator /bin/bash

# Quick start
quick-start:
	@echo "Quick starting alphintra Trading Platform..."
	@make build
	@make up
	@echo "Waiting for services to be ready..."
	@sleep 30
	@make health
	@echo ""
	@echo "🚀 alphintra Trading Platform is ready!"
	@echo ""
	@echo "Access points:"
	@echo "  - API Gateway: http://localhost:8080"
	@echo "  - Grafana Dashboard: http://localhost:3001 (admin/admin123)"
	@echo "  - Prometheus: http://localhost:9090"
	@echo "  - MLflow: http://localhost:5000"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Create a user account: curl -X POST http://localhost:8080/api/auth/register -H 'Content-Type: application/json' -d '{\"email\": \"user@example.com\", \"password\": \"password\", \"full_name\": \"Test User\"}'"
	@echo "  2. Login: curl -X POST http://localhost:8080/api/auth/login -H 'Content-Type: application/json' -d '{\"email\": \"user@example.com\", \"password\": \"password\"}'"
	@echo "  3. Check the documentation: cat README.md"
	@echo ""
	@echo "For help: make help"
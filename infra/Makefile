# Alphintra Trading Platform Infrastructure Makefile
# Enhanced automation for multi-environment deployment and management

.PHONY: help install clean setup-* start-* stop-* logs-* status-* health-* test-* deploy-* backup-* restore-*

# ===============================
# CONFIGURATION
# ===============================

# Default environment
ENV ?= dev
VERSION ?= latest
DOCKER_REGISTRY ?= gcr.io/alphintra-trading-platform

# Color codes for output
RED := \033[31m
GREEN := \033[32m
YELLOW := \033[33m
BLUE := \033[34m
PURPLE := \033[35m
CYAN := \033[36m
WHITE := \033[37m
RESET := \033[0m

# ===============================
# HELP TARGET
# ===============================

help: ## Show this help message
	@echo "$(CYAN)Alphintra Trading Platform Infrastructure$(RESET)"
	@echo "$(BLUE)================================================$(RESET)"
	@echo ""
	@echo "$(GREEN)Environment Management:$(RESET)"
	@echo "  make setup-dev          - Set up development environment"
	@echo "  make setup-staging      - Set up staging environment" 
	@echo "  make setup-prod         - Set up production environment"
	@echo "  make start-dev          - Start development environment"
	@echo "  make start-staging      - Start staging environment"
	@echo "  make start-prod         - Start production environment"
	@echo "  make stop-ENV           - Stop environment (ENV=dev/staging/prod)"
	@echo ""
	@echo "$(GREEN)Infrastructure Operations:$(RESET)"
	@echo "  make install            - Install dependencies and tools"
	@echo "  make clean              - Clean Docker resources"
	@echo "  make reset-ENV          - Reset environment completely"
	@echo "  make status-ENV         - Show environment status"
	@echo "  make health-ENV         - Check environment health"
	@echo "  make logs-ENV           - Show environment logs"
	@echo ""
	@echo "$(GREEN)Kubernetes Operations:$(RESET)"
	@echo "  make k8s-setup          - Set up local Kubernetes cluster"
	@echo "  make k8s-secrets        - Set up Kubernetes secrets interactively"
	@echo "  make k8s-deploy         - Deploy to Kubernetes"
	@echo "  make k8s-destroy        - Destroy Kubernetes cluster"
	@echo "  make istio-install      - Install Istio service mesh"
	@echo ""
	@echo "$(GREEN)Cloud Operations:$(RESET)"
	@echo "  make gcp-setup          - Set up GCP resources with Terraform"
	@echo "  make gcp-deploy         - Deploy to GCP"
	@echo "  make gcp-destroy        - Destroy GCP resources"
	@echo ""
	@echo "$(GREEN)Development & Testing:$(RESET)"
	@echo "  make test-unit          - Run unit tests"
	@echo "  make test-integration   - Run integration tests"
	@echo "  make test-e2e           - Run end-to-end tests"
	@echo "  make lint               - Run code linting"
	@echo "  make format             - Format code"
	@echo ""
	@echo "$(GREEN)Data Operations:$(RESET)"
	@echo "  make backup-ENV         - Backup environment data"
	@echo "  make restore-ENV        - Restore environment data"
	@echo "  make migrate-ENV        - Run database migrations"
	@echo ""
	@echo "$(GREEN)Monitoring & Debugging:$(RESET)"
	@echo "  make monitor-ENV        - Open monitoring dashboards"
	@echo "  make debug-SERVICE      - Debug specific service"
	@echo "  make shell-SERVICE      - Open shell in service container"
	@echo ""
	@echo "$(YELLOW)Usage Examples:$(RESET)"
	@echo "  make start-dev                    # Start development environment"
	@echo "  make status-prod                  # Check production status"
	@echo "  make logs-staging SERVICE=trading-api  # View specific service logs"
	@echo "  make backup-prod                  # Backup production data"
	@echo ""

# ===============================
# INSTALLATION & SETUP
# ===============================

install: ## Install all required dependencies and tools
	@echo "$(BLUE)Installing Alphintra Infrastructure Dependencies...$(RESET)"
	@echo "$(YELLOW)Checking prerequisites...$(RESET)"
	@./scripts/check-prerequisites.sh
	@echo "$(YELLOW)Installing Docker dependencies...$(RESET)"
	@command -v docker >/dev/null 2>&1 || { echo "$(RED)Docker is required but not installed$(RESET)"; exit 1; }
	@command -v docker-compose >/dev/null 2>&1 || { echo "$(RED)Docker Compose is required but not installed$(RESET)"; exit 1; }
	@echo "$(YELLOW)Installing Kubernetes tools...$(RESET)"
	@# ./scripts/install-k8s-tools.sh # This script is not found, using manual setup for now
	@echo "$(YELLOW)Installing Terraform...$(RESET)"
	@./scripts/install-terraform.sh
	@echo "$(YELLOW)Installing development tools...$(RESET)"
	@./scripts/install-dev-tools.sh
	@echo "$(GREEN)✓ Installation completed successfully!$(RESET)"

setup-prerequisites: ## Install system prerequisites
	@echo "$(BLUE)Setting up system prerequisites...$(RESET)"
	@if [[ "$$(uname)" == "Darwin" ]]; then \
		echo "$(YELLOW)Setting up macOS prerequisites...$(RESET)"; \
		./scripts/setup-macos.sh; \
	elif [[ "$$(uname)" == "Linux" ]]; then \
		echo "$(YELLOW)Setting up Linux prerequisites...$(RESET)"; \
		./scripts/setup-linux.sh; \
	fi

# ===============================
# ENVIRONMENT MANAGEMENT
# ===============================

setup-dev: ## Set up development environment
	@echo "$(BLUE)Setting up Development Environment...$(RESET)"
	@cp infra/docker/.env.dev infra/docker/.env
	@$(MAKE) _setup-environment ENV=dev
	@echo "$(GREEN)✓ Development environment setup completed!$(RESET)"

setup-staging: ## Set up staging environment
	@echo "$(BLUE)Setting up Staging Environment...$(RESET)"
	@cp infra/docker/.env.staging infra/docker/.env 2>/dev/null || cp infra/docker/.env.example infra/docker/.env.staging
	@cp infra/docker/.env.staging infra/docker/.env
	@$(MAKE) _setup-environment ENV=staging
	@echo "$(GREEN)✓ Staging environment setup completed!$(RESET)"

setup-prod: ## Set up production environment
	@echo "$(BLUE)Setting up Production Environment...$(RESET)"
	@cp infra/docker/.env.prod infra/docker/.env 2>/dev/null || cp infra/docker/.env.example infra/docker/.env.prod
	@cp infra/docker/.env.prod infra/docker/.env
	@$(MAKE) _setup-environment ENV=prod
	@echo "$(GREEN)✓ Production environment setup completed!$(RESET)"

_setup-environment: ## Internal: Common environment setup
	@echo "$(YELLOW)Creating networks and volumes...$(RESET)"
	@cd infra/docker && docker network create alphintra-network 2>/dev/null || true
	@echo "$(YELLOW)Building base images...$(RESET)"
	@cd infra/docker && docker-compose -f docker-compose.base.yml build --parallel
	@echo "$(YELLOW)Setting up monitoring...$(RESET)"
	@./scripts/setup-monitoring.sh $(ENV)
	@echo "$(YELLOW)Initializing databases...$(RESET)"
	@./scripts/init-databases.sh $(ENV)

start-dev: ## Start development environment
	@echo "$(BLUE)Starting Development Environment...$(RESET)"
	@cd infra/docker && ENV=dev docker-compose \
		-f docker-compose.yml \
		-f docker-compose.dev.yml \
		--env-file .env.dev \
		up -d
	@$(MAKE) _post-start-actions ENV=dev
	@echo "$(GREEN)✓ Development environment started!$(RESET)"
	@$(MAKE) _show-endpoints ENV=dev

start-staging: ## Start staging environment
	@echo "$(BLUE)Starting Staging Environment...$(RESET)"
	@cd infra/docker && ENV=staging docker-compose \
		-f docker-compose.yml \
		-f docker-compose.staging.yml \
		--env-file .env.staging \
		up -d
	@$(MAKE) _post-start-actions ENV=staging
	@echo "$(GREEN)✓ Staging environment started!$(RESET)"
	@$(MAKE) _show-endpoints ENV=staging

start-prod: ## Start production environment
	@echo "$(BLUE)Starting Production Environment...$(RESET)"
	@cd infra/docker && ENV=prod docker-compose \
		-f docker-compose.yml \
		-f docker-compose.prod.yml \
		--env-file .env.prod \
		up -d
	@$(MAKE) _post-start-actions ENV=prod
	@echo "$(GREEN)✓ Production environment started!$(RESET)"
	@$(MAKE) _show-endpoints ENV=prod

_post-start-actions: ## Internal: Post-start actions
	@echo "$(YELLOW)Waiting for services to be ready...$(RESET)"
	@sleep 30
	@echo "$(YELLOW)Running post-start scripts...$(RESET)"
	@./scripts/post-start-setup.sh $(ENV)
	@echo "$(YELLOW)Creating initial data...$(RESET)"
	@./scripts/create-initial-data.sh $(ENV)

stop-%: ## Stop environment (dev/staging/prod)
	@echo "$(BLUE)Stopping $* Environment...$(RESET)"
	@cd infra/docker && ENV=$* docker-compose \
		-f docker-compose.yml \
		$(if $(filter dev,$*),-f docker-compose.dev.yml) \
		$(if $(filter staging,$*),-f docker-compose.staging.yml) \
		$(if $(filter prod,$*),-f docker-compose.prod.yml) \
		--env-file .env.$* \
		down
	@echo "$(GREEN)✓ $* environment stopped!$(RESET)"

restart-%: ## Restart environment
	@$(MAKE) stop-$*
	@$(MAKE) start-$*

# ===============================
# STATUS & MONITORING
# ===============================

status-%: ## Show environment status
	@echo "$(BLUE)Status of $* Environment:$(RESET)"
	@cd infra/docker && ENV=$* docker-compose \
		-f docker-compose.yml \
		$(if $(filter dev,$*),-f docker-compose.dev.yml) \
		$(if $(filter staging,$*),-f docker-compose.staging.yml) \
		$(if $(filter prod,$*),-f docker-compose.prod.yml) \
		--env-file .env.$* \
		ps

health-%: ## Check environment health
	@echo "$(BLUE)Health Check for $* Environment:$(RESET)"
	@./scripts/health-check.sh $*

logs-%: ## Show environment logs (optional SERVICE=service-name)
	@echo "$(BLUE)Logs for $* Environment:$(RESET)"
	@cd infra/docker && ENV=$* docker-compose \
		-f docker-compose.yml \
		$(if $(filter dev,$*),-f docker-compose.dev.yml) \
		$(if $(filter staging,$*),-f docker-compose.staging.yml) \
		$(if $(filter prod,$*),-f docker-compose.prod.yml) \
		--env-file .env.$* \
		logs -f $(SERVICE)

monitor-%: ## Open monitoring dashboards
	@echo "$(BLUE)Opening monitoring for $* environment...$(RESET)"
	@./scripts/open-monitoring.sh $*

_show-endpoints: ## Internal: Show service endpoints
	@echo ""
	@echo "$(CYAN)🚀 Environment Endpoints:$(RESET)"
	@echo "$(WHITE)────────────────────────────────────$(RESET)"
	@echo "$(GREEN)API Gateway:$(RESET)       http://localhost:8080"
	@echo "$(GREEN)Grafana:$(RESET)           http://localhost:3001 (admin/admin123)"
	@echo "$(GREEN)Prometheus:$(RESET)        http://localhost:9090"
	@echo "$(GREEN)MLflow:$(RESET)            http://localhost:5000"
	@echo "$(GREEN)Jaeger:$(RESET)            http://localhost:16686"
	@echo "$(GREEN)Kafka UI:$(RESET)          http://localhost:8084"
	@echo "$(GREEN)Redis Commander:$(RESET)   http://localhost:8085"
	@echo "$(GREEN)MinIO Console:$(RESET)     http://localhost:9001"
	@if [ "$(ENV)" = "dev" ]; then \
		echo "$(GREEN)MailHog:$(RESET)           http://localhost:8025"; \
		echo "$(GREEN)pgAdmin:$(RESET)           http://localhost:8086"; \
		echo "$(GREEN)Flink Dashboard:$(RESET)   http://localhost:8081"; \
	fi
	@echo ""

# ===============================
# KUBERNETES OPERATIONS
# ===============================

k8s-setup: ## Set up local Kubernetes cluster
	@echo "$(BLUE)Setting up local Kubernetes cluster...$(RESET)"
	@./scripts/setup-k8s-cluster.sh
	@echo "$(GREEN)✓ Local Kubernetes cluster setup completed!$(RESET)"

k8s-secrets: ## Set up Kubernetes secrets interactively
	@echo "$(BLUE)Setting up Kubernetes secrets...$(RESET)"
	@./scripts/setup-secrets.sh
	@echo "$(GREEN)✓ Kubernetes secrets setup completed!$(RESET)"

k8s-deploy: ## Deploy to Kubernetes
	@echo "$(BLUE)Deploying to Kubernetes...$(RESET)"
	@./scripts/k8s/deploy.sh $(ENV)
	@echo "$(GREEN)✓ Kubernetes deployment completed!$(RESET)"

k8s-destroy: ## Destroy Kubernetes cluster
	@echo "$(BLUE)Destroying Kubernetes cluster...$(RESET)"
	@../scripts/destroy-platform.sh
	@echo "$(GREEN)✓ Kubernetes cluster destroyed!$(RESET)"

k8s-stop-all: ## Scale all deployments in all namespaces to zero (stop all services)
	@echo "$(BLUE)Scaling all deployments in all namespaces to zero replicas...$(RESET)"
	@for ns in $(shell kubectl get ns --no-headers -o custom-columns=":metadata.name"); do \
	  kubectl scale deployment --all --replicas=0 -n $$ns; \
	done
	@echo "$(GREEN)✓ All deployments scaled to zero replicas!$(RESET)"

istio-install: ## Install Istio service mesh
	@echo "$(BLUE)Installing Istio service mesh...$(RESET)"
	@./scripts/install-istio.sh
	@echo "$(GREEN)✓ Istio installation completed!$(RESET)"

# ===============================
# CLOUD OPERATIONS
# ===============================

gcp-setup: ## Set up GCP infrastructure with Terraform
	@echo "$(BLUE)Setting up GCP infrastructure...$(RESET)"
	@cd infra/terraform && ./setup-gcp.sh $(ENV)
	@echo "$(GREEN)✓ GCP infrastructure setup completed!$(RESET)"

gcp-deploy: ## Deploy to GCP
	@echo "$(BLUE)Deploying to GCP...$(RESET)"
	@./scripts/gcp/deploy.sh $(ENV)
	@echo "$(GREEN)✓ GCP deployment completed!$(RESET)"

gcp-destroy: ## Destroy GCP infrastructure
	@echo "$(BLUE)Destroying GCP infrastructure...$(RESET)"
	@cd infra/terraform && terraform destroy -var-file="environments/$(ENV).tfvars"
	@echo "$(GREEN)✓ GCP infrastructure destroyed!$(RESET)"

# ===============================
# DEVELOPMENT & TESTING
# ===============================

test-unit: ## Run unit tests
	@echo "$(BLUE)Running unit tests...$(RESET)"
	@./scripts/test/run-unit-tests.sh

test-integration: ## Run integration tests
	@echo "$(BLUE)Running integration tests...$(RESET)"
	@./scripts/test/run-integration-tests.sh $(ENV)

test-e2e: ## Run end-to-end tests
	@echo "$(BLUE)Running end-to-end tests...$(RESET)"
	@./scripts/test/run-e2e-tests.sh $(ENV)

test-all: test-unit test-integration test-e2e ## Run all tests
	@echo "$(BLUE)Running code linting...$(RESET)"
	@./scripts/lint/run-linting.sh

format: ## Format code
	@echo "$(BLUE)Formatting code...$(RESET)"
	@./scripts/lint/format-code.sh

# ===============================
# DATA OPERATIONS
# ===============================

backup-%: ## Backup environment data
	@echo "$(BLUE)Creating backup for $* environment...$(RESET)"
	@./scripts/backup/create-backup.sh $*
	@echo "$(GREEN)✓ Backup completed!$(RESET)"

restore-%: ## Restore environment data
	@echo "$(BLUE)Restoring $* environment from backup...$(RESET)"
	@./scripts/backup/restore-backup.sh $*
	@echo "$(GREEN)✓ Restore completed!$(RESET)"

migrate-%: ## Run database migrations
	@echo "$(BLUE)Running database migrations for $* environment...$(RESET)"
	@./scripts/database/run-migrations.sh $*
	@echo "$(GREEN)✓ Migrations completed!$(RESET)"

# ===============================
# DEBUGGING & UTILITIES
# ===============================

shell-%: ## Open shell in service container (e.g., make shell-trading-api)
	@echo "$(BLUE)Opening shell in $* container...$(RESET)"
	@cd infra/docker && docker-compose exec $* /bin/bash

debug-%: ## Debug specific service with logs and metrics
	@echo "$(BLUE)Debugging $* service...$(RESET)"
	@./scripts/debug/debug-service.sh $*

clean: ## Clean Docker resources
	@echo "$(BLUE)Cleaning Docker resources...$(RESET)"
	@cd infra/docker && docker-compose down -v --remove-orphans 2>/dev/null || true
	@docker system prune -f
	@docker volume prune -f
	@echo "$(GREEN)✓ Cleanup completed!$(RESET)"

reset-%: ## Reset environment completely
	@echo "$(RED)WARNING: This will delete all data for $* environment!$(RESET)"
	@echo "$(YELLOW)Press Ctrl+C to cancel, or wait 10 seconds to continue...$(RESET)"
	@sleep 10
	@$(MAKE) stop-$*
	@cd infra/docker && docker-compose \
		-f docker-compose.yml \
		$(if $(filter dev,$*),-f docker-compose.dev.yml) \
		$(if $(filter staging,$*),-f docker-compose.staging.yml) \
		$(if $(filter prod,$*),-f docker-compose.prod.yml) \
		--env-file .env.$* \
		down -v --remove-orphans
	@docker system prune -af
	@echo "$(GREEN)✓ $* environment reset completed!$(RESET)"

# ===============================
# CI/CD OPERATIONS
# ===============================

build-images: ## Build all Docker images
	@echo "$(BLUE)Building all Docker images...$(RESET)"
	@../scripts/build/build-all-images.sh $(VERSION)
	@echo "$(GREEN)✓ Image building completed!$(RESET)"

push-images: ## Push images to registry
	@echo "$(BLUE)Pushing images to registry...$(RESET)"
	@./scripts/build/push-images.sh $(VERSION) $(DOCKER_REGISTRY)
	@echo "$(GREEN)✓ Images pushed successfully!$(RESET)"

release: ## Create a release
	@echo "$(BLUE)Creating release $(VERSION)...$(RESET)"
	@./scripts/release/create-release.sh $(VERSION)
	@echo "$(GREEN)✓ Release $(VERSION) created!$(RESET)"

# ===============================
# QUICK OPERATIONS
# ===============================

quick-start: setup-dev start-dev ## Quick start development environment
	@echo "$(GREEN)🚀 Alphintra development environment is ready!$(RESET)"

quick-demo: ## Quick demo setup with sample data
	@$(MAKE) quick-start
	@./scripts/demo/setup-demo-data.sh
	@echo "$(GREEN)🎭 Demo environment ready with sample data!$(RESET)"

# ===============================
# UTILITY FUNCTIONS
# ===============================

check-env: ## Check environment variables
	@./scripts/utils/check-env.sh $(ENV)

generate-docs: ## Generate infrastructure documentation
	@echo "$(BLUE)Generating infrastructure documentation...$(RESET)"
	@./scripts/docs/generate-docs.sh
	@echo "$(GREEN)✓ Documentation generated!$(RESET)"

validate-config: ## Validate configuration files
	@echo "$(BLUE)Validating configuration files...$(RESET)"
	@./scripts/validate/validate-config.sh $(ENV)
	@echo "$(GREEN)✓ Configuration validation completed!$(RESET)"

# ===============================
# HELP EXTRACTION
# ===============================

%: ## Catch-all target to show help for unknown commands
	@echo "$(RED)Unknown command: $@$(RESET)"
	@echo "$(YELLOW)Run 'make help' to see available commands$(RESET)"
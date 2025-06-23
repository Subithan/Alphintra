# Alphintra Trading Platform - Master Deployment System
# Single command to deploy the entire architecture

.PHONY: help deploy-all quick-deploy status destroy-all

# Default target
.DEFAULT_GOAL := help

# Configuration
PROJECT_NAME := alphintra
ENVIRONMENT ?= prod
REGION ?= us-central1

# Colors for beautiful output
RED := \033[31m
GREEN := \033[32m
YELLOW := \033[33m
BLUE := \033[34m
MAGENTA := \033[35m
CYAN := \033[36m
RESET := \033[0m

help: ## Show available commands
	@echo "$(CYAN)========================================$(RESET)"
	@echo "$(CYAN)  Alphintra Trading Platform$(RESET)"
	@echo "$(CYAN)  Complete Architecture Deployment$(RESET)"
	@echo "$(CYAN)========================================$(RESET)"
	@echo ""
	@echo "$(GREEN)🚀 Quick Start Commands:$(RESET)"
	@echo ""
	@echo "$(YELLOW)  make deploy-all$(RESET)      Deploy entire platform to cloud (30-45 min)"
	@echo "$(YELLOW)  make quick-deploy$(RESET)    Deploy locally with Docker (5 min)"
	@echo "$(YELLOW)  make status$(RESET)          Check platform health and status"
	@echo "$(YELLOW)  make destroy-all$(RESET)     Destroy entire platform"
	@echo ""
	@echo "$(GREEN)Environment Variables:$(RESET)"
	@echo "  ENVIRONMENT=$(ENVIRONMENT) (dev/staging/prod)"
	@echo "  REGION=$(REGION)"
	@echo ""

deploy-all: ## 🚀 Deploy complete Alphintra platform to cloud
	@echo "$(MAGENTA)================================================$(RESET)"
	@echo "$(MAGENTA)  🚀 ALPHINTRA FULL PLATFORM DEPLOYMENT$(RESET)"
	@echo "$(MAGENTA)================================================$(RESET)"
	@echo ""
	@echo "$(YELLOW)Target Environment: $(ENVIRONMENT)$(RESET)"
	@echo "$(YELLOW)Target Region: $(REGION)$(RESET)"
	@echo "$(YELLOW)Estimated Duration: 30-45 minutes$(RESET)"
	@echo ""
	@echo "$(BLUE)This will deploy:$(RESET)"
	@echo "  ✓ Cloud Infrastructure (GCP/AWS/Azure)"
	@echo "  ✓ Kubernetes Clusters (Multi-region)"
	@echo "  ✓ Core Trading Engine"
	@echo "  ✓ Market Data Services"
	@echo "  ✓ Risk Management Engine"
	@echo "  ✓ AI/ML Services (LLM, Quantum, Federated Learning)"
	@echo "  ✓ Global Services (FX Hedging, Compliance, Regional)"
	@echo "  ✓ Monitoring & Observability Stack"
	@echo "  ✓ Security & Compliance Framework"
	@echo ""
	@read -p "Continue with deployment? [y/N] " -n 1 -r; \
	echo ""; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		./scripts/deploy-full-platform.sh $(ENVIRONMENT) $(REGION); \
	else \
		echo "$(YELLOW)Deployment cancelled$(RESET)"; \
	fi

quick-deploy: ## 🏃 Quick local deployment for development
	@echo "$(CYAN)========================================$(RESET)"
	@echo "$(CYAN)  ⚡ Quick Local Deployment$(RESET)"
	@echo "$(CYAN)========================================$(RESET)"
	@echo ""
	@echo "$(BLUE)Deploying Alphintra locally with Docker Compose...$(RESET)"
	@./scripts/deploy-local.sh
	@echo ""
	@echo "$(GREEN)✅ Local deployment complete!$(RESET)"
	@echo ""
	@echo "$(GREEN)🌐 Access URLs:$(RESET)"
	@echo "  📊 Trading Dashboard: http://localhost:3000"
	@echo "  🔌 API Gateway:       http://localhost:8080"
	@echo "  📈 Monitoring:        http://localhost:3001"
	@echo "  📋 Documentation:     http://localhost:8000"

status: ## Check platform status and health
	@echo "$(BLUE)Checking Alphintra platform status...$(RESET)"
	@./scripts/check-status.sh $(ENVIRONMENT)

destroy-all: ## ⚠️ Destroy entire platform (DESTRUCTIVE)
	@echo "$(RED)================================================$(RESET)"
	@echo "$(RED)  ⚠️  DESTRUCTIVE OPERATION WARNING$(RESET)"
	@echo "$(RED)================================================$(RESET)"
	@echo ""
	@echo "$(RED)This will PERMANENTLY DESTROY:$(RESET)"
	@echo "  🗑️  All cloud infrastructure"
	@echo "  🗑️  All databases and data"
	@echo "  🗑️  All Kubernetes clusters"
	@echo "  🗑️  All monitoring and logs"
	@echo ""
	@echo "$(RED)THIS CANNOT BE UNDONE!$(RESET)"
	@echo ""
	@read -p "Type 'DESTROY' to confirm: " confirmation; \
	if [[ "$$confirmation" == "DESTROY" ]]; then \
		echo "$(RED)Destroying platform...$(RESET)"; \
		./scripts/destroy-platform.sh $(ENVIRONMENT); \
	else \
		echo "$(YELLOW)Operation cancelled$(RESET)"; \
	fi
# Makefile for Alphintra Cloud Build deployments
# Usage: make auth-service or make no-code-service or make service-gateway or make frontend

.PHONY: help no-code-service auth-service service-gateway frontend all

# Get the current commit SHA
COMMIT_SHA := $(shell git rev-parse HEAD)
PROJECT_ID := alphintra-472817

# Default target
help:
	@echo "Alphintra Cloud Build Makefile"
	@echo ""
	@echo "Usage: make [service]"
	@echo ""
	@echo "Available services:"
	@echo "  no-code-service  - Build and deploy no-code-service"
	@echo "  auth-service     - Build and deploy auth-service"
	@echo "  service-gateway  - Build and deploy service-gateway"
	@echo "  frontend         - Build and deploy frontend"
	@echo "  all              - Build and deploy all services"
	@echo ""
	@echo "Example: make auth-service"

# Build and deploy no-code-service
no-code-service:
	@echo "========================================="
	@echo "Building and deploying no-code-service..."
	@echo "========================================="
	gcloud builds submit \
		--config src/backend/no-code-service/cloudbuild.yaml \
		--substitutions=_COMMIT_SHA=$(COMMIT_SHA) \
		--project $(PROJECT_ID)
	@echo "✅ no-code-service deployed successfully!"

# Build and deploy auth-service
auth-service:
	@echo "========================================="
	@echo "Building and deploying auth-service..."
	@echo "========================================="
	gcloud builds submit \
		--config src/backend/auth-service/cloudbuild.yaml \
		--substitutions=_COMMIT_SHA=$(COMMIT_SHA),_SERVICE_NAME=auth-service \
		--project $(PROJECT_ID)
	@echo "✅ auth-service deployed successfully!"

# Build and deploy service-gateway
service-gateway:
	@echo "========================================="
	@echo "Building and deploying service-gateway..."
	@echo "========================================="
	gcloud builds submit \
		--config src/backend/service-gateway/cloudbuild.yaml \
		--substitutions=_COMMIT_SHA=$(COMMIT_SHA),_SERVICE_NAME=service-gateway \
		--project $(PROJECT_ID)
	@echo "✅ service-gateway deployed successfully!"

# Build and deploy frontend
frontend:
	@echo "========================================="
	@echo "Building and deploying frontend..."
	@echo "========================================="
	gcloud builds submit \
		--config src/frontend/cloudbuild.yaml \
		--substitutions=_BUILD_TAG=$(COMMIT_SHA) \
		--project $(PROJECT_ID)
	@echo "✅ Frontend deployed successfully!"

# Build and deploy all services
all: no-code-service auth-service service-gateway frontend
	@echo ""
	@echo "========================================="
	@echo "All services deployed successfully!"
	@echo "========================================="
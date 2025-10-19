# TODO: Add Marketplace Service to Docker Compose

## Tasks
- [x] Create Dockerfile in src/backend/marketplace/ based on FastAPI pattern
- [x] Add /health endpoint to src/backend/marketplace/dev/main.py
- [x] Add marketplace service to infra/docker/dev/docker-compose.minimal.yml with proper configuration

## Details
- Marketplace service: FastAPI-based Stripe marketplace API
- Port: 8012
- Database: alphintra-marketplace
- Dependencies: postgres, redis
- Environment variables: DATABASE_URL, STRIPE_SECRET_KEY, STRIPE_PUBLISHABLE_KEY, STRIPE_WEBHOOK_SECRET, DOMAIN_URL
- Healthcheck: curl /health

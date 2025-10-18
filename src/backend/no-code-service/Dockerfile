# Production Dockerfile for No-Code Service
# Simple single-stage build to ensure proper dependency installation

FROM python:3.11-slim

# Set arguments for build-time customization
ARG APP_UID=1001
ARG APP_GID=1001

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create application user
RUN groupadd -g ${APP_GID} appgroup && \
    useradd -m -u ${APP_UID} -g ${APP_GID} appuser

# Create application directories
RUN mkdir -p /app /app/logs /app/uploads /app/models /app/temp && \
    chown -R appuser:appgroup /app

# Set working directory
WORKDIR /app

# Copy requirements first for better layer caching
COPY --chown=appuser:appgroup requirements.txt .

# Upgrade pip and install dependencies
RUN pip install --upgrade pip

# Install pg8000 first and explicitly
RUN pip install --no-cache-dir pg8000==1.30.5

# Verify pg8000 installation immediately
RUN python -c "import pg8000; print('✅ pg8000 installed successfully - version:', pg8000.__version__)"

# Install all other dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Verify all critical imports
RUN python -c "import fastapi, sqlalchemy, alembic, pydantic, redis, strawberry, pg8000; print('✅ All critical dependencies imported successfully')"

# Copy application code
COPY --chown=appuser:appgroup . .

# Set environment variables for production
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PORT=8006
ENV HOST=0.0.0.0

# Set a placeholder DATABASE_URL for build time (will be overridden at runtime)
ENV DATABASE_URL="postgresql://user:password@localhost:5432/build_db"

# Switch to non-root user
USER appuser

# Verify the application can import its modules
RUN python -c "from app.core.config import get_settings; from app.core.db import _create_engine; print('✅ Application modules imported successfully')"

# Reset DATABASE_URL to empty (will be set by runtime environment)
ENV DATABASE_URL=""

# Default production configuration
ENV DEV_MODE=false
ENV LOG_LEVEL=INFO
ENV CLOUD_SQL_CONNECTION_NAME=""
ENV REDIS_URL="redis://localhost:6379/0"
ENV AUTH_SERVICE_URL="http://auth-service.alphintra.svc.cluster.local:8009"
ENV AIML_SERVICE_URL="http://ai-ml-strategy-service.alphintra.svc.cluster.local:8002"

# Expose port
EXPOSE 8006

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8006/health || exit 1

# Copy the entrypoint script and make it executable
COPY --chown=appuser:appgroup entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Run the application
ENTRYPOINT ["/app/entrypoint.sh"]
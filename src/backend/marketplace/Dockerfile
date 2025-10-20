# Optimized multi-stage Dockerfile for the Marketplace service
# Provides fast builds, dependency caching and a hardened runtime image

# -----------------------------------------------------------------------------
# Builder stage: install Python dependencies into a relocatable prefix
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install build dependencies required for compiling psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Copy dependency manifest first to maximize Docker layer caching
COPY requirements.txt ./

# Install dependencies into /install so they can be copied to the runtime image
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --prefix /install -r requirements.txt

# Copy the rest of the application source (kept separate from dependency layer)
COPY . /src

# -----------------------------------------------------------------------------
# Runtime stage: minimal image with only runtime dependencies and application
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_HOME=/app \
    PORT=8200 \
    HOST=0.0.0.0

# Install lightweight system dependencies used at runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a dedicated non-root user
RUN groupadd -r marketplace && useradd -r -g marketplace marketplace

WORKDIR ${APP_HOME}

# Copy installed Python dependencies from the builder image
COPY --from=builder /install /usr/local

# Copy application source code
COPY --from=builder /src ${APP_HOME}

# Ensure runtime directories exist and are writable by the app user
RUN mkdir -p ${APP_HOME}/logs ${APP_HOME}/tmp && \
    chown -R marketplace:marketplace ${APP_HOME}

USER marketplace

# Expose the FastAPI port
EXPOSE ${PORT}

# Simple health check to surface failures quickly
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://${HOST:-0.0.0.0}:${PORT:-8200}/health || exit 1

# Default command – can be overridden by Cloud Run / Kubernetes args
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8200"]

# Multi-stage build for AI/ML Strategy Service
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=1000

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    gcc \
    g++ \
    gfortran \
    libopenblas-dev \
    liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set work directory
WORKDIR /app

# Upgrade pip and install wheel for better package installation
RUN pip install --upgrade pip setuptools wheel

# Copy requirements and install dependencies in stages to better handle timeouts
COPY requirements.txt .

# Install core dependencies first (these are less likely to timeout)
RUN pip install --timeout=1000 --retries=5 fastapi==0.104.1 uvicorn[standard]==0.24.0 pydantic==2.5.0

# Install database dependencies
RUN pip install --timeout=1000 --retries=5 sqlalchemy==2.0.23 asyncpg==0.29.0 alembic==1.13.1 psycopg2-binary==2.9.9

# Install caching and messaging dependencies
RUN pip install --timeout=1000 --retries=5 redis==5.0.1 aioredis==2.0.1 aiokafka==0.9.0

# Install ML dependencies (these are the most likely to timeout, so install them separately with more retries)
RUN pip install --timeout=1000 --retries=10 numpy==1.26.4
RUN pip install --timeout=1000 --retries=10 pandas==2.0.3
RUN pip install --timeout=1000 --retries=10 scikit-learn==1.3.0
RUN pip install --timeout=1000 --retries=10 mlflow==2.8.1

# Install remaining dependencies
RUN pip install --timeout=1000 --retries=5 -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/data && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]

# Development stage
FROM base as development

USER root

# Install development dependencies
RUN pip install --no-cache-dir \
    pytest \
    pytest-asyncio \
    pytest-cov \
    black \
    isort \
    flake8 \
    mypy

USER appuser

# Override CMD for development
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002", "--reload"]

# Production stage
FROM base as production

# Copy only necessary files for production
COPY --from=base /app /app

# Ensure proper permissions
USER root
RUN chown -R appuser:appuser /app
USER appuser

# Production command
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002", "--workers", "4"]
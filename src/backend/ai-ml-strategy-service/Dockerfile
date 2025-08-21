# Multi-stage build for AI/ML Strategy Service
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

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
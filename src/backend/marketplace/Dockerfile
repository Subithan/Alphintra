# Stage 1: Build & Base Image (Named 'base')
# This stage installs all dependencies and creates the non-root user.
# ----------------------------------------------------------------------
FROM python:3.11-slim as base

# Set environment variables to optimize Python/Pip behavior
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=1000

# Install system dependencies needed for Python packages (like 'psycopg2-binary')
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create the non-root user and group for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set work directory
WORKDIR /app

# Upgrade pip and install wheel for better package installation
RUN pip install --upgrade pip setuptools wheel

# --- Dependency Installation ---
# Install all dependencies using a single requirements file for better caching/simplicity.
COPY requirements.txt ./
RUN pip install --timeout=1000 --retries=5 -r requirements.txt

# Copy application code (copies contents of the current directory into /app)
COPY . /app/

# Create necessary directories and ensure non-root user owns them
RUN mkdir -p /app/logs && chown -R appuser:appuser /app

# Switch to non-root user for security
USER appuser

# Expose port (Documentation only, does not publish the port)
EXPOSE 8012

# Health check (Ensures container restarts if the app is unhealthy)
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8012/health || exit 1

# Define the command to run the application
# FIX: Changed 'marketplace.main:app' to 'main:app' because the files are copied directly into the /app WORKDIR.
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8012"]

# ----------------------------------------------------------------------
# Stage 2: Development
# Adds development tools and enables auto-reload.
# ----------------------------------------------------------------------
FROM base as development

# Temporarily switch to root to install system-wide development tools
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

# Switch back to the non-root user
USER appuser

# Override CMD for development to enable hot-reload
# FIX: Changed 'marketplace.main:app' to 'main:app'
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8012", "--reload"]

# ----------------------------------------------------------------------
# Stage 3: Production (Optimized Runtime)
# ----------------------------------------------------------------------
FROM base as production

# Ensure the worker command is used for production
# FIX: Changed 'marketplace.main:app' to 'main:app'
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8012", "--workers", "4"]

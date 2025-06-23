FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    build-essential \
    make \
    wget \
    autotools-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Note: Removed TA-Lib C library installation as we're using alternative packages

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .

# Create logs directory
RUN mkdir -p /var/log/alphintra

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app /var/log/alphintra
USER appuser

# Expose port
EXPOSE 8003

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8003/health || exit 1

# Run the application
CMD ["python", "main.py"]
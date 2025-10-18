# Multi-stage Dockerfile for ai-ml-strategy-service

FROM python:3.11-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Prepare runtime directories and permissions (UID/GID 1001)
RUN mkdir -p /app/data && \
    addgroup --system --gid 1001 app && \
    adduser --system --uid 1001 --ingroup app appuser && \
    chown -R 1001:1001 /app

COPY . .
USER 1001:1001

EXPOSE 8002

ENV PORT=8002

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]

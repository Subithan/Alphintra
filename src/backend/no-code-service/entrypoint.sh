#!/bin/bash
set -e

echo "🚀 Starting No-Code Service..."
echo "Configuration:"
echo "- PORT: ${PORT:-8006}"
echo "- HOST: ${HOST:-0.0.0.0}"
echo "- DEV_MODE: ${DEV_MODE:-false}"
echo "- LOG_LEVEL: ${LOG_LEVEL:-INFO}"
echo "- DATABASE_URL: ${DATABASE_URL:+SET}"
echo "- CLOUD_SQL_CONNECTION_NAME: ${CLOUD_SQL_CONNECTION_NAME:+SET}"

# Validate database connection if DATABASE_URL is set
if [[ "${DATABASE_URL}" != "" ]]; then
    echo "🔍 Validating database connection..."
    python validate_db_connection.py || {
        echo "❌ Database connection validation failed!"
        echo "   Please check the database configuration and Cloud SQL settings."
        echo "   Continuing with startup (may fail later)..."
    }
fi

# Initialize database if needed
if [[ "${DATABASE_URL}" != "" && "${SKIP_DB_INIT}" != "true" ]]; then
    echo "🔧 Initializing database..."
    python init_database.py || echo "⚠️  Database initialization failed or already completed"
fi

# Normalize log level for uvicorn
LOG_LEVEL_LOWER=$(echo "${LOG_LEVEL:-info}" | tr '[:upper:]' '[:lower:]')

# Start the application
echo "🌟 Starting FastAPI application..."
exec uvicorn main:app --host ${HOST:-0.0.0.0} --port ${PORT:-8006} --workers 1 --log-level "${LOG_LEVEL_LOWER}"

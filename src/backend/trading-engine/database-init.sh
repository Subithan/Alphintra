#!/bin/sh
# Database initialization script for Trading Engine
# This script checks if tables exist and creates them if needed

set -e

# Function to check if table exists
check_table_exists() {
    psql "$DATABASE_URL" -tAc "SELECT 1 FROM information_schema.tables WHERE table_name = '$1' AND table_schema = 'public'" | grep -q 1 || return 1
}

# Function to run database initialization
init_database() {
    echo "🗄️ Initializing Trading Engine database..."

    # Check if connection is available
    if ! psql "$DATABASE_URL" -c "SELECT 1;" > /dev/null 2>&1; then
        echo "❌ Database connection failed - skipping initialization"
        return 1
    fi

    # Check if tables already exist
    if check_table_exists "trading_bots" && check_table_exists "trade_orders" && check_table_exists "positions"; then
        echo "✅ Database tables already exist - skipping initialization"
        return 0
    fi

    echo "📋 Creating database tables from init_database.sql..."

    # Run the database initialization script
    if psql "$DATABASE_URL" -f /app/init_database.sql; then
        echo "✅ Database initialization completed successfully"

        # Verify tables were created
        echo "📊 Created tables:"
        psql "$DATABASE_URL" -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;"

        return 0
    else
        echo "❌ Database initialization failed"
        return 1
    fi
}

# Main execution
echo "🚀 Trading Engine Database Initialization Script"

if [ "$SKIP_DB_INIT" = "true" ]; then
    echo "⏭️ Skipping database initialization (SKIP_DB_INIT=true)"
else
    # Wait for database to be available (max 30 seconds)
    echo "⏳ Waiting for database to be available..."
    for i in 1 2 3 4 5 6; do
        if psql "$DATABASE_URL" -c "SELECT 1;" > /dev/null 2>&1; then
            echo "✅ Database is available"
            break
        fi
        echo "⏳ Database not ready, waiting 5 seconds... ($i/6)"
        sleep 5
    done

    # Initialize database
    if init_database; then
        echo "🎉 Database setup completed"
    else
        echo "⚠️ Database initialization failed, but continuing with application startup"
    fi
fi

echo "🚀 Starting Trading Engine application..."
exec "$@"
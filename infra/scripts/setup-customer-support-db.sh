#!/bin/bash

# Customer Support Service Database Setup Script for Cloud SQL
# Creates database and user for the customer support service

set -e

# Configuration
PROJECT_ID="alphintra-472817"
REGION="us-central1"
INSTANCE_NAME="alphintra-db-instance"
DATABASE_NAME="alphintra_customer_support"
DB_USER="customer_support"
DB_PASSWORD="alphintra@123"

echo "🚀 Setting up Customer Support Service database in Cloud SQL..."

# Check if gcloud is installed and authenticated
if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: gcloud CLI is not installed or not in PATH"
    exit 1
fi

# Get current project
CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null)
if [[ "$CURRENT_PROJECT" != "$PROJECT_ID" ]]; then
    echo "📝 Switching to project: $PROJECT_ID"
    gcloud config set project "$PROJECT_ID"
fi

echo "🔍 Checking Cloud SQL instance availability..."

# Check if Cloud SQL instance exists
if ! gcloud sql instances describe "$INSTANCE_NAME" --format="value(state)" &> /dev/null; then
    echo "❌ Error: Cloud SQL instance '$INSTANCE_NAME' not found"
    echo "   Please ensure the instance exists and is accessible"
    exit 1
fi

INSTANCE_STATE=$(gcloud sql instances describe "$INSTANCE_NAME" --format="value(state)")
echo "✅ Cloud SQL instance '$INSTANCE_NAME' is $INSTANCE_STATE"

echo "🗄️ Creating database: $DATABASE_NAME"

# Create the database if it doesn't exist
if gcloud sql databases list --instance="$INSTANCE_NAME" --filter="name:$DATABASE_NAME" --format="value(name)" | grep -q "$DATABASE_NAME"; then
    echo "✅ Database '$DATABASE_NAME' already exists"
else
    gcloud sql databases create "$DATABASE_NAME" --instance="$INSTANCE_NAME"
    echo "✅ Database '$DATABASE_NAME' created successfully"
fi

echo "👤 Creating database user: $DB_USER"

# Create the user if it doesn't exist
if gcloud sql users list --instance="$INSTANCE_NAME" --filter="name:$DB_USER" --format="value(name)" | grep -q "$DB_USER"; then
    echo "✅ User '$DB_USER' already exists"
    echo "🔄 Updating user password..."
    gcloud sql users set-password "$DB_USER" --host "%" --instance="$INSTANCE_NAME" --password="$DB_PASSWORD"
else
    gcloud sql users create "$DB_USER" --host "%" --instance="$INSTANCE_NAME" --password="$DB_PASSWORD"
    echo "✅ User '$DB_USER' created successfully"
fi

echo "🔐 Granting permissions to database user..."

# Grant necessary permissions to the user
gcloud sql connect "$INSTANCE_NAME" --user=postgres << EOF
-- Connect to the customer support service database
\c $DATABASE_NAME;

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE $DATABASE_NAME TO $DB_USER;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $DB_USER;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $DB_USER;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO $DB_USER;

-- Set default permissions for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $DB_USER;

-- Exit
\q
EOF

echo "📋 Database configuration summary:"
echo "  Project: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Instance: $INSTANCE_NAME"
echo "  Database: $DATABASE_NAME"
echo "  User: $DB_USER"
echo "  Password: [REDACTED]"
echo ""

echo "🧪 Testing database connection..."

# Test the database connection
gcloud sql connect "$INSTANCE_NAME" --user="$DB_USER" --database="$DATABASE_NAME" << EOF
-- Test basic connection
SELECT current_database(), current_user;

-- Show existing tables (should be empty initially)
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

-- Exit
\q
EOF

echo "✅ Database connection test successful!"

echo ""
echo "🎉 Customer Support Service database setup completed!"
echo ""
echo "📊 Connection Information:"
echo "  Database: $DATABASE_NAME"
echo "  User: $DB_USER"
echo "  Connection String: jdbc:postgresql://$INSTANCE_NAME:$REGION:$PROJECT_ID/$DATABASE_NAME"
echo "  Python Connection: postgresql://$DB_USER:[PASSWORD]@127.0.0.1:5432/$DATABASE_NAME"
echo ""
echo "🚀 Next steps:"
echo "  1. Update customer support service application configuration with database credentials"
echo "  2. Run the customer support service build (it will auto-initialize tables)"
echo "  3. Verify table creation after first startup"
echo ""
echo "💡 Note: The customer support service will automatically create tables on first startup"
echo "   using Flyway migrations included in the Docker image."
echo "   Tables to be created: support_tickets, support_messages, knowledge_base_articles, etc."
echo ""

# Display current databases and users for verification
echo "📋 Current databases in instance:"
gcloud sql databases list --instance="$INSTANCE_NAME" --format="table(name,instance,createTime)"

echo ""
echo "👥 Current database users:"
gcloud sql users list --instance="$INSTANCE_NAME" --format="table(name,host,type,state)"
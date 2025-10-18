#!/usr/bin/env python3
"""
Database connection validation script for Cloud SQL deployment.
This script helps diagnose database connectivity issues.
"""

import os
import sys
import logging
from urllib.parse import urlparse
import time

def check_environment_variables():
    """Check if required environment variables are set."""
    print("🔍 Checking environment variables...")

    required_vars = ['DATABASE_URL', 'CLOUD_SQL_CONNECTION_NAME']
    optional_vars = ['DEV_MODE']

    missing_required = []

    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {'*' * len(value.split('@')[0])}@{value.split('@')[1] if '@' in value else 'SET'}")
        else:
            print(f"❌ {var}: NOT SET")
            missing_required.append(var)

    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"⚠️  {var}: NOT SET (optional)")

    if missing_required:
        print(f"\n❌ Missing required environment variables: {', '.join(missing_required)}")
        return False

    return True

def validate_database_url():
    """Validate the DATABASE_URL format."""
    print("\n🔗 Validating DATABASE_URL format...")

    database_url = os.getenv('DATABASE_URL', '')

    if not database_url:
        print("❌ DATABASE_URL is not set")
        return False

    try:
        parsed = urlparse(database_url)
        print(f"   Scheme: {parsed.scheme}")
        print(f"   Username: {'SET' if parsed.username else 'NOT SET'}")
        print(f"   Hostname: {parsed.hostname or 'NOT SET'}")
        print(f"   Port: {parsed.port or 'DEFAULT'}")
        print(f"   Database: {parsed.path.lstrip('/') or 'NOT SET'}")

        # Check for pg8000 driver
        if 'pg8000' in parsed.scheme:
            print("✅ Using pg8000 driver")
        elif 'postgresql' in parsed.scheme:
            print("⚠️  Using postgresql driver (should be postgresql+pg8000)")
        else:
            print(f"⚠️  Unknown driver: {parsed.scheme}")

        return True

    except Exception as e:
        print(f"❌ Invalid DATABASE_URL format: {e}")
        return False

def test_database_connection():
    """Test the database connection with retry logic."""
    print("\n🧪 Testing database connection...")

    try:
        # Import SQLAlchemy components
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import sessionmaker

        database_url = os.getenv('DATABASE_URL', '')

        if not database_url:
            print("❌ Cannot test connection: DATABASE_URL not set")
            return False

        print(f"   Connecting to: {database_url.split('@')[0] + '@' + database_url.split('@')[1] if '@' in database_url else database_url}")

        # Create engine with connection settings for Cloud SQL
        engine = create_engine(
            database_url,
            pool_pre_ping=True,
            pool_recycle=300,
            connect_args={
                "connect_timeout": 10,
                "application_name": "no-code-service-connection-test"
            }
        )

        # Test connection with retry
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"   Attempt {attempt + 1}/{max_retries}...")

                with engine.connect() as conn:
                    result = conn.execute(text("SELECT 1 as test_value"))
                    row = result.fetchone()
                    if row and row[0] == 1:
                        print("✅ Database connection successful!")
                        return True
                    else:
                        print("❌ Database query returned unexpected result")

            except Exception as conn_error:
                print(f"   Attempt {attempt + 1} failed: {str(conn_error)}")
                if attempt < max_retries - 1:
                    print(f"   Waiting {2 ** attempt} seconds before retry...")
                    time.sleep(2 ** attempt)
                else:
                    print(f"❌ All {max_retries} connection attempts failed")
                    print(f"   Last error: {str(conn_error)}")
                    return False

    except ImportError as import_error:
        print(f"❌ Failed to import database libraries: {import_error}")
        print("   Make sure pg8000 and sqlalchemy are installed")
        return False
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        return False

def check_pg8000_installation():
    """Check if pg8000 is properly installed."""
    print("\n📦 Checking pg8000 installation...")

    try:
        import pg8000
        print(f"✅ pg8000 version: {pg8000.__version__}")

        # Test basic import functionality
        print("   Testing pg8000 basic functionality...")
        connection = pg8000.connect(
            user="test",
            password="test",
            host="localhost",
            database="test",
            port=5432,
            timeout=1
        )
        print("✅ pg8000 basic functionality test passed (expected timeout error)")

    except ImportError:
        print("❌ pg8000 is not installed")
        return False
    except Exception as e:
        # Expected to fail with connection error, but that's okay
        if "timeout" in str(e).lower() or "connection" in str(e).lower():
            print("✅ pg8000 is working (expected connection error)")
        else:
            print(f"⚠️  pg8000 test returned unexpected error: {e}")

    return True

def main():
    """Main validation function."""
    print("🚀 No-Code Service Database Connection Validation")
    print("=" * 50)

    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    logger = logging.getLogger(__name__)

    all_checks_passed = True

    # Run all validation checks
    checks = [
        ("Environment Variables", check_environment_variables),
        ("pg8000 Installation", check_pg8000_installation),
        ("DATABASE_URL Format", validate_database_url),
    ]

    for check_name, check_func in checks:
        try:
            if not check_func():
                all_checks_passed = False
                print(f"\n❌ {check_name} check failed")
            else:
                print(f"✅ {check_name} check passed")
        except Exception as e:
            print(f"\n❌ {check_name} check failed with exception: {e}")
            all_checks_passed = False

    # Only test database connection if other checks pass
    if all_checks_passed:
        print("\n" + "=" * 50)
        if test_database_connection():
            print("\n🎉 All database connection checks passed!")
            print("   The service should be able to start successfully.")
            return 0
        else:
            print("\n❌ Database connection test failed.")
            print("   Please check the above error messages and fix the configuration.")
            return 1
    else:
        print("\n❌ Some pre-checks failed. Please fix them before testing the database connection.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
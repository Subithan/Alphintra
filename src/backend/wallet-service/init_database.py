#!/usr/bin/env python3
"""
Database initialization script for the wallet service.
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import Base, User, WalletConnection

# Database URL
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://alphintra:alphintra123@postgres:5432/alphintra"
)

def create_database():
    """Create database tables"""
    engine = create_engine(DATABASE_URL)
    
    print("Creating wallet service database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")
    
    return engine

def create_sample_data(engine):
    """Create sample user for testing"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Check if test user already exists
        test_user = db.query(User).filter(User.email == "wallet_test@alphintra.com").first()
        
        if not test_user:
            print("Creating test user...")
            test_user = User(
                email="wallet_test@alphintra.com",
                password_hash="hashed_password_here",
                first_name="Wallet",
                last_name="Test",
                is_verified=True,
                is_active=True
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
            print(f"✅ Created test user: {test_user.email}")
        else:
            print(f"✅ Test user already exists: {test_user.email}")
        
        print("🎉 Wallet service database initialization completed!")
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        db.rollback()
        raise e
    finally:
        db.close()

def main():
    """Main initialization function"""
    print("🚀 Initializing Wallet Service Database...")
    
    try:
        engine = create_database()
        create_sample_data(engine)
        
        print("\n" + "="*50)
        print("✅ Database initialization completed successfully!")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ Database initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://alphintra:alphintra123@postgres:5432/alphintra"
)

# Create engine
engine = create_engine(
    DATABASE_URL, 
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=300     # Recreate connections every 5 minutes
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Database dependency for FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create tables (called on startup)
def create_tables():
    Base.metadata.create_all(bind=engine)
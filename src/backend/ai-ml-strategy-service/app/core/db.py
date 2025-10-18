from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import NullPool
from .config import settings
import os


class Base(DeclarativeBase):
    pass


engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
    poolclass=None if settings.DATABASE_URL.startswith("postgresql") else NullPool,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    # Imported locally to avoid circular imports
    from ..models.project import Project
    from ..models.file import ProjectFile
    # Ensure sqlite directory exists when using a file path
    if settings.DATABASE_URL.startswith("sqlite"):
        # Extract file path part after sqlite:/// or sqlite:////
        url = settings.DATABASE_URL
        prefix = "sqlite:///"
        if url.startswith("sqlite:////"):
            prefix = "sqlite:////"
        path = url[len(prefix):]
        dir_path = os.path.dirname(path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

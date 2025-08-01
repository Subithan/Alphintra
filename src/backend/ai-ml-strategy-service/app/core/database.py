"""
Database configuration and session management.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import NullPool
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)

# Create async database engine
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,
    poolclass=NullPool if settings.is_development else None,
    echo=settings.DEBUG,
)

# Create async session maker
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Create base class for declarative models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session for dependency injection.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database - create tables if they don't exist.
    """
    try:
        async with engine.begin() as conn:
            # Import all models to ensure they are registered
            from app.models import (
                strategy,
                dataset,
                training,
                backtesting,
                paper_trading,
                experiment
            )
            
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
            
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise


async def close_db() -> None:
    """
    Close database engine.
    """
    await engine.dispose()
    logger.info("Database engine disposed")


# TimescaleDB connection (if configured)
timescale_engine = None
TimescaleSessionLocal = None

if settings.TIMESCALE_DATABASE_URL:
    timescale_engine = create_async_engine(
        settings.TIMESCALE_DATABASE_URL,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_pre_ping=True,
        echo=settings.DEBUG,
    )
    
    TimescaleSessionLocal = async_sessionmaker(
        timescale_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def get_timescale_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get TimescaleDB session for time-series data.
    """
    if not TimescaleSessionLocal:
        raise RuntimeError("TimescaleDB not configured")
    
    async with TimescaleSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
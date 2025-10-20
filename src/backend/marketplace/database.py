from __future__ import annotations

import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from config import settings
from model import Base, Order, Strategy

logger = logging.getLogger(__name__)

engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


def create_db_and_tables() -> None:
    """Create database tables if they do not exist."""
    Base.metadata.create_all(bind=engine, checkfirst=True)
    logger.info("Database schema ready.")


def seed_demo_data() -> None:
    """
    Populate the database with a handful of demo strategies so the service is
    immediately usable when started locally.
    """
    if not settings.seed_demo_data:
        logger.info("Skipping demo data seeding (disabled via settings).")
        return

    with SessionLocal() as session:
        if session.query(Strategy).limit(1).first():
            logger.info("Demo data already present; skipping seeding.")
            return

        demo_strategies = [
            Strategy(
                name="Day Trading Momentum",
                price_cents=9900,
                description="Short holding periods with configurable risk controls.",
                strategy_file="strategies/day_trading_momentum.py",
            ),
            Strategy(
                name="Swing Trader Pro",
                price_cents=14900,
                description="Multi-day swing trading with automated stop losses.",
                strategy_file="strategies/swing_trader_pro.py",
            ),
            Strategy(
                name="Long-Term Growth",
                price_cents=5900,
                description="Diversified strategy focused on growth equities.",
                strategy_file="strategies/long_term_growth.py",
            ),
        ]

        session.add_all(demo_strategies)
        session.flush()

        for idx, strategy in enumerate(demo_strategies, start=1):
            strategy.subscriber_count = 1
            session.add(
                Order(
                    strategy_id=strategy.id,
                    buyer_id=idx,
                    notes="Seeded demo order.",
                )
            )

        session.commit()
        logger.info("Seeded %s demo strategies and demo orders.", len(demo_strategies))


def get_session():
    """FastAPI dependency to provide a database session."""
    session: Session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

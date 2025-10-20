from typing import Any, List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from model import Order, OrderCreate, Strategy, StrategyCreate


def _model_to_dict(model: Any) -> dict:
    """Support Pydantic v1 and v2 style models."""
    if hasattr(model, "model_dump"):
        return model.model_dump()
    if hasattr(model, "dict"):
        return model.dict()
    raise TypeError(f"Unsupported model type for serialization: {type(model)!r}")


def list_strategies(db: Session) -> List[Strategy]:
    """Return all strategies ordered by creation."""
    return db.query(Strategy).order_by(Strategy.id).all()


def create_strategy(db: Session, payload: StrategyCreate) -> Strategy:
    """Persist a new strategy."""
    strategy = Strategy(**_model_to_dict(payload))
    db.add(strategy)
    db.commit()
    db.refresh(strategy)
    return strategy


def get_strategy_or_404(db: Session, strategy_id: int) -> Strategy:
    strategy = db.get(Strategy, strategy_id)
    if not strategy or not strategy.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found.")
    return strategy


def list_orders(db: Session) -> List[Order]:
    """Return all orders (useful for debugging via curl/Adminer)."""
    return db.query(Order).order_by(Order.id.desc()).all()


def purchase_strategy(db: Session, strategy_id: int, payload: OrderCreate) -> Order:
    """Record a paid order for a strategy and increment the subscriber count."""
    strategy = get_strategy_or_404(db, strategy_id)

    order_payload = _model_to_dict(payload)
    order_payload["status"] = "paid"
    order = Order(strategy_id=strategy.id, **order_payload)

    db.add(order)
    strategy.subscriber_count += 1
    db.commit()

    db.refresh(order)
    db.refresh(strategy)
    return order

# marketplace/models.py

from typing import Optional
from sqlmodel import Field, SQLModel, Relationship

# --- Core Marketplace Models ---

class StrategyBase(SQLModel):
    name: str
    price_cents: int = Field(gt=0, description="Price in CENTS")
    description: str
    stripe_price_id: Optional[str] = Field(default=None, index=True)
    subscriber_count: int = Field(default=0)

class Strategy(StrategyBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # Optional: Define relationship to subscriptions
    subscriptions: list["Subscription"] = Relationship(back_populates="strategy")

# --- Subscription Model (The outcome of a successful payment) ---

class SubscriptionBase(SQLModel):
    # Foreign key link
    strategy_id: int = Field(index=True, foreign_key="strategy.id")
    # Payment details from Stripe
    stripe_session_id: str = Field(unique=True, index=True)
    customer_email: str
    status: str = Field(default="pending") # e.g., "pending", "paid", "failed"

class Subscription(SubscriptionBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # Optional: Define relationship to Strategy
    strategy: Strategy = Relationship(back_populates="subscriptions")
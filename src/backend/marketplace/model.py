from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Strategy(Base):
    __tablename__ = "strategy"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    strategy_file: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # image_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    subscriber_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    orders: Mapped[List["Order"]] = relationship(
        "Order",
        back_populates="strategy",
        cascade="all, delete-orphan",
    )


class Order(Base):
    __tablename__ = "order"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    strategy_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("strategy.id", ondelete="CASCADE"),
        nullable=False,
    )
    buyer_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="paid")

    strategy: Mapped["Strategy"] = relationship("Strategy", back_populates="orders")


class StrategyBase(BaseModel):
    name: str
    price_cents: int = Field(gt=0, description="Price in cents")
    description: str = ""
    is_active: bool = True
    strategy_file: Optional[str] = None
    # image_url: Optional[str] = None

class StrategyCreate(StrategyBase):
    pass


class StrategyRead(StrategyBase):
    id: int
    subscriber_count: int

    model_config = ConfigDict(from_attributes=True)


class OrderBase(BaseModel):
    buyer_id: int
    notes: Optional[str] = Field(default=None, max_length=1024)


class OrderCreate(OrderBase):
    pass


class OrderRead(OrderBase):
    id: int
    strategy_id: int
    status: str

    model_config = ConfigDict(from_attributes=True)


class StrategySummary(BaseModel):
    id: int
    name: str
    price_cents: int
    description: str
    subscriber_count: int

    model_config = ConfigDict(from_attributes=True)


class OrderWithStrategyRead(OrderRead):
    strategy: StrategySummary

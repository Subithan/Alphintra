from typing import Annotated, List

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
# from fastapi.staticfiles import StaticFiles

from config import settings
from database import create_db_and_tables, get_session, seed_demo_data
from model import (
    OrderCreate,
    OrderRead,
    OrderWithStrategyRead,
    StrategyCreate,
    StrategyRead,
)
from service import (
    purchase_strategy,
    create_strategy,
    list_orders,
    list_orders_for_buyer,
    list_strategies,
)

SessionDep = Annotated[Session, Depends(get_session)]

app = FastAPI(title="Marketplace Service", version="1.0.0")

# Serve local images / assets from /static
# app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    create_db_and_tables()
    seed_demo_data()


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/docs")


@app.get("/strategies", response_model=List[StrategyRead])
def read_strategies(db: SessionDep):
    return list_strategies(db)


@app.post("/strategies", response_model=StrategyRead, status_code=201)
def create_strategies(strategy: StrategyCreate, db: SessionDep):
    return create_strategy(db, strategy)


@app.post("/strategies/{strategy_id}/purchase", response_model=OrderRead, status_code=201)
def buy_strategy(strategy_id: int, order: OrderCreate, db: SessionDep):
    return purchase_strategy(db, strategy_id, order)


@app.get("/orders", response_model=List[OrderRead])
def read_orders(db: SessionDep):
    return list_orders(db)


@app.get("/orders/by-buyer/{buyer_id}", response_model=List[OrderWithStrategyRead])
def read_orders_for_buyer(buyer_id: int, db: SessionDep):
    return list_orders_for_buyer(db, buyer_id)


@app.get("/health")
def health_check():
    return {"status": "healthy"}

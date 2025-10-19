# marketplace/main.py

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware # <--- NEW IMPORT for CORS
from sqlmodel import Session, select
from typing import Annotated, List

# CRITICAL FIX: Explicitly import 'engine' along with the functions
from database import create_db_and_tables, get_session, engine 
from model import Strategy
from service import create_checkout_session_for_strategy
from webhooks import router as webhooks_router

# The session dependency type
SessionDep = Annotated[Session, Depends(get_session)]

# 1. Initialize FastAPI app
app = FastAPI(
    title="Stripe Marketplace API",
    version="1.0.0",
)

# 2. ADD CORS MIDDLEWARE (FIX)
# These origins cover common frontend development ports (3000=React/Vite, 8080=Vue/Webpack)
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8080",
    "http://localhost:5173", # Common Vite port
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include the webhook router
app.include_router(webhooks_router, prefix="/webhooks")


@app.on_event("startup")
def on_startup():
    """
    Called when the application starts.
    1. Assigns the imported engine to the app state.
    2. Creates database tables.
    3. Adds dummy data if none exists.
    """
    app.state.engine = engine
    create_db_and_tables()
    
    with Session(app.state.engine) as session:
        if not session.exec(select(Strategy)).first():
            dummy_strategy = Strategy(
                name="Day Trading Bot",
                price_cents=9999, # $99.99
                description="Our top performing day trading algorithm.",
            )
            session.add(dummy_strategy)
            session.commit()
            print("INFO: Added a dummy Strategy for testing.")


# --- Application Routes ---

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")


@app.get("/strategies/", response_model=List[Strategy])
def read_strategies(db: SessionDep):
    """List all available trading strategies."""
    strategies = db.exec(select(Strategy)).all()
    return strategies


@app.post("/strategies/{strategy_id}/purchase", status_code=status.HTTP_303_SEE_OTHER)
def purchase_strategy(strategy_id: int, user_email: str, db: SessionDep):
    """
    Creates a Stripe Checkout Session and redirects the user to the Stripe page.
    """
    checkout_session = create_checkout_session_for_strategy(db, strategy_id, user_email)
    
    # Return a 303 Redirect to the Stripe Checkout page
    return RedirectResponse(url=checkout_session.url, status_code=status.HTTP_303_SEE_OTHER)


# --- Frontend Feedback Routes (Simplified) ---

@app.get("/success")
def payment_success(session_id: str):
    return {"message": "Payment successful! We are fulfilling your order. Session ID: " + session_id}

@app.get("/cancel")
def payment_cancel():
    return {"message": "Payment cancelled. You were not charged."}

@app.get("/health")
def health_check():
    """
    Health check endpoint for the service.
    """
    return {"status": "healthy"}

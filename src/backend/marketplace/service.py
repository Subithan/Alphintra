import stripe
from fastapi import HTTPException
from sqlmodel import Session, select

from config import settings
from model import Strategy, Subscription

# Initialize Stripe Client
# stripe.api_key = settings.STRIPE_SECRET_KEY # 🛑 NOTE: Keep this line, but the key status is checked below

# --- Core Business Logic Functions ---

def create_checkout_session_for_strategy(db: Session, strategy_id: int, user_email: str):
    """
    Creates a new Stripe Checkout Session for a given strategy.
    """
    # 🛑 DEBUG CHECK: Ensure the key is set before proceeding
    if not settings.STRIPE_SECRET_KEY:
        print("FATAL ERROR: STRIPE_SECRET_KEY is empty in settings.")
        # Raise an exception that returns a 500 error to the client
        raise HTTPException(status_code=500, detail="Internal Error: Stripe Secret Key is not configured.")

    # Apply the key to the Stripe client (in case the initialization at the top failed)
    stripe.api_key = settings.STRIPE_SECRET_KEY
    print(f"DEBUG: Stripe API Key loaded. Key starts with: {stripe.api_key[:8]}...")
    
    strategy = db.get(Strategy, strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    if not strategy.stripe_price_id:
        # NOTE: In a real app, you would dynamically create this Price object
        # or pre-populate it in your DB. For this demo, we'll create an ad-hoc price.
        try:
            price = stripe.Price.create(
                currency="usd",
                unit_amount=strategy.price_cents,
                product_data={"name": strategy.name},
            )
            strategy.stripe_price_id = price.id
            db.add(strategy)
            db.commit()
            db.refresh(strategy)
        except stripe.error.AuthenticationError:
            raise HTTPException(status_code=500, detail="Stripe Authentication Failed. Check STRIPE_SECRET_KEY validity.")
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=500, detail=f"Stripe Price Creation Error: {e}")


    # 1. Create a new PENDING subscription record
    new_subscription = Subscription(
        strategy_id=strategy.id,
        customer_email=user_email,
        # We will populate stripe_session_id after session creation
        stripe_session_id="TEMP", 
        status="pending"
    )
    db.add(new_subscription)
    db.commit()
    db.refresh(new_subscription)
    
    try:
        # 2. Call the Stripe API to create the Checkout Session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price": strategy.stripe_price_id,
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=f"{settings.DOMAIN_URL}/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.DOMAIN_URL}/cancel",
            # Pass our unique subscription ID to Stripe for later reference in the webhook
            metadata={"local_subscription_id": new_subscription.id},
            customer_email=user_email,
        )

        print(f"DEBUG: Created Stripe Checkout Session: {checkout_session.id}")
        print(f"DEBUG: Session URL: {checkout_session.url}")
        print(f"DEBUG: Session status: {checkout_session.status}")
        print(f"DEBUG: Session payment_status: {checkout_session.payment_status}")

        # 3. Update the subscription record with the actual session ID
        new_subscription.stripe_session_id = checkout_session.id
        db.add(new_subscription)
        db.commit()
        db.refresh(new_subscription)

        return checkout_session

    except stripe.error.StripeError as e:
        # Rollback or mark the pending subscription as failed/cancelled if Stripe call fails
        db.delete(new_subscription)
        db.commit()
        # This will now print a much clearer error to the Docker logs AND to the frontend
        raise HTTPException(status_code=500, detail=f"Stripe Session Creation Error: {e}")


def fulfill_order_from_webhook(db: Session, session_id: str) -> bool:
    """
    Fulfills the order by updating the database after a successful payment webhook.
    """
    subscription = db.exec(select(Subscription).where(Subscription.stripe_session_id == session_id)).first()

    if not subscription:
        print(f"ERROR: Subscription with session ID {session_id} not found.")
        return False
    
    if subscription.status == "paid":
        print(f"WARNING: Subscription {session_id} already fulfilled.")
        return True # Already fulfilled

    # 1. Update the Subscription status to 'paid'
    subscription.status = "paid"
    db.add(subscription)
    
    # 2. Update the Strategy's subscriber count
    strategy = db.get(Strategy, subscription.strategy_id)
    if strategy:
        strategy.subscriber_count += 1
        db.add(strategy)
        
    db.commit()
    print(f"SUCCESS: Subscription {session_id} fulfilled for strategy {strategy.name}.")
    return True

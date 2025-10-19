# marketplace/webhooks.py

import stripe
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlmodel import Session, select
from typing import Annotated

from config import settings
from database import get_session
from service import fulfill_order_from_webhook

# Use APIRouter to define the routes for webhooks
router = APIRouter(tags=["webhooks"])

# Initialize Stripe Client
stripe.api_key = settings.STRIPE_SECRET_KEY

# The session dependency type
SessionDep = Annotated[Session, Depends(get_session)]

@router.post("/stripe")
async def stripe_webhook(request: Request, db: SessionDep):
    """
    Receives real-time events from Stripe (e.g., successful payment).
    """
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET
    signature = request.headers.get("stripe-signature")
    payload = await request.body()
    
    try:
        # 1. Verify the event signature to ensure it is from Stripe
        event = stripe.Webhook.construct_event(
            payload, signature, webhook_secret
        )
    except Exception as e:
        # Return a 400 status code for bad requests/verification failure
        raise HTTPException(status_code=400, detail=str(e))

    # 2. Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        session_id = session.get('id')
        
        # Check if the payment was successful
        if session.get('payment_status') == 'paid':
            # Call the fulfillment logic
            fulfill_order_from_webhook(db, session_id)
        
        # NOTE: You would also handle other events here, like 'checkout.session.async_payment_succeeded', etc.

    return {"status": "success"}
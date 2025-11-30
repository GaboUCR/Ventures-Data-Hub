import os

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import stripe
from dotenv import load_dotenv

# Load .env file (optional but handy in dev)
load_dotenv()

STRIPE_API_KEY = os.getenv("STRIPE_API_KEY")

if not STRIPE_API_KEY:
    raise RuntimeError("STRIPE_API_KEY is not set. Make sure it's in your environment or .env file.")

# Configure Stripe SDK
stripe.api_key = STRIPE_API_KEY

app = FastAPI(title="Ace Analytics – Stripe Test")

# CORS (optional, but useful if you call from React later)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/stripe/charges")
def get_stripe_charges(limit: int = Query(10, ge=1, le=100)):
    """
    Simple endpoint to read charges from your Stripe account (test mode if your key is test).
    """
    try:
        charges = stripe.Charge.list(limit=limit)
        # charges is a stripe.ListObject; .data is a list of Charge objects
        items = [c for c in charges.data]
        return {"items": items}
    except stripe.error.StripeError as e:
        # Stripe-specific error
        raise HTTPException(status_code=502, detail=f"Stripe error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

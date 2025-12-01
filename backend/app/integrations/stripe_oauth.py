# app/integrations/stripe_oauth.py
from urllib.parse import urlencode
import stripe
from fastapi import HTTPException
from app.core.config import settings
from app.storage.connections import save_stripe_account, get_stripe_access_token

stripe.api_key = settings.STRIPE_SECRET_KEY

def build_stripe_oauth_url(state: str) -> str:
    params = {
        "response_type": "code",
        "client_id": settings.STRIPE_CLIENT_ID,
        "scope": "read_write",
        "redirect_uri": "http://localhost:8000/stripe/oauth/callback",
        "state": state,
    }
    return f"https://connect.stripe.com/oauth/authorize?{urlencode(params)}"

def handle_stripe_oauth_callback(code: str) -> str:
    try:
        token_resp = stripe.OAuth.token(grant_type="authorization_code", code=code)
        account_id = token_resp["stripe_user_id"]

        save_stripe_account(account_id, {
            "access_token": token_resp["access_token"],
            "refresh_token": token_resp.get("refresh_token"),
            "scope": token_resp.get("scope"),
            "token_type": token_resp.get("token_type"),
            "livemode": token_resp.get("livemode"),
            "stripe_publishable_key": token_resp.get("stripe_publishable_key"),
        })
        return account_id
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=502, detail=f"Stripe error during OAuth token exchange: {str(e)}")

def list_charges_for_account(account_id: str, limit: int = 10):
    access_token = get_stripe_access_token(account_id)
    charges = stripe.Charge.list(limit=limit, api_key=access_token)
    return [c for c in charges.data]

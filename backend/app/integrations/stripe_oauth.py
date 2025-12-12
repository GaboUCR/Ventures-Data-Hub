# app/integrations/stripe_oauth.py
from urllib.parse import urlencode
import app.etl.stripe_etl as stripe_etl
from fastapi import HTTPException

from app.core.config import settings
from app.storage.connections import save_stripe_account, get_stripe_access_token

stripe_etl.api_key = settings.STRIPE_SECRET_KEY


def build_stripe_oauth_url(company_id: str, state: str) -> str:
    """
    Build Stripe Connect OAuth URL.
    As with GA, 'state' should embed CSRF token + company_id.
    """
    params = {
        "response_type": "code",
        "client_id": settings.STRIPE_CLIENT_ID,
        "scope": "read_write",  # can be 'read_only' if you wish later
        "redirect_uri": "http://localhost:8000/stripe/oauth/callback",
        "state": state,
    }
    return f"https://connect.stripe.com/oauth/authorize?{urlencode(params)}"


def handle_stripe_oauth_callback(company_id: str, code: str) -> str:
    """
    Exchange OAuth code for an access token and store it via core.integration_connections.
    Returns integration connection id (UUID as string).
    """
    try:
        token_resp = stripe_etl.OAuth.token(grant_type="authorization_code", code=code)
        account_id = token_resp["stripe_user_id"]

        connection_id = save_stripe_account(
            company_id=company_id,
            account_id=account_id,
            data={
                "access_token": token_resp["access_token"],
                "refresh_token": token_resp.get("refresh_token"),
                "scope": token_resp.get("scope"),
                "token_type": token_resp.get("token_type"),
                "livemode": token_resp.get("livemode"),
                "stripe_publishable_key": token_resp.get("stripe_publishable_key"),
            },
        )
        return connection_id
    except stripe_etl.error.StripeError as e:
        raise HTTPException(status_code=502, detail=f"Stripe error during OAuth token exchange: {str(e)}")

def list_charges_for_account(connection_id: str, limit: int = 10):
    """
    Use connection_id (integration_connections.id) to fetch the Stripe access token
    and list charges for that connected account.
    """
    access_token = get_stripe_access_token(connection_id)
    charges = stripe_etl.Charge.list(limit=limit, api_key=access_token)
    return [c for c in charges.data]

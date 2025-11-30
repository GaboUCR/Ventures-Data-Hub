import os
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv
from urllib.parse import urlencode

import stripe

# Load .env file
load_dotenv()

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_CLIENT_ID = os.getenv("STRIPE_CLIENT_ID")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

if not STRIPE_SECRET_KEY:
    raise RuntimeError("STRIPE_SECRET_KEY is not set. Make sure it's in your environment or .env file.")

if not STRIPE_CLIENT_ID:
    raise RuntimeError("STRIPE_CLIENT_ID is not set. Configure it from your Stripe Connect settings.")

# This is YOUR platform secret key, used for OAuth exchanges, etc.
stripe.api_key = STRIPE_SECRET_KEY

app = FastAPI(title="Ace Analytics – Stripe OAuth Test")

# CORS (for React / local dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------------
# ⚠️ DEMO ONLY: In-memory store of connected accounts
# In a real app, you’d store this in a DB, tied to your tenant/company.
# -------------------------------------------------------------------
CONNECTED_ACCOUNTS: Dict[str, Dict[str, Any]] = {}


@app.get("/health")
def health_check():
    return {"status": "ok"}


# 1) Generate Stripe OAuth URL (your frontend will hit this, then redirect the user)
@app.get("/stripe/oauth/url")
def get_stripe_oauth_url(state: str = "demo-state"):
    """
    Returns the Stripe Connect OAuth URL for a user to connect their Stripe account.
    In real life, 'state' should be a random CSRF token tied to the logged-in user/tenant.
    """
    params = {
        "response_type": "code",
        "client_id": STRIPE_CLIENT_ID,
        "scope": "read_write",  # for analytics we usually only need read-only
        "redirect_uri": "http://localhost:8000/stripe/oauth/callback",
        "state": state,
    }

    url = f"https://connect.stripe.com/oauth/authorize?{urlencode(params)}"
    return {"url": url}


# 2) OAuth callback – Stripe redirects the user here after they approve access
@app.get("/stripe/oauth/callback")
def stripe_oauth_callback(code: str | None = None, state: str | None = None, error: str | None = None):
    """
    Handles the redirect from Stripe. Exchanges 'code' for an access token
    that we can use to call Stripe's API on behalf of that connected account.
    """
    if error:
        # User denied, or some other issue
        raise HTTPException(status_code=400, detail=f"Stripe OAuth error: {error}")

    if not code:
        raise HTTPException(status_code=400, detail="Missing 'code' parameter from Stripe OAuth.")

    try:
        # Exchange the code for an access token & account info
        token_resp = stripe.OAuth.token(
            grant_type="authorization_code",
            code=code,
        )

        # token_resp will contain fields like:
        # access_token, refresh_token, stripe_user_id, scope, livemode, token_type, stripe_publishable_key, etc.
        account_id = token_resp["stripe_user_id"]

        CONNECTED_ACCOUNTS[account_id] = {
            "access_token": token_resp["access_token"],
            "refresh_token": token_resp.get("refresh_token"),
            "scope": token_resp.get("scope"),
            "token_type": token_resp.get("token_type"),
            "livemode": token_resp.get("livemode"),
            "stripe_publishable_key": token_resp.get("stripe_publishable_key"),
        }

        # In a real app, you’d persist this in your DB and associate it with the logged-in tenant.

        # After successful connection, send the user back to your frontend
        redirect_url = f"{FRONTEND_URL}/integrations/stripe/success?account_id={account_id}"
        return RedirectResponse(redirect_url)

    except stripe.error.StripeError as e:
        raise HTTPException(status_code=502, detail=f"Stripe error during OAuth token exchange: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_access_token_for_account(account_id: str) -> str:
    """
    Helper to get the connected account's access token.
    In real life, you'd fetch this from a DB using the tenant + provider.
    """
    account = CONNECTED_ACCOUNTS.get(account_id)
    if not account or "access_token" not in account:
        raise HTTPException(status_code=404, detail=f"No connected Stripe account found for id={account_id}")
    return account["access_token"]


# 3) Use the connected account's access token to list charges
@app.get("/stripe/{account_id}/charges")
def get_stripe_charges(
    account_id: str,
    limit: int = Query(10, ge=1, le=100),
):
    """
    Lists charges for a specific connected Stripe account.
    'account_id' here is the Stripe account id (e.g., acct_123...) returned via OAuth.
    """
    try:
        access_token = get_access_token_for_account(account_id)

        # Use the connected account's access token instead of your platform secret
        charges = stripe.Charge.list(limit=limit, api_key=access_token)

        items = [c for c in charges.data]
        return {"items": items}
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=502, detail=f"Stripe error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

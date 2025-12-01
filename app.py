import os
from typing import Dict, Any
from urllib.parse import urlencode

import requests  
import stripe
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse


# Load .env file
load_dotenv()

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_CLIENT_ID = os.getenv("STRIPE_CLIENT_ID")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/ga/oauth/callback")
GA4_PROPERTY_ID = os.getenv("GA4_PROPERTY_ID")  # e.g. "123456789"
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

if not STRIPE_SECRET_KEY:
    raise RuntimeError("STRIPE_SECRET_KEY is not set. Make sure it's in your environment or .env file.")

if not STRIPE_CLIENT_ID:
    raise RuntimeError("STRIPE_CLIENT_ID is not set. Configure it from your Stripe Connect settings.")

# This is YOUR platform secret key, used for OAuth exchanges, etc.
stripe.api_key = STRIPE_SECRET_KEY

if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
    raise RuntimeError("Google OAuth CLIENT_ID / CLIENT_SECRET not configured.")

GA_SCOPE = "https://www.googleapis.com/auth/analytics.readonly"

app = FastAPI(title="Ace Analytics – Stripe + GA4")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DEMO ONLY: in-memory store of GA tokens ---
GA_CONNECTIONS: Dict[str, Dict[str, Any]] = {}


# -------------------------------------------------------------------
# ⚠️ DEMO ONLY: In-memory store of connected accounts
# In a real app, you’d store this in a DB, tied to your tenant/company.
# -------------------------------------------------------------------
CONNECTED_ACCOUNTS: Dict[str, Dict[str, Any]] = {}


@app.get("/health")
def health_check():
    return {"status": "ok"}

# 1) Generate Google OAuth URL for GA4
@app.get("/ga/oauth/url")
def get_ga_oauth_url(state: str = "demo-state"):
    """
    Frontend calls this, then redirects user to the returned URL.
    In real life, 'state' should be a random CSRF token tied to the logged-in tenant/user.
    """
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": GA_SCOPE,
        "access_type": "offline",              # so we get a refresh_token
        "include_granted_scopes": "true",
        "prompt": "consent",                   # forces showing consent screen to get refresh_token
        "state": state,
    }
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
    return {"url": url}


# 2) OAuth callback – Google sends 'code' here
@app.get("/ga/oauth/callback")
def ga_oauth_callback(code: str | None = None, state: str | None = None, error: str | None = None):
    if error:
        raise HTTPException(status_code=400, detail=f"Google OAuth error: {error}")
    if not code:
        raise HTTPException(status_code=400, detail="Missing 'code' parameter from Google OAuth.")

    # Exchange code for access_token + refresh_token
    token_resp = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    if not token_resp.ok:
        raise HTTPException(status_code=502, detail=f"Token exchange failed: {token_resp.text}")

    tokens = token_resp.json()
    # tokens includes: access_token, expires_in, refresh_token (if first time), scope, token_type, id_token

    # DEMO: single connection id. In real app, tie this to tenant + provider.
    connection_id = "default"
    GA_CONNECTIONS[connection_id] = tokens

    # Redirect back to frontend with connection id
    redirect_url = f"{FRONTEND_URL}/integrations/ga4/success?connection_id={connection_id}"
    return RedirectResponse(redirect_url)


def get_ga_access_token(connection_id: str = "default") -> str:
    tokens = GA_CONNECTIONS.get(connection_id)
    if not tokens or "access_token" not in tokens:
        raise HTTPException(status_code=404, detail="No GA4 connection or access token")
    # NOTE: in a real app you must check expiry and refresh using refresh_token if needed.
    return tokens["access_token"]


# 3) Example: run a simple GA4 report
@app.get("/ga/{connection_id}/basic-report")
def ga_basic_report(connection_id: str, days: int = Query(7, ge=1, le=30)):
    """
    Calls GA4 Data API to get activeUsers by default channel group over the last N days.
    """
    if not GA4_PROPERTY_ID:
        raise HTTPException(status_code=500, detail="GA4_PROPERTY_ID not configured in backend.")

    access_token = get_ga_access_token(connection_id)

    url = f"https://analyticsdata.googleapis.com/v1beta/properties/{GA4_PROPERTY_ID}:runReport"
    body = {
        "dateRanges": [
            {"startDate": f"{days}daysAgo", "endDate": "today"}
        ],
        "dimensions": [
            {"name": "sessionDefaultChannelGroup"}
        ],
        "metrics": [
            {"name": "activeUsers"}
        ],
        "limit": 10,
    }

    resp = requests.post(
        url,
        json=body,
        headers={"Authorization": f"Bearer {access_token}"},
    )

    if not resp.ok:
        raise HTTPException(status_code=502, detail=f"GA4 API error: {resp.text}")

    return resp.json()

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

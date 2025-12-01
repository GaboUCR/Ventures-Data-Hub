# app/api/routes/stripe.py
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from app.core.config import settings
from app.integrations.stripe_oauth import (
    build_stripe_oauth_url,
    handle_stripe_oauth_callback,
    list_charges_for_account,
)

router = APIRouter(prefix="/stripe", tags=["stripe"])

@router.get("/oauth/url")
def get_stripe_oauth_url(state: str = "demo-state"):
    url = build_stripe_oauth_url(state)
    return {"url": url}

@router.get("/oauth/callback")
def stripe_oauth_callback(code: str | None = None, state: str | None = None, error: str | None = None):
    if error:
        raise HTTPException(status_code=400, detail=f"Stripe OAuth error: {error}")
    if not code:
        raise HTTPException(status_code=400, detail="Missing 'code' parameter from Stripe OAuth.")

    account_id = handle_stripe_oauth_callback(code)
    redirect_url = f"{settings.FRONTEND_URL}/integrations/stripe/success?account_id={account_id}"
    return RedirectResponse(redirect_url)

@router.get("/{account_id}/charges")
def get_stripe_charges(account_id: str, limit: int = Query(10, ge=1, le=100)):
    items = list_charges_for_account(account_id, limit)
    return {"items": items}

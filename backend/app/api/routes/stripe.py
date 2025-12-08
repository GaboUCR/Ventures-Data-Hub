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
def get_stripe_oauth_url(
    company_id: str = Query(..., description="ID of the company to connect Stripe for"),
    state: str = Query("demo-state", description="CSRF token or client state"),
):
    """
    Returns the Stripe Connect OAuth URL for a given company.

    We embed the company_id in the OAuth `state` so we can recover it in the callback.
    """
    combined_state = f"{state}|{company_id}"
    url = build_stripe_oauth_url(company_id=company_id, state=combined_state)
    return {"url": url}


@router.get("/oauth/callback")
def stripe_oauth_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
):
    if error:
        raise HTTPException(status_code=400, detail=f"Stripe OAuth error: {error}")
    if not code:
        raise HTTPException(status_code=400, detail="Missing 'code' parameter from Stripe OAuth.")
    if not state:
        raise HTTPException(status_code=400, detail="Missing 'state' parameter from Stripe OAuth.")

    # state = "<csrf>|<company_id>"
    try:
        _csrf, company_id = state.split("|", 1)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid state format from Stripe OAuth.")

    # Persist tokens in DB, get integration_connections.id as connection_id
    connection_id = handle_stripe_oauth_callback(company_id=company_id, code=code)

    redirect_url = (
        f"{settings.FRONTEND_URL}"
        f"/integrations/stripe/success?company_id={company_id}&connection_id={connection_id}"
    )
    return RedirectResponse(redirect_url)


@router.get("/{connection_id}/charges")
def get_stripe_charges(
    connection_id: str,
    limit: int = Query(10, ge=1, le=100),
):
    """
    Test endpoint: list charges for a given Stripe connection (integration_connections.id).
    """
    items = list_charges_for_account(connection_id, limit)
    return {"items": items}

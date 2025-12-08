# app/api/routes/ga.py
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse

from app.core.config import settings
from app.integrations.ga4_oauth import (
    build_ga_oauth_url,
    exchange_ga_code_for_tokens,
    run_basic_ga_report,
)

router = APIRouter(prefix="/ga", tags=["google-analytics"])


@router.get("/oauth/url")
def get_ga_oauth_url(
    company_id: str = Query(..., description="ID of the company to connect GA4 for"),
    state: str = Query("demo-state", description="CSRF token or client state"),
):
    """
    Returns the Google OAuth URL for a given company.

    We embed the company_id in the OAuth `state` so we can recover it in the callback.
    """
    combined_state = f"{state}|{company_id}"
    url = build_ga_oauth_url(company_id=company_id, state=combined_state)
    return {"url": url}


@router.get("/oauth/callback")
def ga_oauth_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
):
    if error:
        raise HTTPException(status_code=400, detail=f"Google OAuth error: {error}")
    if not code:
        raise HTTPException(status_code=400, detail="Missing 'code' parameter from Google OAuth.")
    if not state:
        raise HTTPException(status_code=400, detail="Missing 'state' parameter from Google OAuth.")

    # state = "<csrf>|<company_id>"
    try:
        _csrf, company_id = state.split("|", 1)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid state format from Google OAuth.")

    # Persist tokens in DB, get integration_connections.id as connection_id
    connection_id = exchange_ga_code_for_tokens(company_id=company_id, code=code)

    redirect_url = (
        f"{settings.FRONTEND_URL}"
        f"/integrations/ga4/success?company_id={company_id}&connection_id={connection_id}"
    )
    return RedirectResponse(redirect_url)


@router.get("/{connection_id}/basic-report")
def ga_basic_report(
    connection_id: str,
    days: int = Query(7, ge=1, le=30),
):
    """
    Simple test endpoint: run a GA4 report using the stored connection_id.
    """
    return run_basic_ga_report(connection_id, days)

# app/api/routes/ga.py
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from app.core.config import settings
from app.integrations.ga4_oauth import build_ga_oauth_url, exchange_ga_code_for_tokens, run_basic_ga_report

router = APIRouter(prefix="/ga", tags=["google-analytics"])

@router.get("/oauth/url")
def get_ga_oauth_url(state: str = "demo-state"):
    url = build_ga_oauth_url(state)
    return {"url": url}

@router.get("/oauth/callback")
def ga_oauth_callback(code: str | None = None, state: str | None = None, error: str | None = None):
    if error:
        raise HTTPException(status_code=400, detail=f"Google OAuth error: {error}")
    if not code:
        raise HTTPException(status_code=400, detail="Missing 'code' parameter from Google OAuth.")

    connection_id = exchange_ga_code_for_tokens(code)
    redirect_url = f"{settings.FRONTEND_URL}/integrations/ga4/success?connection_id={connection_id}"
    return RedirectResponse(redirect_url)

@router.get("/{connection_id}/basic-report")
def ga_basic_report(connection_id: str, days: int = Query(7, ge=1, le=30)):
    return run_basic_ga_report(connection_id, days)

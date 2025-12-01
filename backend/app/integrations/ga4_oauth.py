# app/integrations/ga4_oauth.py
from urllib.parse import urlencode
import requests
from fastapi import HTTPException
from app.core.config import settings
from app.storage.connections import save_ga_tokens, get_ga_access_token

def build_ga_oauth_url(state: str) -> str:
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": settings.GA_SCOPE,
        "access_type": "offline",
        "include_granted_scopes": "true",
        "prompt": "consent",
        "state": state,
    }
    return "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)

def exchange_ga_code_for_tokens(code: str) -> str:
    token_resp = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    if not token_resp.ok:
        raise HTTPException(status_code=502, detail=f"Token exchange failed: {token_resp.text}")

    tokens = token_resp.json()
    connection_id = "default"  # later: tenant-specific
    save_ga_tokens(connection_id, tokens)
    return connection_id

def run_basic_ga_report(connection_id: str, days: int):
    if not settings.GA4_PROPERTY_ID:
        raise HTTPException(status_code=500, detail="GA4_PROPERTY_ID not configured.")

    access_token = get_ga_access_token(connection_id)
    url = f"https://analyticsdata.googleapis.com/v1beta/properties/{settings.GA4_PROPERTY_ID}:runReport"
    body = {
        "dateRanges": [{"startDate": f"{days}daysAgo", "endDate": "today"}],
        "dimensions": [{"name": "sessionDefaultChannelGroup"}],
        "metrics": [{"name": "activeUsers"}],
        "limit": 10,
    }

    resp = requests.post(url, json=body, headers={"Authorization": f"Bearer {access_token}"})
    if not resp.ok:
        raise HTTPException(status_code=502, detail=f"GA4 API error: {resp.text}")
    return resp.json()

# app/storage/connections.py
from typing import Dict, Any
from fastapi import HTTPException

# DEMO ONLY: replace with DB later
GA_CONNECTIONS: Dict[str, Dict[str, Any]] = {}
STRIPE_CONNECTED_ACCOUNTS: Dict[str, Dict[str, Any]] = {}


def save_ga_tokens(connection_id: str, tokens: Dict[str, Any]) -> None:
    GA_CONNECTIONS[connection_id] = tokens


def get_ga_access_token(connection_id: str = "default") -> str:
    tokens = GA_CONNECTIONS.get(connection_id)
    if not tokens or "access_token" not in tokens:
        raise HTTPException(status_code=404, detail="No GA4 connection or access token")
    return tokens["access_token"]


def save_stripe_account(account_id: str, data: Dict[str, Any]) -> None:
    STRIPE_CONNECTED_ACCOUNTS[account_id] = data


def get_stripe_access_token(account_id: str) -> str:
    account = STRIPE_CONNECTED_ACCOUNTS.get(account_id)
    if not account or "access_token" not in account:
        raise HTTPException(status_code=404, detail=f"No connected Stripe account for id={account_id}")
    return account["access_token"]

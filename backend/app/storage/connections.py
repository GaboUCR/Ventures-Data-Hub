# app/storage/connections.py
from __future__ import annotations

from typing import Dict, Any, Optional, List

from fastapi import HTTPException
from sqlalchemy import select, insert, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import func

from app.db.session import engine
from app.db.tables import integration_connections

def _parse_scopes(scope_raw: Optional[str]) -> Optional[List[str]]:
    if not scope_raw:
        return None
    # GA/Google returns scope as space-separated string sometimes
    return scope_raw.split(" ")


def save_ga_tokens(
    company_id: str,
    external_account_id: str,
    tokens: Dict[str, Any],
) -> str:
    """
    Create or update a GA4 integration row in core.integration_connections.
    Returns the connection id (UUID as string).
    """
    try:
        with engine.begin() as conn:
            # Find existing GA4 connection for this company
            stmt = (
                select(integration_connections)
                .where(
                    integration_connections.c.company_id == company_id,
                    integration_connections.c.provider == "ga4",
                )
            )
            existing = conn.execute(stmt).first()

            scopes = _parse_scopes(tokens.get("scope"))
            access_token = tokens["access_token"]
            refresh_token = tokens.get("refresh_token")

            if existing:
                conn_id = existing.id
                upd = (
                    update(integration_connections)
                    .where(integration_connections.c.id == conn_id)
                    .values(
                        access_token=access_token,
                        refresh_token=refresh_token,
                        scopes=scopes,
                        status="connected",
                        updated_at=func.now(),
                    )
                    .returning(integration_connections.c.id)
                )
                result = conn.execute(upd)
                return str(result.scalar_one())

            # Insert new connection
            ins = (
                insert(integration_connections)
                .values(
                    company_id=company_id,
                    provider="ga4",
                    external_account_id=external_account_id,
                    access_token=access_token,
                    refresh_token=refresh_token,
                    scopes=scopes,
                    status="connected",
                    created_at=func.now(),
                    updated_at=func.now(),
                )
                .returning(integration_connections.c.id)
            )
            result = conn.execute(ins)
            return str(result.scalar_one())

    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"DB error saving GA tokens: {e}")

def get_ga_access_token(connection_id: str) -> str:
    """
    Look up GA4 connection by ID (UUID string) and return its access token.
    """
    try:
        with engine.begin() as conn:
            stmt = (
                select(
                    integration_connections.c.provider,
                    integration_connections.c.status,
                    integration_connections.c.access_token,
                )
                .where(integration_connections.c.id == connection_id)
            )
            row = conn.execute(stmt).first()

            if not row:
                raise HTTPException(status_code=404, detail="GA4 connection not found")
            if row.provider != "ga4" or row.status != "connected":
                raise HTTPException(status_code=404, detail="No GA4 connection or not connected")
            if not row.access_token:
                raise HTTPException(status_code=404, detail="GA4 access token missing")

            return row.access_token
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"DB error reading GA connection: {e}")


def save_stripe_account(
    company_id: str,
    account_id: str,
    data: Dict[str, Any],
) -> str:
    """
    Create or update a Stripe integration row in core.integration_connections.
    external_account_id = Stripe account id (acct_xxx).
    Returns the connection id (UUID as string).
    """
    try:
        with engine.begin() as conn:
            stmt = (
                select(integration_connections)
                .where(
                    integration_connections.c.company_id == company_id,
                    integration_connections.c.provider == "stripe",
                )
            )
            existing = conn.execute(stmt).first()

            scopes = _parse_scopes(data.get("scope"))
            access_token = data["access_token"]
            refresh_token = data.get("refresh_token")

            if existing:
                conn_id = existing.id
                upd = (
                    update(integration_connections)
                    .where(integration_connections.c.id == conn_id)
                    .values(
                        external_account_id=account_id,
                        access_token=access_token,
                        refresh_token=refresh_token,
                        scopes=scopes,
                        status="connected",
                        updated_at=func.now(),
                    )
                    .returning(integration_connections.c.id)
                )
                result = conn.execute(upd)
                return str(result.scalar_one())

            ins = (
                insert(integration_connections)
                .values(
                    company_id=company_id,
                    provider="stripe",
                    external_account_id=account_id,
                    access_token=access_token,
                    refresh_token=refresh_token,
                    scopes=scopes,
                    status="connected",
                    created_at=func.now(),
                    updated_at=func.now(),
                )
                .returning(integration_connections.c.id)
            )
            result = conn.execute(ins)
            return str(result.scalar_one())

    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"DB error saving Stripe account: {e}")

def get_stripe_access_token(connection_id: str) -> str:
    """
    Look up Stripe connection by its integration_connections.id and return the access token.
    """
    try:
        with engine.begin() as conn:
            stmt = (
                select(
                    integration_connections.c.provider,
                    integration_connections.c.status,
                    integration_connections.c.access_token,
                )
                .where(integration_connections.c.id == connection_id)
            )
            row = conn.execute(stmt).first()

            if not row:
                raise HTTPException(
                    status_code=404,
                    detail=f"No connected Stripe account for connection id={connection_id}",
                )
            if row.provider != "stripe" or row.status != "connected":
                raise HTTPException(
                    status_code=404,
                    detail=f"Stripe connection not in connected state for id={connection_id}",
                )
            if not row.access_token:
                raise HTTPException(status_code=404, detail="Stripe access token missing")

            return row.access_token

    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"DB error reading Stripe connection: {e}")


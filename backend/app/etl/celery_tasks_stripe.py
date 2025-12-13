# app/etl/celery_tasks_stripe.py
from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import select

from app.celery_app import celery_app
from app.db.session import engine
from app.db.tables import integration_connections
from app.etl.stripe_etl import sync_stripe_for_company


@celery_app.task(name="etl.stripe.sync_company", queue="etl")
def stripe_sync_company_task(company_id: str, days: int = 2) -> None:
    """
    Run Stripe ETL for a single company for the last N days.
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    sync_stripe_for_company(company_id, start_date, end_date)


@celery_app.task(name="etl.stripe.sync_all_companies", queue="etl")
def stripe_sync_all_companies_task(days: int = 2) -> None:
    """
    Fan-out task: for all connected Stripe companies, enqueue per-company tasks.
    """
    with engine.begin() as conn:
        rows = conn.execute(
            select(integration_connections.c.company_id)
            .where(integration_connections.c.provider == "stripe")
            .where(integration_connections.c.status == "connected")
        ).all()

    seen = set()
    for (company_id,) in rows:
        cid = str(company_id)
        if cid in seen:
            continue
        seen.add(cid)
        stripe_sync_company_task.delay(cid, days=days)

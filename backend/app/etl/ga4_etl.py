# app/etl/ga4_etl.py
from __future__ import annotations

import os
import random
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Dict, Iterable, List, Tuple

import requests
from sqlalchemy import delete, insert, select, update

from app.core.config import settings
from app.db.session import engine
from app.db.tables import (
    integration_connections,
    acquisition_channels_daily,
    acquisition_daily,
    acquisition_funnel_daily,
)

# -------------------------------------------------------------------
# Mock config (same pattern as stripe_etl)
# -------------------------------------------------------------------

USE_GA4_MOCK = os.getenv("STRESS_TEST_MOCK_GA4", "").lower() in ("1", "true", "yes")

# Reuse the same latency env vars as Stripe mock for simplicity
MOCK_LATENCY_MIN_MS = int(os.getenv("STRESS_TEST_MOCK_LATENCY_MIN_MS", "50"))
MOCK_LATENCY_MAX_MS = int(os.getenv("STRESS_TEST_MOCK_LATENCY_MAX_MS", "500"))


def _simulate_mock_latency() -> None:
    if not USE_GA4_MOCK:
        return
    delay_ms = random.randint(MOCK_LATENCY_MIN_MS, MOCK_LATENCY_MAX_MS)
    time.sleep(delay_ms / 1000.0)


@dataclass
class GA4Connection:
    id: str
    company_id: str
    access_token: str
    external_account_id: str  # GA property ID or mock_ga4_xxx


def _use_mock_for_connection(conn: GA4Connection) -> bool:
    """
    Use the mock GA4 implementation only when:
      - env flag STRESS_TEST_MOCK_GA4 is ON
      - AND this connection's external_account_id starts with 'mock_ga4_'
    """
    if not USE_GA4_MOCK:
        return False
    return conn.external_account_id.startswith("mock_ga4_")


# -------------------------------------------------------------------
# Connection lookup
# -------------------------------------------------------------------

def _get_ga_connections_for_companies() -> List[GA4Connection]:
    """
    Return all active GA4 connections (grouped later per company).
    """
    with engine.begin() as conn:
        stmt = (
            select(
                integration_connections.c.id,
                integration_connections.c.company_id,
                integration_connections.c.access_token,
                integration_connections.c.external_account_id,
            )
            .where(integration_connections.c.provider == "ga4")
            .where(integration_connections.c.status == "connected")
        )
        rows = conn.execute(stmt).all()

    return [
        GA4Connection(
            id=str(r.id),
            company_id=str(r.company_id),
            access_token=r.access_token,
            external_account_id=r.external_account_id,
        )
        for r in rows
    ]


def _get_ga_connection_for_company(company_id: str) -> GA4Connection | None:
    with engine.begin() as conn:
        stmt = (
            select(
                integration_connections.c.id,
                integration_connections.c.company_id,
                integration_connections.c.access_token,
                integration_connections.c.external_account_id,
            )
            .where(integration_connections.c.company_id == company_id)
            .where(integration_connections.c.provider == "ga4")
            .where(integration_connections.c.status == "connected")
        )
        row = conn.execute(stmt).first()

    if not row:
        return None

    return GA4Connection(
        id=str(row.id),
        company_id=str(row.company_id),
        access_token=row.access_token,
        external_account_id=row.external_account_id,
    )


# -------------------------------------------------------------------
# GA4 API helpers (real path)
# -------------------------------------------------------------------

def _to_ga_date(d: date) -> str:
    return d.isoformat()


def _run_ga_report_raw(access_token: str, property_id: str, body: Dict) -> Dict:
    """
    Thin wrapper around GA4 Data API runReport endpoint.

    This is the "real" GA path. In stress-test uses you will mostly hit
    the mock path instead.
    """
    url = f"https://analyticsdata.googleapis.com/v1beta/properties/{property_id}:runReport"
    resp = requests.post(
        url,
        json=body,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=30,
    )
    if not resp.ok:
        raise RuntimeError(f"GA4 API error: {resp.status_code} {resp.text}")
    return resp.json()


def _fetch_channel_and_funnel_from_ga(
    conn: GA4Connection,
    start_date: date,
    end_date: date,
) -> Tuple[List[Dict], List[Dict]]:
    """
    Real GA4 implementation.

    For now we make some reasonable assumptions; you can refine the body
    to match your actual GA4 property (custom events, etc.).

    Returns:
      - channel_rows: List[{
            date, channel, sessions, signups, new_customers, new_mrr_cents
        }]
      - funnel_rows: List[{
            date, visits, signups, started_checkout, paid
        }]
    """
    property_id = conn.external_account_id or settings.GA4_PROPERTY_ID
    if not property_id:
        raise RuntimeError("GA4 property_id is not configured for connection.")

    ga_start = _to_ga_date(start_date)
    ga_end = _to_ga_date(end_date)

    # 1) Channel breakdown: sessions + revenue per default channel group
    body_channels = {
        "dateRanges": [{"startDate": ga_start, "endDate": ga_end}],
        "dimensions": [
            {"name": "date"},
            {"name": "sessionDefaultChannelGroup"},
        ],
        "metrics": [
            {"name": "sessions"},
            # NOTE: signups + totalRevenue here are placeholders; adapt
            # to your actual GA4 property (e.g. event-scoped metrics).
            {"name": "totalRevenue"},
        ],
        "limit": 100000,
    }

    report_channels = _run_ga_report_raw(conn.access_token, property_id, body_channels)

    channel_rows: List[Dict] = []
    for row in report_channels.get("rows", []):
        dims = row["dimensionValues"]
        mets = row["metricValues"]

        d_str = dims[0]["value"]  # e.g. "20251212"
        channel = dims[1]["value"] or "Other"

        d = date(int(d_str[0:4]), int(d_str[4:6]), int(d_str[6:8]))
        sessions = int(mets[0]["value"] or 0)
        total_revenue = float(mets[1]["value"] or 0.0) if len(mets) > 1 else 0.0

        # For now:
        # - signups ~ 5% of sessions
        # - new_customers ~ 50% of signups
        signups = int(sessions * 0.05)
        new_customers = int(signups * 0.5)

        channel_rows.append(
            {
                "date": d,
                "channel": channel,
                "sessions": sessions,
                "signups": signups,
                "new_customers": new_customers,
                "new_mrr_cents": int(total_revenue * 100),
            }
        )

    # 2) Funnel view at the daily level
    body_funnel = {
        "dateRanges": [{"startDate": ga_start, "endDate": ga_end}],
        "dimensions": [{"name": "date"}],
        "metrics": [
            {"name": "activeUsers"},
        ],
        "limit": 100000,
    }

    report_funnel = _run_ga_report_raw(conn.access_token, property_id, body_funnel)

    funnel_rows_map: Dict[date, Dict[str, int]] = {}
    for row in report_funnel.get("rows", []):
        dims = row["dimensionValues"]
        mets = row["metricValues"]
        d_str = dims[0]["value"]
        d = date(int(d_str[0:4]), int(d_str[4:6]), int(d_str[6:8]))

        visits = int(mets[0]["value"] or 0)

        funnel_rows_map[d] = {
            "date": d,
            "visits": visits,
            # Naive heuristic:
            "signups": int(visits * 0.05),
            "started_checkout": int(visits * 0.02),
            "paid": int(visits * 0.01),
        }

    funnel_rows = list(funnel_rows_map.values())
    return channel_rows, funnel_rows


# -------------------------------------------------------------------
# MOCK IMPLEMENTATION (stress-test)
# -------------------------------------------------------------------

def _mock_fetch_channel_and_funnel(
    conn: GA4Connection,
    start_date: date,
    end_date: date,
) -> Tuple[List[Dict], List[Dict]]:
    """
    Generate synthetic GA4-style data per company/date/channel with
    stochastic latency + random values.

    This is used when:
       STRESS_TEST_MOCK_GA4=1
    AND external_account_id starts with 'mock_ga4_' (seeded stress-test companies).
    """
    _simulate_mock_latency()

    channels = ["Organic Search", "Paid Search", "Direct", "Referral"]
    channel_rows: List[Dict] = []
    funnel_rows: List[Dict] = []

    current = start_date
    while current <= end_date:
        # Funnel base
        base_visits = random.randint(200, 2000)

        day_signups = 0
        day_new_customers = 0
        day_mrr_cents = 0

        # Per channel metrics
        for ch in channels:
            # Split base_visits roughly across channels
            sessions = int(base_visits * random.uniform(0.1, 0.4))
            signups = int(sessions * random.uniform(0.03, 0.12))
            new_customers = int(signups * random.uniform(0.3, 0.8))
            avg_mrr = random.randint(4000, 20000)  # in cents
            new_mrr_cents = new_customers * avg_mrr

            day_signups += signups
            day_new_customers += new_customers
            day_mrr_cents += new_mrr_cents

            channel_rows.append(
                {
                    "date": current,
                    "channel": ch,
                    "sessions": sessions,
                    "signups": signups,
                    "new_customers": new_customers,
                    "new_mrr_cents": new_mrr_cents,
                }
            )

        # Funnel shape: visits >= signups >= started_checkout >= paid
        visits = base_visits
        signups = day_signups
        started_checkout = int(signups * random.uniform(0.4, 0.8))
        paid = int(started_checkout * random.uniform(0.4, 0.9))

        funnel_rows.append(
            {
                "date": current,
                "visits": visits,
                "signups": signups,
                "started_checkout": started_checkout,
                "paid": paid,
            }
        )

        current += timedelta(days=1)

    return channel_rows, funnel_rows


# -------------------------------------------------------------------
# Transform + Load (shared between real + mock)
# -------------------------------------------------------------------

def _upsert_acquisition_channels_daily(
    company_id: str,
    rows: List[Dict],
) -> None:
    if not rows:
        return

    dates = {r["date"] for r in rows}
    min_date, max_date = min(dates), max(dates)

    with engine.begin() as conn:
        conn.execute(
            delete(acquisition_channels_daily)
            .where(acquisition_channels_daily.c.company_id == company_id)
            .where(acquisition_channels_daily.c.date >= min_date)
            .where(acquisition_channels_daily.c.date <= max_date)
        )

        conn.execute(
            insert(acquisition_channels_daily),
            [
                {
                    "company_id": company_id,
                    "date": r["date"],
                    "channel": r["channel"],
                    "sessions": r["sessions"],
                    "signups": r["signups"],
                    "new_customers": r["new_customers"],
                    "new_mrr_cents": r["new_mrr_cents"],
                }
                for r in rows
            ],
        )


def _upsert_acquisition_daily(
    company_id: str,
    channel_rows: List[Dict],
) -> None:
    """
    Aggregate per date across channels into acquisition_daily
    with channel_group='All'.
    """
    per_day: Dict[date, Dict[str, int]] = {}
    for r in channel_rows:
        day = r["date"]
        bucket = per_day.setdefault(
            day,
            {
                "sessions": 0,
                "signups": 0,
                "new_customers": 0,
                "new_mrr_cents": 0,
            },
        )

        bucket["sessions"] += r["sessions"]
        bucket["signups"] += r["signups"]
        bucket["new_customers"] += r["new_customers"]
        bucket["new_mrr_cents"] += r["new_mrr_cents"]

    if not per_day:
        return

    dates = list(per_day.keys())
    min_date, max_date = min(dates), max(dates)

    with engine.begin() as conn:
        conn.execute(
            delete(acquisition_daily)
            .where(acquisition_daily.c.company_id == company_id)
            .where(acquisition_daily.c.date >= min_date)
            .where(acquisition_daily.c.date <= max_date)
        )

        conn.execute(
            insert(acquisition_daily),
            [
                {
                    "company_id": company_id,
                    "date": day,
                    "channel_group": "All",
                    "sessions": vals["sessions"],
                    "signups": vals["signups"],
                    "new_customers": vals["new_customers"],
                    "new_mrr_cents": vals["new_mrr_cents"],
                }
                for day, vals in per_day.items()
            ],
        )


def _upsert_acquisition_funnel_daily(
    company_id: str,
    funnel_rows: List[Dict],
) -> None:
    if not funnel_rows:
        return

    dates = {r["date"] for r in funnel_rows}
    min_date, max_date = min(dates), max(dates)

    with engine.begin() as conn:
        conn.execute(
            delete(acquisition_funnel_daily)
            .where(acquisition_funnel_daily.c.company_id == company_id)
            .where(acquisition_funnel_daily.c.date >= min_date)
            .where(acquisition_funnel_daily.c.date <= max_date)
        )

        conn.execute(
            insert(acquisition_funnel_daily),
            [
                {
                    "company_id": company_id,
                    "date": r["date"],
                    "visits": r["visits"],
                    "signups": r["signups"],
                    "started_checkout": r["started_checkout"],
                    "paid": r["paid"],
                }
                for r in funnel_rows
            ],
        )


def _update_last_synced(connection_id: str) -> None:
    with engine.begin() as conn:
        conn.execute(
            update(integration_connections)
            .where(integration_connections.c.id == connection_id)
            .values(last_synced_at=datetime.utcnow())
        )


# -------------------------------------------------------------------
# Public ETL entrypoints
# -------------------------------------------------------------------

def sync_ga_for_company(
    company_id: str,
    start_date: date,
    end_date: date,
) -> None:
    """
    End-to-end GA4 ETL for a single company and date range.
    Idempotent over [start_date, end_date].

    Uses either the real GA4 API or the mock generator depending
    on env flag + external_account_id.
    """
    conn_info = _get_ga_connection_for_company(company_id)
    if not conn_info:
        print(f"[ga4_etl] No active GA4 connection for company {company_id}, skipping.")
        return

    print(
        f"[ga4_etl] Syncing GA4 for company {company_id} "
        f"from {start_date} to {end_date} "
        f"(mock={_use_mock_for_connection(conn_info)})…"
    )

    if _use_mock_for_connection(conn_info):
        channel_rows, funnel_rows = _mock_fetch_channel_and_funnel(
            conn_info, start_date, end_date
        )
    else:
        channel_rows, funnel_rows = _fetch_channel_and_funnel_from_ga(
            conn_info, start_date, end_date
        )

    _upsert_acquisition_channels_daily(company_id, channel_rows)
    _upsert_acquisition_daily(company_id, channel_rows)
    _upsert_acquisition_funnel_daily(company_id, funnel_rows)
    _update_last_synced(conn_info.id)

    print(f"[ga4_etl] Done for company {company_id}.")


def sync_ga_for_all_companies(
    days: int = 30,
) -> None:
    """
    Convenience helper: sync last N days for all companies
    with a GA4 connection.
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    conns = _get_ga_connections_for_companies()
    seen_companies = set()
    for conn_info in conns:
        if conn_info.company_id in seen_companies:
            continue
        seen_companies.add(conn_info.company_id)
        sync_ga_for_company(conn_info.company_id, start_date, end_date)

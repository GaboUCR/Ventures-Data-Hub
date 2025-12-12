# app/etl/stripe_etl.py
from __future__ import annotations

import os
import random
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Dict, Iterable, List, Tuple

import stripe
import app.etl.stripe_etl as stripe_etl
from sqlalchemy import delete, insert, select, update
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.db.session import engine
from app.db.tables import (
    integration_connections,
    billing_daily,
    billing_past_due_invoices,
    customer_metrics,
    company_monthly_metrics,
    plan_monthly_metrics,
    retention_cohorts,  
)

from typing import DefaultDict
from collections import defaultdict

stripe.api_key = settings.STRIPE_SECRET_KEY

# We keep the same pattern as app/integrations/stripe_oauth.py
stripe_etl.api_key = settings.STRIPE_SECRET_KEY



@dataclass
class StripeConnection:
    id: str
    company_id: str
    access_token: str
    external_account_id: str  # acct_xxx
    currency: str | None = None  # We can infer default currency from invoices later


# ---------- Helpers: connection lookup ----------

def _add_months(month_start: date, months: int) -> date:
    """
    Add a number of whole months to a 'month start' date (YYYY-MM-01).
    """
    year = month_start.year + (month_start.month - 1 + months) // 12
    month = (month_start.month - 1 + months) % 12 + 1
    return date(year, month, 1)


def _get_stripe_connections_for_companies() -> List[StripeConnection]:
    """
    Return all active Stripe connections (grouped later per company).
    """
    with engine.begin() as conn:
        stmt = (
            select(
                integration_connections.c.id,
                integration_connections.c.company_id,
                integration_connections.c.access_token,
                integration_connections.c.external_account_id,
            )
            .where(integration_connections.c.provider == "stripe")
            .where(integration_connections.c.status == "connected")
        )
        rows = conn.execute(stmt).all()

    return [
        StripeConnection(
            id=str(r.id),
            company_id=str(r.company_id),
            access_token=r.access_token,
            external_account_id=r.external_account_id,
        )
        for r in rows
    ]


def _get_stripe_connection_for_company(company_id: str) -> StripeConnection | None:
    with engine.begin() as conn:
        stmt = (
            select(
                integration_connections.c.id,
                integration_connections.c.company_id,
                integration_connections.c.access_token,
                integration_connections.c.external_account_id,
            )
            .where(integration_connections.c.company_id == company_id)
            .where(integration_connections.c.provider == "stripe")
            .where(integration_connections.c.status == "connected")
        )
        row = conn.execute(stmt).first()

    if not row:
        return None

    return StripeConnection(
        id=str(row.id),
        company_id=str(row.company_id),
        access_token=row.access_token,
        external_account_id=row.external_account_id,
    )


# ---------- Helpers: Stripe fetch ----------

def _unix_range(start: date, end: date) -> Tuple[int, int]:
    """
    Stripe uses unix timestamps. We treat end as inclusive day and add +1 day.
    """
    start_dt = datetime.combine(start, datetime.min.time(), tzinfo=timezone.utc)
    end_dt = datetime.combine(end + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
    return int(start_dt.timestamp()), int(end_dt.timestamp())


def _list_charges_for_range(conn: StripeConnection, start: date, end: date):
    """
    List all charges in [start, end]. Uses real Stripe OR mock depending on
    connection and env flag.
    """
    if _use_mock_for_connection(conn):
        return _mock_list_charges_for_range(conn, start, end)

    from stripe import Charge

    created_gte, created_lt = _unix_range(start, end)
    charges = Charge.auto_paging_iter(
        api_key=conn.access_token,
        created={"gte": created_gte, "lt": created_lt},
    )
    return list(charges)

def _list_invoices_for_range(conn: StripeConnection, start: date, end: date):
    if _use_mock_for_connection(conn):
        return _mock_list_invoices_for_range(conn, start, end)

    from stripe import Invoice

    created_gte, created_lt = _unix_range(start, end)
    invoices = Invoice.auto_paging_iter(
        api_key=conn.access_token,
        created={"gte": created_gte, "lt": created_lt},
    )
    return list(invoices)


def _list_subscriptions_for_range(conn: StripeConnection, start: date, end: date):
    from backend.app.etl.stripe_etl import Subscription

    created_gte, created_lt = _unix_range(start, end)
    subs = Subscription.auto_paging_iter(
        api_key=conn.access_token,
        created={"gte": created_gte, "lt": created_lt},
    )
    return list(subs)


def _list_customers(conn: StripeConnection):
    if _use_mock_for_connection(conn):
        return _mock_list_customers(conn)

    from stripe import Customer

    customers = Customer.auto_paging_iter(api_key=conn.access_token)
    return list(customers)


# ---------- Transform: billing_daily + past_due + customer_metrics ----------

def _group_charges_by_day(charges: Iterable) -> Dict[date, Dict[str, int]]:
    """
    Build per-day aggregates:
      - payment_attempts
      - payment_success
      - payment_failed
      - refunds_cents
    """
    per_day: Dict[date, Dict[str, int]] = {}
    for ch in charges:
        created_ts = datetime.fromtimestamp(ch["created"], tz=timezone.utc).date()
        day = created_ts
        bucket = per_day.setdefault(
            day,
            {
                "payment_attempts": 0,
                "payment_success": 0,
                "payment_failed": 0,
                "refunds_cents": 0,
            },
        )

        bucket["payment_attempts"] += 1

        status = ch.get("status")
        paid = ch.get("paid", False)
        amount_refunded = int(ch.get("amount_refunded") or 0)

        if paid and status == "succeeded":
            bucket["payment_success"] += 1
        else:
            bucket["payment_failed"] += 1

        if amount_refunded > 0:
            bucket["refunds_cents"] += amount_refunded

    return per_day


def _get_past_due_invoices(invoices: Iterable) -> List[Dict]:
    """
    Return invoices that are past due / uncollectible.
    """
    results: List[Dict] = []
    for inv in invoices:
        status = inv.get("status")
        due_date_unix = inv.get("due_date") or inv.get("due_at")
        if not due_date_unix:
            continue

        due_dt = datetime.fromtimestamp(due_date_unix, tz=timezone.utc).date()
        # Past due = due date in the past AND invoice not fully paid
        if status in ("open", "uncollectible", "past_due") and due_dt < date.today():
            customer = inv.get("customer_details", {}) or {}
            results.append(
                {
                    "invoice_id": inv["id"],
                    "amount_cents": int(inv.get("amount_remaining") or inv.get("amount_due") or 0),
                    "currency": (inv.get("currency") or "usd").upper(),
                    "due_date": due_dt,
                    "customer_name": customer.get("name"),
                    "customer_email": customer.get("email"),
                }
            )
    return results


def _build_customer_metrics(
    charges: Iterable,
    invoices: Iterable,
    customers: Iterable,
) -> Dict[str, Dict]:
    """
    Build a map customer_id -> customer_metrics row values.
    Very simple heuristic:
      - lifetime_revenue_cents = sum of successful charge amounts for that customer
      - current_mrr_cents: derived very roughly from recent invoices (e.g. last invoice / 12 for annual, etc.)
      - status: active if had successful charge in last 90 days, else churned
    """
    customer_info: Dict[str, Dict] = {}
    # Seed with Stripe customer objects
    for c in customers:
        customer_info.setdefault(
            c["id"],
            {
                "email": c.get("email"),
                "name": c.get("name"),
                "lifetime_revenue_cents": 0,
                "current_mrr_cents": 0,
                "first_seen_at": None,
                "last_activity_at": None,
                "status": "churned",
            },
        )

    # Aggregate from charges
    for ch in charges:
        cust_id = ch.get("customer")
        if not cust_id:
            continue
        obj = customer_info.setdefault(
            cust_id,
            {
                "email": None,
                "name": None,
                "lifetime_revenue_cents": 0,
                "current_mrr_cents": 0,
                "first_seen_at": None,
                "last_activity_at": None,
                "status": "churned",
            },
        )
        created_at = datetime.fromtimestamp(ch["created"], tz=timezone.utc)
        amount = int(ch.get("amount") or 0)
        paid = ch.get("paid", False)
        status = ch.get("status")

        if paid and status == "succeeded":
            obj["lifetime_revenue_cents"] += amount

        if obj["first_seen_at"] is None or created_at < obj["first_seen_at"]:
            obj["first_seen_at"] = created_at
        if obj["last_activity_at"] is None or created_at > obj["last_activity_at"]:
            obj["last_activity_at"] = created_at

    # Heuristic current_mrr: use latest invoice amount if it's recurring
    for inv in invoices:
        cust_id = inv.get("customer")
        if not cust_id:
            continue
        obj = customer_info.setdefault(
            cust_id,
            {
                "email": None,
                "name": None,
                "lifetime_revenue_cents": 0,
                "current_mrr_cents": 0,
                "first_seen_at": None,
                "last_activity_at": None,
                "status": "churned",
            },
        )
        created_at = datetime.fromtimestamp(inv["created"], tz=timezone.utc)
        amount_due = int(inv.get("amount_due") or 0)
        # Very naive: treat monthly invoices as MRR, yearly as amount / 12
        # We could inspect invoice lines price.recurring.interval
        interval = "month"
        lines = inv.get("lines", {}).get("data", [])
        for line in lines:
            price = (line.get("price") or {})
            recurring = price.get("recurring") or {}
            if recurring.get("interval") == "year":
                interval = "year"
                break

        if interval == "year":
            mrr = amount_due // 12
        else:
            mrr = amount_due

        # Keep the most recent invoice as the "current" MRR
        if obj["last_activity_at"] is None or created_at >= obj["last_activity_at"]:
            obj["current_mrr_cents"] = max(obj["current_mrr_cents"], mrr)
            obj["last_activity_at"] = created_at

    # Status based on last_activity_at
    ninety_days_ago = datetime.now(timezone.utc) - timedelta(days=90)
    for cust_id, obj in customer_info.items():
        last = obj["last_activity_at"]
        if last and last >= ninety_days_ago:
            obj["status"] = "active"
        else:
            obj["status"] = "churned"

    # is_high_value flag based on lifetime revenue threshold (e.g. >= $5,000)
    result: Dict[str, Dict] = {}
    for cust_id, obj in customer_info.items():
        lifetime = int(obj["lifetime_revenue_cents"])
        result[cust_id] = {
            "customer_id": cust_id,
            "email": obj["email"],
            "name": obj["name"],
            "current_mrr_cents": int(obj["current_mrr_cents"]),
            "lifetime_revenue_cents": lifetime,
            "first_seen_at": obj["first_seen_at"],
            "last_activity_at": obj["last_activity_at"],
            "status": obj["status"],
            "is_high_value": lifetime >= 500_000,  # $5,000
        }
    return result


def _compute_company_monthly_metrics(
    company_id: str,
    invoices: Iterable,
) -> Dict[Tuple[date, str], Dict]:
    """
    Rough monthly aggregation to populate analytics.company_monthly_metrics.
    Key by (month_start, currency).
    """
    per_month: Dict[Tuple[date, str], Dict] = {}
    for inv in invoices:
        created_dt = datetime.fromtimestamp(inv["created"], tz=timezone.utc)
        month_start = date(created_dt.year, created_dt.month, 1)
        currency = (inv.get("currency") or "usd").upper()
        key = (month_start, currency)
        bucket = per_month.setdefault(
            key,
            {
                "mrr_cents": 0,
                "arr_cents": 0,
                "new_mrr_cents": 0,
                "expansion_mrr_cents": 0,
                "contraction_mrr_cents": 0,
                "churned_mrr_cents": 0,
                "nrr_percent": None,
                "active_customers": 0,
                "churn_rate_percent": None,
                "customer_ids": set(),
            },
        )

        amount = int(inv.get("amount_due") or 0)
        bucket["mrr_cents"] += amount
        bucket["arr_cents"] = bucket["mrr_cents"] * 12
        cust_id = inv.get("customer")
        if cust_id:
            bucket["customer_ids"].add(cust_id)

    # Post-process counts
    for (_month_start, _currency), bucket in per_month.items():
        bucket["active_customers"] = len(bucket["customer_ids"])
        bucket.pop("customer_ids", None)

    # Wrap with company_id
    result: Dict[Tuple[date, str], Dict] = {}
    for (month_start, currency), bucket in per_month.items():
        result[(month_start, currency)] = {
            "company_id": company_id,
            "month": month_start,
            "currency": currency,
            **bucket,
        }
    return result

def _compute_retention_cohorts(
    company_id: str,
    invoices: Iterable,
) -> List[Dict]:
    """
    Build retention cohorts from invoice history.

    Heuristic:
      - Cohort month = month of the customer's *first* paid/open invoice
      - MRR in a month = sum of invoice.amount_due for that customer in that month
      - For each cohort & month offset:
          * mrr_retained_percent = current_mrr / cohort_mrr_month0 * 100
          * customer_retained_percent = active_customers / cohort_size * 100

    Works for both real and mock Stripe invoices, as long as they have:
      - 'customer'
      - 'created' (unix timestamp)
      - 'status' ('paid' or 'open' counted)
      - 'amount_due'
    """
    # ---- 1) Build per-customer monthly MRR & cohort month ----
    customers: Dict[str, Dict] = {}
    all_months: set[date] = set()

    for inv in invoices:
        status = inv.get("status")
        if status not in ("paid", "open"):
            continue

        cust_id = inv.get("customer")
        if not cust_id:
            continue

        amount_due = int(inv.get("amount_due") or 0)
        if amount_due <= 0:
            continue

        created_ts = inv.get("created")
        if created_ts is None:
            continue

        created_dt = datetime.fromtimestamp(created_ts, tz=timezone.utc)
        month_start = date(created_dt.year, created_dt.month, 1)

        info = customers.setdefault(
            cust_id,
            {
                "cohort_month": month_start,
                "per_month_mrr": defaultdict(int),
            },
        )

        # earliest month = cohort month
        if month_start < info["cohort_month"]:
            info["cohort_month"] = month_start

        info["per_month_mrr"][month_start] += amount_due
        all_months.add(month_start)

    if not customers:
        return []

    last_month_overall = max(all_months)

    # ---- 2) Group customers into cohorts and compute base (month 0) MRR ----
    cohorts: Dict[date, Dict] = {}
    for cust_id, info in customers.items():
        cohort_month = info["cohort_month"]
        cohort = cohorts.setdefault(
            cohort_month,
            {
                "customers": set(),
                "base_mrr_cents": 0,
            },
        )
        cohort["customers"].add(cust_id)
        cohort["base_mrr_cents"] += info["per_month_mrr"].get(cohort_month, 0)

    # ---- 3) For each cohort, compute retention over time ----
    rows: List[Dict] = []

    for cohort_month, cohort in cohorts.items():
        cohort_customer_ids = list(cohort["customers"])
        cohort_size = len(cohort_customer_ids)
        base_mrr = int(cohort["base_mrr_cents"] or 0)

        if cohort_size == 0:
            continue

        # We still emit customer_retained even when base_mrr == 0;
        # in that case mrr_retained_percent will be None.
        months_since = 0
        cur_month = cohort_month

        while cur_month <= last_month_overall:
            month_mrr = 0
            active_customers = 0

            for cust_id in cohort_customer_ids:
                cust_info = customers[cust_id]
                mrr_for_month = int(cust_info["per_month_mrr"].get(cur_month, 0))
                if mrr_for_month > 0:
                    active_customers += 1
                    month_mrr += mrr_for_month

            mrr_pct = None
            if base_mrr > 0:
                mrr_pct = (month_mrr / base_mrr) * 100.0

            cust_pct = (active_customers / cohort_size) * 100.0

            rows.append(
                {
                    "company_id": company_id,
                    "cohort_month": cohort_month,
                    "months_since_signup": months_since,
                    "mrr_retained_percent": round(mrr_pct, 2) if mrr_pct is not None else None,
                    "customer_retained_percent": round(cust_pct, 2),
                }
            )

            months_since += 1
            cur_month = _add_months(cohort_month, months_since)

    return rows


# ---------- Load: into analytics tables (idempotent) ----------

def _upsert_billing_daily(company_id: str, aggregates: Dict[date, Dict[str, int]]) -> None:
    with engine.begin() as conn:
        if not aggregates:
            return
        dates = list(aggregates.keys())
        min_date, max_date = min(dates), max(dates)

        # Delete existing rows in date window
        conn.execute(
            delete(billing_daily)
            .where(billing_daily.c.company_id == company_id)
            .where(billing_daily.c.date >= min_date)
            .where(billing_daily.c.date <= max_date)
        )

        rows = []
        for day, vals in aggregates.items():
            rows.append(
                {
                    "company_id": company_id,
                    "date": day,
                    "payment_attempts": vals["payment_attempts"],
                    "payment_success": vals["payment_success"],
                    "payment_failed": vals["payment_failed"],
                    "refunds_cents": vals["refunds_cents"],
                    # For now, MRR at risk is zero; later we can tie to open invoices.
                    "mrr_at_risk_cents": 0,
                }
            )

        if rows:
            conn.execute(insert(billing_daily), rows)


def _upsert_past_due_invoices(company_id: str, invoices_data: List[Dict]) -> None:
    with engine.begin() as conn:
        # Clear all past due invoices for this company (snapshot table)
        conn.execute(
            delete(billing_past_due_invoices)
            .where(billing_past_due_invoices.c.company_id == company_id)
        )

        rows = [
            {
                "company_id": company_id,
                "invoice_id": row["invoice_id"],
                "customer_name": row.get("customer_name"),
                "customer_email": row.get("customer_email"),
                "amount_cents": row["amount_cents"],
                "currency": row["currency"],
                "due_date": row["due_date"],
            }
            for row in invoices_data
        ]
        if rows:
            conn.execute(insert(billing_past_due_invoices), rows)


def _upsert_customer_metrics(company_id: str, customers_map: Dict[str, Dict]) -> None:
    with engine.begin() as conn:
        # Replace all metrics for this company (we can optimize later)
        conn.execute(
            delete(customer_metrics)
            .where(customer_metrics.c.company_id == company_id)
        )

        rows = []
        for cust_id, data in customers_map.items():
            rows.append(
                {
                    "company_id": company_id,
                    "customer_id": cust_id,
                    "email": data["email"],
                    "name": data["name"],
                    "current_mrr_cents": data["current_mrr_cents"],
                    "lifetime_revenue_cents": data["lifetime_revenue_cents"],
                    "first_seen_at": data["first_seen_at"],
                    "last_activity_at": data["last_activity_at"],
                    "status": data["status"],
                    "is_high_value": data["is_high_value"],
                }
            )

        if rows:
            conn.execute(insert(customer_metrics), rows)


def _upsert_company_monthly_metrics(
    company_id: str,
    monthly_map: Dict[Tuple[date, str], Dict],
) -> None:
    if not monthly_map:
        return

    months = [k[0] for k in monthly_map.keys()]
    min_month, max_month = min(months), max(months)

    with engine.begin() as conn:
        conn.execute(
            delete(company_monthly_metrics)
            .where(company_monthly_metrics.c.company_id == company_id)
            .where(company_monthly_metrics.c.month >= min_month)
            .where(company_monthly_metrics.c.month <= max_month)
        )

        rows = list(monthly_map.values())
        if rows:
            conn.execute(insert(company_monthly_metrics), rows)

def _upsert_retention_cohorts(
    company_id: str,
    rows: List[Dict],
) -> None:
    """
    Idempotent load into analytics.retention_cohorts.

    We delete existing rows for this company whose cohort_month
    is in the min/max range of the new rows, then insert fresh.
    """
    if not rows:
        return

    cohort_months = {r["cohort_month"] for r in rows}
    min_cohort = min(cohort_months)
    max_cohort = max(cohort_months)

    with engine.begin() as conn:
        conn.execute(
            delete(retention_cohorts)
            .where(retention_cohorts.c.company_id == company_id)
            .where(retention_cohorts.c.cohort_month >= min_cohort)
            .where(retention_cohorts.c.cohort_month <= max_cohort)
        )
        conn.execute(insert(retention_cohorts), rows)


def _update_last_synced(connection_id: str) -> None:
    try:
        with engine.begin() as conn:
            conn.execute(
                update(integration_connections)
                .where(integration_connections.c.id == connection_id)
                .values(last_synced_at=datetime.now(timezone.utc))
            )
    except SQLAlchemyError:
        # Non-fatal
        return


# ---------- Public ETL entrypoints ----------

def sync_stripe_for_company(
    company_id: str,
    start_date: date,
    end_date: date,
) -> None:
    """
    End-to-end Stripe ETL for a single company and date range.
    Idempotent over [start_date, end_date].
    """
    conn_info = _get_stripe_connection_for_company(company_id)
    if not conn_info:
        print(f"[stripe_etl] No active Stripe connection for company {company_id}, skipping.")
        return

    print(f"[stripe_etl] Syncing Stripe for company {company_id} from {start_date} to {end_date}…")

    charges = _list_charges_for_range(conn_info, start_date, end_date)
    invoices = _list_invoices_for_range(conn_info, start_date, end_date)
    customers = _list_customers(conn_info)

    billing_per_day = _group_charges_by_day(charges)
    past_due = _get_past_due_invoices(invoices)
    customer_map = _build_customer_metrics(charges, invoices, customers)
    monthly_map = _compute_company_monthly_metrics(company_id, invoices)
    plan_rows = _compute_plan_monthly_metrics(company_id, invoices)
    cohort_rows = _compute_retention_cohorts(company_id, invoices) 

    _upsert_billing_daily(company_id, billing_per_day)
    _upsert_past_due_invoices(company_id, past_due)
    _upsert_customer_metrics(company_id, customer_map)
    _upsert_company_monthly_metrics(company_id, monthly_map)
    _upsert_plan_monthly_metrics(company_id, plan_rows) 
    _update_last_synced(conn_info.id)
    _upsert_retention_cohorts(company_id, cohort_rows) 

    print(f"[stripe_etl] Done for company {company_id}.")


def sync_stripe_for_all_companies(
    days: int = 30,
) -> None:
    """
    Convenience helper: sync last N days for all companies with a Stripe connection.
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    conns = _get_stripe_connections_for_companies()
    seen_companies = set()
    for conn_info in conns:
        if conn_info.company_id in seen_companies:
            continue
        seen_companies.add(conn_info.company_id)
        sync_stripe_for_company(conn_info.company_id, start_date, end_date)

def _compute_plan_monthly_metrics(
    company_id: str,
    invoices: Iterable,
) -> List[Dict]:
    """
    Aggregate invoices into analytics.plan_monthly_metrics rows.

    - Groups by (month_start, plan_id, currency)
    - Derives MRR from invoice line amounts and recurring interval
    - Counts distinct customers per (month, plan) as 'subscribers'
    - Then computes growth_rate_percent & churn_rate_percent by plan over time
    """
    # key: (month_start, plan_id, currency) -> bucket
    per_bucket: Dict[Tuple[date, str, str], Dict] = {}

    for inv in invoices:
        created_ts = inv.get("created")
        if not created_ts:
            continue

        created_dt = datetime.fromtimestamp(created_ts, tz=timezone.utc)
        month_start = date(created_dt.year, created_dt.month, 1)

        inv_currency = (inv.get("currency") or "usd").upper()
        cust_id = inv.get("customer")

        lines = (inv.get("lines") or {}).get("data", [])
        if not lines:
            # Fallback: treat the whole invoice as one "unknown plan"
            lines = [
                {
                    "price": {
                        "id": "price_unknown",
                        "nickname": "Unknown Plan",
                        "currency": inv_currency,
                        "recurring": {"interval": "month"},
                    },
                    "amount": inv.get("amount_due") or 0,
                }
            ]

        for line in lines:
            price = line.get("price") or {}
            plan_id = price.get("id") or "price_unknown"
            plan_name = price.get("nickname") or plan_id
            recurring = price.get("recurring") or {}
            interval = recurring.get("interval") or "month"
            line_currency = (price.get("currency") or inv_currency).upper()

            key = (month_start, plan_id, line_currency)

            bucket = per_bucket.setdefault(
                key,
                {
                    "company_id": company_id,
                    "plan_id": plan_id,
                    "plan_name": plan_name,
                    "month": month_start,
                    "currency": line_currency,
                    "mrr_cents": 0,
                    "subscribers": 0,  # set later
                    "churn_rate_percent": None,
                    "growth_rate_percent": None,
                    "_customer_ids": set(),
                },
            )

            amount_line = int(
                line.get("amount")
                or line.get("amount_excluding_tax")
                or inv.get("amount_due")
                or 0
            )

            if interval == "year":
                mrr = amount_line // 12
            else:
                mrr = amount_line

            bucket["mrr_cents"] += mrr
            if cust_id:
                bucket["_customer_ids"].add(cust_id)

    if not per_bucket:
        return []

    # subscribers per bucket
    for bucket in per_bucket.values():
        bucket["subscribers"] = len(bucket["_customer_ids"])
        bucket.pop("_customer_ids", None)

    # compute growth/churn per plan across months
    # group by (plan_id, currency)
    by_plan: DefaultDict[Tuple[str, str], List[Dict]] = defaultdict(list)
    for (month_start, plan_id, currency), bucket in per_bucket.items():
        by_plan[(plan_id, currency)].append(bucket)

    for (_plan_id, _currency), buckets in by_plan.items():
        buckets.sort(key=lambda b: b["month"])
        prev_mrr = None
        for bucket in buckets:
            curr_mrr = bucket["mrr_cents"]
            if prev_mrr and prev_mrr > 0:
                growth = (curr_mrr - prev_mrr) / prev_mrr * 100
                bucket["growth_rate_percent"] = round(growth, 2)

                if curr_mrr < prev_mrr:
                    churn = (prev_mrr - curr_mrr) / prev_mrr * 100
                    bucket["churn_rate_percent"] = round(churn, 2)
                else:
                    bucket["churn_rate_percent"] = 0.0
            else:
                bucket["growth_rate_percent"] = None
                bucket["churn_rate_percent"] = None
            prev_mrr = curr_mrr

    # Flatten to list
    return list(per_bucket.values())

def _upsert_plan_monthly_metrics(
    company_id: str,
    rows: List[Dict],
) -> None:
    """
    Idempotent upsert: delete existing rows for this company/month window
    and reinsert the new ones.
    """
    if not rows:
        return

    months = [r["month"] for r in rows]
    min_month, max_month = min(months), max(months)

    with engine.begin() as conn:
        conn.execute(
            delete(plan_monthly_metrics)
            .where(plan_monthly_metrics.c.company_id == company_id)
            .where(plan_monthly_metrics.c.month >= min_month)
            .where(plan_monthly_metrics.c.month <= max_month)
        )

        conn.execute(insert(plan_monthly_metrics), rows)


# --- NEW: stress-test / mock config ---

USE_STRIPE_MOCK = os.getenv("STRESS_TEST_MOCK_STRIPE", "").lower() in ("1", "true", "yes")

MOCK_LATENCY_MIN_MS = int(os.getenv("STRESS_TEST_MOCK_LATENCY_MIN_MS", "50"))
MOCK_LATENCY_MAX_MS = int(os.getenv("STRESS_TEST_MOCK_LATENCY_MAX_MS", "500"))


def _simulate_mock_latency() -> None:
    if not USE_STRIPE_MOCK:
        return
    delay_ms = random.randint(MOCK_LATENCY_MIN_MS, MOCK_LATENCY_MAX_MS)
    time.sleep(delay_ms / 1000.0)


@dataclass
class StripeConnection:
    id: str
    company_id: str
    access_token: str
    external_account_id: str  # acct_xxx or mock_stripe_xxx
    currency: str | None = None


def _use_mock_for_connection(conn: StripeConnection) -> bool:
    """
    Return True if this connection should use the stress-test mock instead of
    real Stripe. We only mock when:
      - The env flag is ON, AND
      - The external_account_id has the stress-test prefix.
    """
    if not USE_STRIPE_MOCK:
        return False
    return conn.external_account_id.startswith("mock_stripe_")

# --- MOCK IMPLEMENTATION ---

def _mock_list_charges_for_range(conn: StripeConnection, start: date, end: date) -> List[dict]:
    """
    Mock Stripe charges: generate some fake charges per day, with random
    outcomes. We also sleep a random amount to simulate network latency.
    """
    _simulate_mock_latency()

    charges: List[dict] = []
    current = start
    while current <= end:
        # random number of charges per day
        n = random.randint(5, 30)
        for _ in range(n):
            created_dt = datetime.combine(current, datetime.min.time(), tzinfo=timezone.utc)
            created_ts = int(created_dt.timestamp()) + random.randint(0, 23 * 3600)
            amount = random.randint(1000, 50000)  # in cents
            paid = random.random() < 0.9
            status = "succeeded" if paid else "failed"
            amount_refunded = 0
            # Some refunded
            if paid and random.random() < 0.05:
                amount_refunded = random.randint(0, amount)

            charges.append(
                {
                    "id": f"ch_mock_{conn.external_account_id}_{created_ts}_{random.randint(1, 1_000_000)}",
                    "created": created_ts,
                    "paid": paid,
                    "status": status,
                    "amount": amount,
                    "amount_refunded": amount_refunded,
                    "customer": f"cus_mock_{random.randint(1, 50)}",
                }
            )
        current += timedelta(days=1)

    return charges


def _mock_list_invoices_for_range(conn: StripeConnection, start: date, end: date) -> List[dict]:
    """
    Mock invoices: a few per day, some past due, mostly monthly subscriptions.
    Each invoice is associated with a single 'plan' via price.id / nickname.
    """
    _simulate_mock_latency()

    invoices: List[dict] = []
    current = start

    # Define a few fake plans per company
    plan_defs = [
        ("basic", "Basic"),
        ("pro", "Pro"),
        ("enterprise", "Enterprise"),
    ]

    while current <= end:
        n = random.randint(2, 10)
        for _ in range(n):
            created_dt = datetime.combine(current, datetime.min.time(), tzinfo=timezone.utc)
            created_ts = int(created_dt.timestamp()) + random.randint(0, 23 * 3600)

            # Choose a plan
            plan_code, plan_label = random.choices(
                population=plan_defs,
                weights=[0.6, 0.3, 0.1],  # mostly Basic / Pro
                k=1,
            )[0]

            price_id = f"price_{conn.external_account_id}_{plan_code}"
            plan_name = f"{plan_label} Plan"

            amount_due = random.randint(2000, 20000)
            currency = "usd"

            # 10% chance of being late
            is_late = random.random() < 0.1
            due_date = current - timedelta(days=random.randint(1, 10)) if is_late else current + timedelta(days=14)
            status = "open" if is_late else "paid"

            cust_id = f"cus_mock_{random.randint(1, 50)}"

            line_amount = amount_due  # one line per invoice for simplicity

            invoices.append(
                {
                    "id": f"in_mock_{conn.external_account_id}_{created_ts}_{random.randint(1, 1_000_000)}",
                    "created": created_ts,
                    "status": status,
                    "amount_due": amount_due,
                    "amount_remaining": amount_due if is_late else 0,
                    "currency": currency,
                    "due_date": int(
                        datetime.combine(due_date, datetime.min.time(), tzinfo=timezone.utc).timestamp()
                    ),
                    "customer": cust_id,
                    "customer_details": {
                        "name": f"Mock Customer {cust_id[-3:]}",
                        "email": f"{cust_id}@example.mock",
                    },
                    "lines": {
                        "data": [
                            {
                                "price": {
                                    "id": price_id,
                                    "nickname": plan_name,
                                    "currency": currency,
                                    "recurring": {
                                        "interval": "month",
                                    },
                                },
                                "quantity": 1,
                                "amount": line_amount,
                            }
                        ]
                    },
                }
            )
        current += timedelta(days=1)

    return invoices


def _mock_list_customers(conn: StripeConnection) -> List[dict]:
    """
    Mock list of customers: just a fixed set of ~50 customers with emails and names.
    """
    _simulate_mock_latency()

    customers: List[dict] = []
    for i in range(1, 51):
        cid = f"cus_mock_{i}"
        customers.append(
            {
                "id": cid,
                "email": f"{cid}@example.mock",
                "name": f"Mock Customer {i:03d}",
            }
        )
    return customers

# app/scripts/test_stripe_etl.py

from __future__ import annotations

import argparse
from datetime import date, timedelta

from sqlalchemy import func, select

from app.db.session import engine
from app.db.tables import (
    billing_daily,
    billing_past_due_invoices,
    customer_metrics,
    company_monthly_metrics,
)
from app.etl.stripe_etl import sync_stripe_for_company


def _count_rows(table, company_id: str):
    with engine.begin() as conn:
        stmt = select(func.count()).select_from(table).where(
            table.c.company_id == company_id
        )
        return conn.execute(stmt).scalar_one()


def _print_counts(stage: str, company_id: str):
    bd = _count_rows(billing_daily, company_id)
    past_due = _count_rows(billing_past_due_invoices, company_id)
    customers = _count_rows(customer_metrics, company_id)
    monthly = _count_rows(company_monthly_metrics, company_id)

    print(f"\n[{stage}] row counts for company {company_id}:")
    print(f"  billing_daily              : {bd}")
    print(f"  billing_past_due_invoices  : {past_due}")
    print(f"  customer_metrics           : {customers}")
    print(f"  company_monthly_metrics    : {monthly}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Stripe ETL for a single company and show DB effects."
    )
    parser.add_argument(
        "--company-id",
        required=True,
        help="UUID of the company to run ETL for",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days back from today to sync (default: 7)",
    )
    args = parser.parse_args()

    company_id = args.company_id
    days = args.days

    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    print(
        f"Running Stripe ETL test for company={company_id}, "
        f"window={start_date}..{end_date}"
    )

    # Show counts before ETL
    _print_counts("BEFORE", company_id)

    # Run the actual ETL (this will use mock Stripe if STRESS_TEST_MOCK_STRIPE=1
    # and the company's integration_connection.external_account_id starts with 'mock_stripe_')
    sync_stripe_for_company(company_id, start_date, end_date)

    # Show counts after ETL
    _print_counts("AFTER", company_id)

    print("\nDone.")


if __name__ == "__main__":
    main()

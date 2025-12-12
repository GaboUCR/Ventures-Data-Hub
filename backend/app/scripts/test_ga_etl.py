# app/scripts/test_ga_etl.py

from __future__ import annotations

import argparse
from datetime import date, timedelta

from sqlalchemy import func, select

from app.db.session import engine
from app.db.tables import (
    acquisition_daily,
    acquisition_channels_daily,
    acquisition_funnel_daily,
)
from app.etl.ga4_etl import sync_ga_for_company


def _count_rows(table, company_id: str) -> int:
    with engine.begin() as conn:
        stmt = (
            select(func.count())
            .select_from(table)
            .where(table.c.company_id == company_id)
        )
        return conn.execute(stmt).scalar_one()


def _print_counts(stage: str, company_id: str) -> None:
    ad = _count_rows(acquisition_daily, company_id)
    ac = _count_rows(acquisition_channels_daily, company_id)
    af = _count_rows(acquisition_funnel_daily, company_id)

    print(f"\n[{stage}] row counts for company {company_id}:")
    print(f"  acquisition_daily             : {ad}")
    print(f"  acquisition_channels_daily    : {ac}")
    print(f"  acquisition_funnel_daily      : {af}")


def _print_samples(company_id: str) -> None:
    with engine.begin() as conn:
        print("\nSample acquisition_daily rows:")
        rows = (
            conn.execute(
                select(acquisition_daily)
                .where(acquisition_daily.c.company_id == company_id)
                .order_by(acquisition_daily.c.date.desc())
                .limit(5)
            )
            .mappings()
            .all()
        )
        for r in rows:
            print(dict(r))

        print("\nSample acquisition_channels_daily rows:")
        rows = (
            conn.execute(
                select(acquisition_channels_daily)
                .where(acquisition_channels_daily.c.company_id == company_id)
                .order_by(
                    acquisition_channels_daily.c.date.desc(),
                    acquisition_channels_daily.c.channel.asc(),
                )
                .limit(10)
            )
            .mappings()
            .all()
        )
        for r in rows:
            print(dict(r))

        print("\nSample acquisition_funnel_daily rows:")
        rows = (
            conn.execute(
                select(acquisition_funnel_daily)
                .where(acquisition_funnel_daily.c.company_id == company_id)
                .order_by(acquisition_funnel_daily.c.date.desc())
                .limit(5)
            )
            .mappings()
            .all()
        )
        for r in rows:
            print(dict(r))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run GA4 ETL for a single company and show DB effects."
    )
    parser.add_argument(
        "--company-id",
        required=True,
        help="UUID of the company to run GA4 ETL for",
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
        f"Running GA4 ETL test for company={company_id}, "
        f"window={start_date}..{end_date}"
    )

    # BEFORE
    _print_counts("BEFORE", company_id)

    # Run ETL (this will use mock GA4 if STRESS_TEST_MOCK_GA4=1
    # and external_account_id starts with 'mock_ga4_')
    sync_ga_for_company(company_id, start_date, end_date)

    # AFTER
    _print_counts("AFTER", company_id)
    _print_samples(company_id)

    print("\nDone.")


if __name__ == "__main__":
    main()

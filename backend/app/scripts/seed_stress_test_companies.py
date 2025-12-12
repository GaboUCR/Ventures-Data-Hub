# app/scripts/seed_stress_test_companies.py

from __future__ import annotations

import argparse
from datetime import datetime
from typing import Optional

from sqlalchemy import insert, select

from app.db.session import engine
from app.db.tables import (
    users,
    companies,
    company_memberships,
    integration_connections,
)


DEFAULT_N_COMPANIES = 500
ADMIN_EMAIL = "admin@aceventures.com"


def _get_admin_user_id(conn) -> Optional[str]:
    row = conn.execute(
        select(users.c.id).where(users.c.email == ADMIN_EMAIL)
    ).first()
    return str(row[0]) if row else None


def seed_stress_test_companies(n_companies: int = DEFAULT_N_COMPANIES) -> None:
    """
    Seed a large number of 'mock' companies + Stripe/GA4 integration_connections
    to stress-test ingestion.

    - Companies:
        name: "MockCo 001", "MockCo 002", ...
        slug: "mockco-001", ...
        stage: "StressTest"
        sector: "MockData"

    - integration_connections:
        provider='stripe', external_account_id='mock_stripe_001', ...
        provider='ga4',    external_account_id='mock_ga4_001', ...

    - If the Ace admin (admin@aceventures.com) exists, it is added as an
      'admin' member to each mock company.
    """
    now = datetime.utcnow()

    print(f"Seeding {n_companies} stress-test companies...")
    with engine.begin() as conn:
        admin_id = _get_admin_user_id(conn)
        if admin_id:
            print(f"Found admin user {ADMIN_EMAIL} -> {admin_id}")
        else:
            print(f"WARNING: admin user {ADMIN_EMAIL} not found, "
                  "will skip memberships.")

        for i in range(1, n_companies + 1):
            label = f"{i:03d}"
            name = f"MockCo {label}"
            slug = f"mockco-{label}"

            # --- company ---
            company_id = conn.execute(
                insert(companies)
                .returning(companies.c.id)
                .values(
                    name=name,
                    slug=slug,
                    stage="StressTest",
                    sector="MockData",
                    country="US",
                    website_url=f"https://{slug}.example.mock",
                    created_at=now,
                    updated_at=now,
                )
            ).scalar_one()

            # --- integration connections: mock Stripe + mock GA4 ---
            conn.execute(
                insert(integration_connections),
                [
                    {
                        "company_id": company_id,
                        "provider": "stripe",
                        # Detection key for ETL mocks:
                        "external_account_id": f"mock_stripe_{label}",
                        "access_token": "sk_mock_stress_test",
                        "refresh_token": None,
                        "scopes": ["read_write"],
                        "status": "connected",
                        "created_at": now,
                        "updated_at": now,
                    },
                    {
                        "company_id": company_id,
                        "provider": "ga4",
                        "external_account_id": f"mock_ga4_{label}",
                        "access_token": "ga_mock_stress_test",
                        "refresh_token": None,
                        "scopes": ["https://www.googleapis.com/auth/analytics.readonly"],
                        "status": "connected",
                        "created_at": now,
                        "updated_at": now,
                    },
                ],
            )

            # --- optional: admin membership ---
            if admin_id:
                conn.execute(
                    insert(company_memberships).values(
                        company_id=company_id,
                        user_id=admin_id,
                        role="admin",
                        is_primary_owner=False,
                        created_at=now,
                    )
                )

            if i % 50 == 0:
                print(f"  -> inserted {i} companies...")

    print(f"Done. Seeded {n_companies} stress-test companies.")
    

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed stress-test mock companies + integrations."
    )
    parser.add_argument(
        "--n",
        type=int,
        default=DEFAULT_N_COMPANIES,
        help=f"Number of companies to create (default: {DEFAULT_N_COMPANIES})",
    )
    args = parser.parse_args()
    seed_stress_test_companies(args.n)


if __name__ == "__main__":
    main()

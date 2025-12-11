# app/scripts/seed_demo_data.py

from __future__ import annotations

import random
from datetime import date, datetime, timedelta
from typing import Dict, List, Tuple

from sqlalchemy import delete, insert
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import engine
from app.db.tables import (
    users,
    companies,
    company_memberships,
    integration_connections,
    company_monthly_metrics,
    billing_daily,
    acquisition_daily,
    plan_monthly_metrics,
    retention_cohorts,
    pre_churn_insights,
    acquisition_channels_daily,
    acquisition_funnel_daily,
    billing_past_due_invoices,
    customer_metrics,
)
from app.core.security import get_password_hash


def wipe_data() -> None:
    """Delete all existing data in a FK-safe order."""
    print("Wiping existing data...")

    with engine.begin() as conn:
        # analytics first (depend on companies)
        conn.execute(delete(retention_cohorts))
        conn.execute(delete(pre_churn_insights))
        conn.execute(delete(billing_past_due_invoices))
        conn.execute(delete(billing_daily))
        conn.execute(delete(acquisition_funnel_daily))
        conn.execute(delete(acquisition_channels_daily))
        conn.execute(delete(acquisition_daily))
        conn.execute(delete(plan_monthly_metrics))
        conn.execute(delete(company_monthly_metrics))
        conn.execute(delete(customer_metrics))

        # core depending tables
        conn.execute(delete(integration_connections))
        conn.execute(delete(company_memberships))

        # base tables
        conn.execute(delete(companies))
        conn.execute(delete(users))

    print("Data wiped.")


def seed_users_and_companies() -> tuple[Dict[str, str], Dict[str, str]]:
    """
    Insert:
      - 1 admin user
      - 3 company founders
      - 3 companies
      - memberships
    Returns:
      (user_ids_by_key, company_ids_by_key)
    """
    print("Seeding users & companies...")
    now = datetime.utcnow()

    with engine.begin() as conn:
        # --- users ---
        admin_id = conn.execute(
            insert(users)
            .returning(users.c.id)
            .values(
                email="admin@aceventures.com",
                password_hash=get_password_hash("admin123"),
                full_name="Ace Admin",
                global_role="admin",
                is_active=True,
                created_at=now,
                updated_at=now,
            )
        ).scalar_one()

        finpay_user_id = conn.execute(
            insert(users)
            .returning(users.c.id)
            .values(
                email="founder@finpay.io",
                password_hash=get_password_hash("founder123"),
                full_name="Finpay Founder",
                global_role="company_user",
                is_active=True,
                created_at=now,
                updated_at=now,
            )
        ).scalar_one()

        green_user_id = conn.execute(
            insert(users)
            .returning(users.c.id)
            .values(
                email="founder@greenledger.io",           
                password_hash=get_password_hash("founder123"),
                full_name="GreenLedger Founder",
                global_role="company_user",
                is_active=True,
                created_at=now,
                updated_at=now,
            )
        ).scalar_one()

        saasify_user_id = conn.execute(
            insert(users)
            .returning(users.c.id)
            .values(
                email="founder@saasify.io",
                password_hash=get_password_hash("founder123"),
                full_name="SaaSify Founder",
                global_role="company_user",
                is_active=True,
                created_at=now,
                updated_at=now,
            )
        ).scalar_one()

        # --- companies ---
        finpay_company_id = conn.execute(
            insert(companies)
            .returning(companies.c.id)
            .values(
                name="Finpay",
                slug="finpay",
                stage="Seed",
                sector="Fintech",
                country="US",
                website_url="https://finpay.demo",
                created_at=now,
                updated_at=now,
            )
        ).scalar_one()

        green_company_id = conn.execute(
            insert(companies)
            .returning(companies.c.id)
            .values(
                name="GreenLedger",
                slug="greenledger",
                stage="Series A",
                sector="Climate / SaaS",
                country="DE",
                website_url="https://greenledger.demo",
                created_at=now,
                updated_at=now,
            )
        ).scalar_one()

        saasify_company_id = conn.execute(
            insert(companies)
            .returning(companies.c.id)
            .values(
                name="SaaSify",
                slug="saasify",
                stage="Seed",
                sector="DevTools",
                country="UK",
                website_url="https://saasify.demo",
                created_at=now,
                updated_at=now,
            )
        ).scalar_one()

        # --- memberships ---
        conn.execute(
            insert(company_memberships),
            [
                # Finpay founder
                {
                    "company_id": finpay_company_id,
                    "user_id": finpay_user_id,
                    "role": "owner",
                    "is_primary_owner": True,
                    "created_at": now,
                },
                # GreenLedger founder
                {
                    "company_id": green_company_id,
                    "user_id": green_user_id,
                    "role": "owner",
                    "is_primary_owner": True,
                    "created_at": now,
                },
                # SaaSify founder
                {
                    "company_id": saasify_company_id,
                    "user_id": saasify_user_id,
                    "role": "owner",
                    "is_primary_owner": True,
                    "created_at": now,
                },
                # Ace admin can see everything as member
                {
                    "company_id": finpay_company_id,
                    "user_id": admin_id,
                    "role": "admin",
                    "is_primary_owner": False,
                    "created_at": now,
                },
                {
                    "company_id": green_company_id,
                    "user_id": admin_id,
                    "role": "admin",
                    "is_primary_owner": False,
                    "created_at": now,
                },
                {
                    "company_id": saasify_company_id,
                    "user_id": admin_id,
                    "role": "admin",
                    "is_primary_owner": False,
                    "created_at": now,
                },
            ],
        )

        # --- fake integrations (Stripe + GA4 per company) ---
        conn.execute(
            insert(integration_connections),
            [
                {
                    "company_id": finpay_company_id,
                    "provider": "stripe",
                    "external_account_id": "acct_finpay_demo",
                    "access_token": "sk_test_finpay_fake",
                    "refresh_token": "rt_finpay_fake",
                    "scopes": ["read_write"],
                    "status": "connected",
                    "created_at": now,
                    "updated_at": now,
                },
                {
                    "company_id": finpay_company_id,
                    "provider": "ga4",
                    "external_account_id": "GA4_FINPAY_PROPERTY",
                    "access_token": "ya29.finpay.fake",
                    "refresh_token": "rt_ga_finpay_fake",
                    "scopes": ["analytics.readonly"],
                    "status": "connected",
                    "created_at": now,
                    "updated_at": now,
                },
                {
                    "company_id": green_company_id,
                    "provider": "stripe",
                    "external_account_id": "acct_green_demo",
                    "access_token": "sk_test_green_fake",
                    "refresh_token": "rt_green_fake",
                    "scopes": ["read_write"],
                    "status": "connected",
                    "created_at": now,
                    "updated_at": now,
                },
                {
                    "company_id": green_company_id,
                    "provider": "ga4",
                    "external_account_id": "GA4_GREEN_PROPERTY",
                    "access_token": "ya29.green.fake",
                    "refresh_token": "rt_ga_green_fake",
                    "scopes": ["analytics.readonly"],
                    "status": "connected",
                    "created_at": now,
                    "updated_at": now,
                },
                {
                    "company_id": saasify_company_id,
                    "provider": "stripe",
                    "external_account_id": "acct_saasify_demo",
                    "access_token": "sk_test_saasify_fake",
                    "refresh_token": "rt_saasify_fake",
                    "scopes": ["read_write"],
                    "status": "connected",
                    "created_at": now,
                    "updated_at": now,
                },
                {
                    "company_id": saasify_company_id,
                    "provider": "ga4",
                    "external_account_id": "GA4_SAASIFY_PROPERTY",
                    "access_token": "ya29.saasify.fake",
                    "refresh_token": "rt_ga_saasify_fake",
                    "scopes": ["analytics.readonly"],
                    "status": "connected",
                    "created_at": now,
                    "updated_at": now,
                },
            ],
        )

    user_ids = {
        "admin": str(admin_id),
        "finpay": str(finpay_user_id),
        "green": str(green_user_id),
        "saasify": str(saasify_user_id),
    }
    company_ids = {
        "finpay": str(finpay_company_id),
        "green": str(green_company_id),
        "saasify": str(saasify_company_id),
    }

    print("Users & companies seeded.")
    return user_ids, company_ids


def month_sequence(n_months: int = 12) -> List[date]:
    today = date.today()
    first_of_this_month = date(today.year, today.month, 1)
    return [
        first_of_this_month - timedelta(days=30 * (n_months - 1 - i))
        for i in range(n_months)
    ]


def seed_company_metrics(company_ids: Dict[str, str]) -> Dict[str, List[Tuple[date, int]]]:
    """
    Seed analytics.company_monthly_metrics for each company.
    Returns {company_key: [(month, mrr_cents), ...]} for later plan metrics.
    """
    print("Seeding company_monthly_metrics...")
    random.seed(42)
    months = month_sequence(12)

    patterns = {
        "finpay": {"currency": "USD", "start_mrr_cents": 50_000_00, "growth": 0.07},   # $50k, 7%/mo
        "green": {"currency": "EUR", "start_mrr_cents": 30_000_00, "growth": 0.05},
        "saasify": {"currency": "USD", "start_mrr_cents": 15_000_00, "growth": 0.09},
    }

    company_month_series: Dict[str, List[Tuple[date, int]]] = {k: [] for k in company_ids}

    with engine.begin() as conn:
        for key, cid in company_ids.items():
            cfg = patterns[key]
            mrr_cents = cfg["start_mrr_cents"]

            for idx, m in enumerate(months):
                # simple monthly dynamics
                new_mrr = int(mrr_cents * 0.18)
                expansion_mrr = int(mrr_cents * 0.05)
                contraction_mrr = int(mrr_cents * 0.03)
                churned_mrr = int(mrr_cents * 0.05)

                arr_cents = mrr_cents * 12
                if mrr_cents > 0:
                    nrr_percent = 100.0 + ((expansion_mrr - churned_mrr) / mrr_cents) * 100.0
                    churn_rate_percent = (churned_mrr / mrr_cents) * 100.0
                else:
                    nrr_percent = 100.0
                    churn_rate_percent = 0.0

                active_customers = max(10, mrr_cents // 10_000)  # rough

                conn.execute(
                    insert(company_monthly_metrics).values(
                        company_id=cid,
                        month=m,
                        currency=cfg["currency"],
                        mrr_cents=mrr_cents,
                        arr_cents=arr_cents,
                        new_mrr_cents=new_mrr,
                        expansion_mrr_cents=expansion_mrr,
                        contraction_mrr_cents=contraction_mrr,
                        churned_mrr_cents=churned_mrr,
                        nrr_percent=nrr_percent,
                        active_customers=active_customers,
                        churn_rate_percent=churn_rate_percent,
                    )
                )

                company_month_series[key].append((m, mrr_cents))
                # next month
                mrr_cents = int(mrr_cents * (1.0 + cfg["growth"]))

    print("company_monthly_metrics seeded.")
    return company_month_series


def seed_plan_monthly_metrics(
    company_ids: Dict[str, str],
    company_month_series: Dict[str, List[Tuple[date, int]]],
) -> None:
    print("Seeding plan_monthly_metrics...")
    with engine.begin() as conn:
        for key, cid in company_ids.items():
            for month, mrr_cents in company_month_series[key]:
                # split: 60% basic, 40% pro
                basic_mrr = int(mrr_cents * 0.6)
                pro_mrr = mrr_cents - basic_mrr

                conn.execute(
                    insert(plan_monthly_metrics).values(
                        company_id=cid,
                        plan_id="basic",
                        month=month,
                        plan_name="Basic",
                        currency="USD",
                        mrr_cents=basic_mrr,
                        subscribers=max(5, basic_mrr // 5000),
                        churn_rate_percent=5.0,
                        growth_rate_percent=8.0,
                    )
                )
                conn.execute(
                    insert(plan_monthly_metrics).values(
                        company_id=cid,
                        plan_id="pro",
                        month=month,
                        plan_name="Pro",
                        currency="USD",
                        mrr_cents=pro_mrr,
                        subscribers=max(3, pro_mrr // 15000),
                        churn_rate_percent=3.0,
                        growth_rate_percent=10.0,
                    )
                )
    print("plan_monthly_metrics seeded.")


def seed_billing_and_invoices(company_ids: Dict[str, str]) -> None:
    print("Seeding billing_daily & billing_past_due_invoices...")
    random.seed(43)
    today = date.today()
    days_back = 90

    with engine.begin() as conn:
        for cid in company_ids.values():
            for offset in range(days_back):
                d = today - timedelta(days=days_back - 1 - offset)
                attempts = random.randint(20, 80)
                failed = random.randint(0, 5)
                success = max(0, attempts - failed)
                refunds_cents = random.randint(0, 20_00)  # up to $200
                mrr_at_risk_cents = random.choice([0, 0, 0, random.randint(0, 5_000_00)])

                conn.execute(
                    insert(billing_daily).values(
                        company_id=cid,
                        date=d,
                        payment_attempts=attempts,
                        payment_success=success,
                        payment_failed=failed,
                        refunds_cents=refunds_cents,
                        mrr_at_risk_cents=mrr_at_risk_cents,
                    )
                )

            # some past-due invoices
            for i in range(2):
                due = today - timedelta(days=random.randint(7, 40))
                conn.execute(
                    insert(billing_past_due_invoices).values(
                        company_id=cid,
                        invoice_id=f"inv_demo_{i}_{cid[:8]}",
                        customer_name=f"Customer {i+1}",
                        customer_email=f"customer{i+1}@demo.test",
                        amount_cents=random.randint(5_000, 50_000),
                        currency="USD",
                        due_date=due,
                    )
                )

    print("billing_daily & billing_past_due_invoices seeded.")


def seed_acquisition(company_ids: Dict[str, str]) -> None:
    print("Seeding acquisition data...")
    random.seed(44)
    today = date.today()
    days_back = 60
    channels = ["Organic Search", "Paid Search", "Direct", "Referral"]

    with engine.begin() as conn:
        for cid in company_ids.values():
            for offset in range(days_back):
                d = today - timedelta(days=days_back - 1 - offset)

                total_sessions = 0
                total_signups = 0
                total_new_customers = 0
                total_new_mrr_cents = 0

                # channel-level detail
                for ch in channels:
                    sessions = random.randint(50, 400)
                    signups = int(sessions * random.uniform(0.03, 0.12))
                    new_cust = int(signups * random.uniform(0.15, 0.4))
                    new_mrr = new_cust * random.randint(5_000, 20_000)

                    total_sessions += sessions
                    total_signups += signups
                    total_new_customers += new_cust
                    total_new_mrr_cents += new_mrr

                    conn.execute(
                        insert(acquisition_channels_daily).values(
                            company_id=cid,
                            date=d,
                            channel=ch,
                            sessions=sessions,
                            signups=signups,
                            new_customers=new_cust,
                            new_mrr_cents=new_mrr,
                        )
                    )

                # simple funnel
                visits = total_sessions
                signups = total_signups
                started_checkout = int(signups * random.uniform(0.5, 0.8))
                paid = int(started_checkout * random.uniform(0.4, 0.7))

                conn.execute(
                    insert(acquisition_funnel_daily).values(
                        company_id=cid,
                        date=d,
                        visits=visits,
                        signups=signups,
                        started_checkout=started_checkout,
                        paid=paid,
                    )
                )

                # optional coarse table
                conn.execute(
                    insert(acquisition_daily).values(
                        company_id=cid,
                        date=d,
                        channel_group="All",
                        sessions=total_sessions,
                        signups=total_signups,
                        new_customers=total_new_customers,
                        new_mrr_cents=total_new_mrr_cents,
                    )
                )

    print("acquisition tables seeded.")


def seed_cohorts(company_ids: Dict[str, str]) -> None:
    print("Seeding retention_cohorts & pre_churn_insights...")
    random.seed(45)
    today = date.today()
    base_month = date(today.year, today.month, 1)

    with engine.begin() as conn:
        for cid in company_ids.values():
            # 12 cohorts, 0–11 months since signup
            for cohort_offset in range(12):
                cohort_month = base_month - timedelta(days=30 * (11 - cohort_offset))
                for m in range(0, 12):
                    # simple decay curve
                    mrr_retained = max(0.0, 100.0 - 5.0 * m + random.uniform(-2.0, 2.0))
                    cust_retained = max(0.0, 100.0 - 4.0 * m + random.uniform(-3.0, 3.0))

                    conn.execute(
                        insert(retention_cohorts).values(
                            company_id=cid,
                            cohort_month=cohort_month,
                            months_since_signup=m,
                            mrr_retained_percent=mrr_retained,
                            customer_retained_percent=cust_retained,
                        )
                    )

            # pre-churn insights
            texts = [
                "Most churned users visited /pricing and /cancel within 7 days before leaving.",
                "Churned customers had 50% fewer logins in the last 30 days.",
                "High-churn cohorts show low engagement with the new onboarding flow.",
            ]
            for rank, t in enumerate(texts, start=1):
                conn.execute(
                    insert(pre_churn_insights).values(
                        company_id=cid,
                        rank=rank,
                        text=t,
                    )
                )

    print("retention_cohorts & pre_churn_insights seeded.")


def seed_customer_metrics(company_ids: Dict[str, str]) -> None:
    print("Seeding customer_metrics...")
    random.seed(46)
    now = datetime.utcnow()

    with engine.begin() as conn:
        for key, cid in company_ids.items():
            for i in range(1, 11):
                first_seen = now - timedelta(days=random.randint(60, 720))
                last_activity = first_seen + timedelta(days=random.randint(0, 60))
                current_mrr_cents = random.choice(
                    [0, 0, random.randint(5_000, 20_000), random.randint(20_000, 80_000)]
                )
                ltv_cents = current_mrr_cents * random.randint(3, 24)
                status = random.choice(["active", "churned", "past_due"])
                is_high_value = ltv_cents >= 500_000  # >= $5k

                conn.execute(
                    insert(customer_metrics).values(
                        company_id=cid,
                        customer_id=f"{key}_cust_{i}",
                        email=f"customer{i}@{key}.demo",
                        name=f"{key.capitalize()} Customer {i}",
                        current_mrr_cents=current_mrr_cents,
                        lifetime_revenue_cents=ltv_cents,
                        first_seen_at=first_seen,
                        last_activity_at=last_activity,
                        status=status,
                        is_high_value=is_high_value,
                        created_at=now,
                        updated_at=now,
                    )
                )

    print("customer_metrics seeded.")


def main() -> None:
    try:
        wipe_data()
        user_ids, company_ids = seed_users_and_companies()
        company_month_series = seed_company_metrics(company_ids)
        seed_plan_monthly_metrics(company_ids, company_month_series)
        seed_billing_and_invoices(company_ids)
        seed_acquisition(company_ids)
        seed_cohorts(company_ids)
        seed_customer_metrics(company_ids)
    except SQLAlchemyError as e:
        print(f"Seeding failed due to DB error: {e}")
        raise
    print("\n✅ Demo data seeded successfully.")
    print("Admin login: admin@ace.local / admin123")
    print("Example founder login: founder@finpay.demo / founder123")


if __name__ == "__main__":
    main()

# app/db/tables.py
from sqlalchemy import (
    Table,
    Column,
    String,
    Text,
    DateTime,
    Boolean,
    Integer,
    Numeric,
    Date,
    ARRAY,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func, text

from app.db.session import metadata
# --- USERS ---

users = Table(
    "users",
    metadata,
    Column(
        "id",
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    ),
    Column("email", Text, nullable=False, unique=True),  # CITEXT in DB, Text here is fine
    Column("password_hash", Text, nullable=False),
    Column("full_name", Text, nullable=False),
    Column("global_role", String, nullable=False, server_default=text("'company_user'")),
    Column("is_active", Boolean, nullable=False, server_default=text("true")),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    Column("updated_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    schema="core",
)

# --- COMPANIES ---

companies = Table(
    "companies",
    metadata,
    Column(
        "id",
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    ),
    Column("name", Text, nullable=False),
    Column("slug", Text, unique=True),
    Column("stage", Text),
    Column("sector", Text),
    Column("country", Text),
    Column("website_url", Text),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    Column("updated_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    schema="core",
)

# --- COMPANY MEMBERSHIPS ---

company_memberships = Table(
    "company_memberships",
    metadata,
    Column("company_id", UUID(as_uuid=True), nullable=False),
    Column("user_id", UUID(as_uuid=True), nullable=False),
    Column("role", String, nullable=False, server_default=text("'owner'")),  # 'owner' | 'admin' | 'member' | 'viewer'
    Column("is_primary_owner", Boolean, nullable=False, server_default=text("false")),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    schema="core",
)

integration_connections = Table(
    "integration_connections",
    metadata,
    Column(
        "id",
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    ),
    Column("company_id", UUID(as_uuid=True), nullable=False),
    Column("provider", String, nullable=False),          # 'stripe' | 'ga4'
    Column("external_account_id", Text, nullable=False), # acct_xxx or GA property id
    Column("access_token", Text, nullable=False),
    Column("refresh_token", Text),
    Column("scopes", ARRAY(Text)),
    Column("status", String, nullable=False, server_default=text("'connected'")),
    Column("last_synced_at", DateTime(timezone=True)),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    Column("updated_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    schema="core",
)

# --- ANALYTICS: company_monthly_metrics ---

company_monthly_metrics = Table(
    "company_monthly_metrics",
    metadata,
    Column("company_id", UUID(as_uuid=True), primary_key=True),
    Column("month", Date, primary_key=True),  # e.g. 2025-01-01
    Column("currency", String, nullable=False),

    Column("mrr_cents", Integer, nullable=False, server_default=text("0")),
    Column("arr_cents", Integer, nullable=False, server_default=text("0")),

    Column("new_mrr_cents", Integer, nullable=False, server_default=text("0")),
    Column("expansion_mrr_cents", Integer, nullable=False, server_default=text("0")),
    Column("contraction_mrr_cents", Integer, nullable=False, server_default=text("0")),
    Column("churned_mrr_cents", Integer, nullable=False, server_default=text("0")),

    Column("nrr_percent", Numeric(6, 2)),
    Column("active_customers", Integer, nullable=False, server_default=text("0")),
    Column("churn_rate_percent", Numeric(6, 2)),

    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    Column("updated_at", DateTime(timezone=True), server_default=func.now(), nullable=False),

    schema="analytics",
)

# --- ANALYTICS: billing_daily ---

billing_daily = Table(
    "billing_daily",
    metadata,
    Column("company_id", UUID(as_uuid=True), primary_key=True),
    Column("date", Date, primary_key=True),

    Column("payment_attempts", Integer, nullable=False, server_default=text("0")),
    Column("payment_success", Integer, nullable=False, server_default=text("0")),
    Column("payment_failed", Integer, nullable=False, server_default=text("0")),

    Column("refunds_cents", Integer, nullable=False, server_default=text("0")),
    Column("mrr_at_risk_cents", Integer, nullable=False, server_default=text("0")),

    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),

    schema="analytics",
)

# --- ANALYTICS: acquisition_daily (for GA4 sessions / signups) ---

acquisition_daily = Table(
    "acquisition_daily",
    metadata,
    Column("company_id", UUID(as_uuid=True), primary_key=True),
    Column("date", Date, primary_key=True),
    Column("channel_group", Text, primary_key=True),  # 👈 add this

    Column("sessions", Integer, nullable=False, server_default=text("0")),
    Column("signups", Integer, nullable=False, server_default=text("0")),
    Column("new_customers", Integer, nullable=False, server_default=text("0")),
    Column("new_mrr_cents", Integer, nullable=False, server_default=text("0")),

    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),

    schema="analytics",
)

# --- company_monthly_metrics, billing_daily, acquisition_daily

plan_monthly_metrics = Table(
    "plan_monthly_metrics",
    metadata,
    Column("company_id", UUID(as_uuid=True), primary_key=True),
    Column("plan_id", Text, primary_key=True),
    Column("month", Date, primary_key=True),

    Column("plan_name", Text, nullable=False),
    Column("currency", String, nullable=False),

    Column("mrr_cents", Integer, nullable=False, server_default=text("0")),
    Column("subscribers", Integer, nullable=False, server_default=text("0")),

    Column("churn_rate_percent", Numeric(6, 2)),
    Column("growth_rate_percent", Numeric(6, 2)),

    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),

    schema="analytics",
)

# --- Cohorts

retention_cohorts = Table(
    "retention_cohorts",
    metadata,
    Column("company_id", UUID(as_uuid=True), primary_key=True),
    Column("cohort_month", Date, primary_key=True),          # e.g. 2025-01-01
    Column("months_since_signup", Integer, primary_key=True),# 0,1,...,12
    Column("mrr_retained_percent", Numeric(5, 2)),           # 0–100
    Column("customer_retained_percent", Numeric(5, 2)),      # optional
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    schema="analytics",
)

pre_churn_insights = Table(
    "pre_churn_insights",
    metadata,
    Column("company_id", UUID(as_uuid=True), primary_key=True),
    Column("rank", Integer, primary_key=True),               # 1,2,3...
    Column("text", Text, nullable=False),                    # e.g. "Most churned users visited /pricing"
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    schema="analytics",
)

# --- Acquisition

acquisition_channels_daily = Table(
    "acquisition_channels_daily",
    metadata,
    Column("company_id", UUID(as_uuid=True), primary_key=True),
    Column("date", Date, primary_key=True),
    Column("channel", Text, primary_key=True),  # e.g. "Organic Search"
    Column("sessions", Integer, nullable=False, server_default=text("0")),
    Column("signups", Integer, nullable=False, server_default=text("0")),
    Column("new_customers", Integer, nullable=False, server_default=text("0")),
    Column("new_mrr_cents", Integer, nullable=False, server_default=text("0")),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    schema="analytics",
)

acquisition_funnel_daily = Table(
    "acquisition_funnel_daily",
    metadata,
    Column("company_id", UUID(as_uuid=True), primary_key=True),
    Column("date", Date, primary_key=True),
    Column("visits", Integer, nullable=False, server_default=text("0")),
    Column("signups", Integer, nullable=False, server_default=text("0")),
    Column("started_checkout", Integer, nullable=False, server_default=text("0")),
    Column("paid", Integer, nullable=False, server_default=text("0")),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    schema="analytics",
)

# --- Billing

billing_past_due_invoices = Table(
    "billing_past_due_invoices",
    metadata,
    Column("company_id", UUID(as_uuid=True), primary_key=True),
    Column("invoice_id", Text, primary_key=True),     # e.g. "in_123"
    Column("customer_name", Text),
    Column("customer_email", Text),
    Column("amount_cents", Integer, nullable=False, server_default=text("0")),
    Column("currency", String, nullable=False),
    Column("due_date", Date, nullable=False),
    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    schema="analytics",
)

# --- Customer

customer_metrics = Table(
    "customer_metrics",
    metadata,
    Column("company_id", UUID(as_uuid=True), primary_key=True),
    Column("customer_id", Text, primary_key=True),

    Column("email", Text),
    Column("name", Text),

    Column("current_mrr_cents", Integer, nullable=False, server_default=text("0")),
    Column("lifetime_revenue_cents", Integer, nullable=False, server_default=text("0")),

    Column("first_seen_at", DateTime(timezone=True)),
    Column("last_activity_at", DateTime(timezone=True)),

    Column("status", String, nullable=False, server_default=text("'active'")),
    # optional pre-computed flag from your ETL
    Column("is_high_value", Boolean, nullable=False, server_default=text("false")),

    Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False),
    Column("updated_at", DateTime(timezone=True), server_default=func.now(), nullable=False),

    schema="analytics",
)

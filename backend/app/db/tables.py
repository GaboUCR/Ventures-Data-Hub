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

    Column("sessions", Integer, nullable=False, server_default=text("0")),
    Column("signups", Integer, nullable=False, server_default=text("0")),
    Column("new_customers", Integer, nullable=False, server_default=text("0")),

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
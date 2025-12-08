-- =========================================================
-- Esquema base para usuarios (admin Ace + dueños de compañía)
-- =========================================================

-- 1) Crear esquema y extensiones necesarias
CREATE SCHEMA IF NOT EXISTS core;

CREATE EXTENSION IF NOT EXISTS pgcrypto;  -- para gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS citext;    -- para tipo CITEXT (email case-insensitive)

-- 2) Tipos ENUM
-- Rol global del usuario (a nivel plataforma Ace)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_type WHERE typname = 'global_user_role' AND typnamespace = 'core'::regnamespace
    ) THEN
        CREATE TYPE core.global_user_role AS ENUM (
            'admin',         -- admin de Ace (ve todo el portfolio)
            'company_user'   -- dueño/miembro de una o varias compañías
        );
    END IF;
END $$;

-- Rol del usuario dentro de una compañía concreta
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_type WHERE typname = 'company_role' AND typnamespace = 'core'::regnamespace
    ) THEN
        CREATE TYPE core.company_role AS ENUM (
            'owner',     -- dueño / founder principal
            'admin',     -- permisos altos dentro de la compañía
            'member',    -- miembro normal
            'viewer'     -- solo lectura
        );
    END IF;
END $$;

-- 3) Tabla de usuarios (admins + dueños/miembros)
CREATE TABLE IF NOT EXISTS core.users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           CITEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,             -- o NULL si luego usas SSO
    full_name       TEXT NOT NULL,
    global_role     core.global_user_role NOT NULL DEFAULT 'company_user',
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,

    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 4) Tabla de compañías (startups del portfolio)
CREATE TABLE IF NOT EXISTS core.companies (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL,
    slug        TEXT UNIQUE,                      -- para URLs tipo /companies/finpay
    stage       TEXT,                             -- luego se puede cambiar a ENUM
    sector      TEXT,                             -- ej: 'Fintech', 'B2B SaaS'
    country     TEXT,
    website_url TEXT,

    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 5) Tabla de memberships (relación usuario <-> compañía)
CREATE TABLE IF NOT EXISTS core.company_memberships (
    company_id        UUID NOT NULL
        REFERENCES core.companies(id) ON DELETE CASCADE,
    user_id           UUID NOT NULL
        REFERENCES core.users(id) ON DELETE CASCADE,

    role              core.company_role NOT NULL DEFAULT 'owner',
    is_primary_owner  BOOLEAN NOT NULL DEFAULT FALSE,

    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),

    PRIMARY KEY (company_id, user_id)
);

-- 6) Índice único opcional para un solo owner principal por compañía
CREATE UNIQUE INDEX IF NOT EXISTS company_primary_owner_unique_idx
    ON core.company_memberships (company_id)
    WHERE is_primary_owner = TRUE;

-- =====================================================================
-- SCHEMAS & EXTENSIONS
-- =====================================================================

CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS stripe_raw;
CREATE SCHEMA IF NOT EXISTS ga_raw;
CREATE SCHEMA IF NOT EXISTS analytics;

CREATE EXTENSION IF NOT EXISTS pgcrypto;  -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS citext;    -- CITEXT type for email, etc.

-- =====================================================================
-- CORE ENUMS
-- =====================================================================

-- Global role of the user (what they can see at app level)
CREATE TYPE core.global_user_role AS ENUM (
    'admin',         -- Ace admin, can see portfolio
    'company_user'   -- company owner/member, sees only their companies
);

-- Role of the user *within* a company
CREATE TYPE core.company_role AS ENUM (
    'owner',     -- main owner / founder
    'admin',     -- admin for that company
    'member',    -- regular member
    'viewer'     -- read-only
);

-- Integration provider (Stripe / GA4)
CREATE TYPE core.integration_provider AS ENUM ('stripe', 'ga4');

-- Integration connection status
CREATE TYPE core.integration_status AS ENUM (
    'pending',
    'connected',
    'revoked',
    'error'
);

-- =====================================================================
-- CORE TABLES: USERS, COMPANIES, MEMBERSHIPS
-- =====================================================================

CREATE TABLE core.users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           CITEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,             -- or NULL if using SSO
    full_name       TEXT NOT NULL,
    global_role     core.global_user_role NOT NULL DEFAULT 'company_user',
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,

    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE core.companies (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL,
    slug        TEXT UNIQUE,
    stage       TEXT,          -- e.g. 'seed', 'series_a'
    sector      TEXT,          -- e.g. 'Fintech', 'B2B SaaS'
    country     TEXT,
    website_url TEXT,

    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE core.company_memberships (
    company_id        UUID NOT NULL
        REFERENCES core.companies(id) ON DELETE CASCADE,
    user_id           UUID NOT NULL
        REFERENCES core.users(id) ON DELETE CASCADE,

    role              core.company_role NOT NULL DEFAULT 'owner',
    is_primary_owner  BOOLEAN NOT NULL DEFAULT FALSE,

    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),

    PRIMARY KEY (company_id, user_id)
);

CREATE UNIQUE INDEX company_primary_owner_unique_idx
    ON core.company_memberships (company_id)
    WHERE is_primary_owner = TRUE;

-- =====================================================================
-- CORE TABLES: INTEGRATIONS & SYNC STATE
-- =====================================================================

CREATE TABLE core.integration_connections (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id          UUID NOT NULL
        REFERENCES core.companies(id) ON DELETE CASCADE,
    provider            core.integration_provider NOT NULL,
    external_account_id TEXT NOT NULL,      -- Stripe account_id, GA4 property id, etc.

    access_token        TEXT NOT NULL,      -- ideally encrypted / stored securely
    refresh_token       TEXT,
    scopes              TEXT[],

    status              core.integration_status NOT NULL DEFAULT 'connected',
    last_synced_at      TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (company_id, provider)
);

CREATE TABLE core.integration_sync_state (
    id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    integration_connection_id UUID NOT NULL
        REFERENCES core.integration_connections(id) ON DELETE CASCADE,

    object_type               TEXT NOT NULL,       -- 'stripe_subscription', 'stripe_invoice', 'ga4_daily_traffic', ...
    last_cursor               TEXT,
    last_synced_at            TIMESTAMPTZ,
    last_run_status           TEXT,                -- 'ok', 'error', etc.

    created_at                TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at                TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (integration_connection_id, object_type)
);

-- =====================================================================
-- STRIPE RAW TABLES
-- =====================================================================

CREATE TABLE stripe_raw.events (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id        UUID NOT NULL
        REFERENCES core.companies(id) ON DELETE CASCADE,
    stripe_account_id TEXT NOT NULL,

    event_id          TEXT NOT NULL,
    type              TEXT NOT NULL,        -- 'invoice.paid', 'customer.subscription.created', ...
    object_type       TEXT NOT NULL,        -- 'invoice', 'subscription', 'charge', ...
    external_id       TEXT NOT NULL,        -- main object id (inv_..., sub_..., ch_...)

    payload           JSONB NOT NULL,       -- full Stripe event
    created_at        TIMESTAMPTZ NOT NULL, -- Stripe event creation time
    received_at       TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (stripe_account_id, event_id)
);

CREATE INDEX stripe_events_company_obj_idx
    ON stripe_raw.events (company_id, object_type);

CREATE INDEX stripe_events_account_created_idx
    ON stripe_raw.events (stripe_account_id, created_at);

CREATE TABLE stripe_raw.snapshots (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id        UUID NOT NULL
        REFERENCES core.companies(id) ON DELETE CASCADE,
    stripe_account_id TEXT NOT NULL,

    object_type       TEXT NOT NULL,        -- 'customer', 'subscription', 'invoice', ...
    external_id       TEXT NOT NULL,        -- Stripe object id
    payload           JSONB NOT NULL,
    synced_at         TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (stripe_account_id, object_type, external_id)
);

CREATE INDEX stripe_snapshots_company_obj_idx
    ON stripe_raw.snapshots (company_id, object_type);

-- =====================================================================
-- GA4 RAW TABLES
-- =====================================================================

CREATE TABLE ga_raw.daily_traffic (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id       UUID NOT NULL
        REFERENCES core.companies(id) ON DELETE CASCADE,

    date             DATE NOT NULL,
    channel_group    TEXT,      -- 'Organic Search', 'Direct', ...
    landing_page     TEXT,      -- optional

    sessions         INTEGER NOT NULL DEFAULT 0,
    users            INTEGER NOT NULL DEFAULT 0,
    signups          INTEGER NOT NULL DEFAULT 0,
    started_checkout INTEGER NOT NULL DEFAULT 0,
    paid_events      INTEGER NOT NULL DEFAULT 0,

    synced_at        TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (company_id, date, channel_group, landing_page)
);

CREATE INDEX ga_daily_traffic_company_date_idx
    ON ga_raw.daily_traffic (company_id, date);

CREATE TABLE ga_raw.user_activity (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id         UUID NOT NULL
        REFERENCES core.companies(id) ON DELETE CASCADE,

    ga_user_id         TEXT NOT NULL,     -- user_pseudo_id or user_id
    stripe_customer_id TEXT,              -- if mapped

    last_seen_at       TIMESTAMPTZ NOT NULL,
    sessions_last_30d  INTEGER,
    events_last_30d    INTEGER,
    recent_pages       TEXT[],            -- ['/pricing','/account/cancel', ...]

    synced_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (company_id, ga_user_id)
);

CREATE INDEX ga_user_activity_company_customer_idx
    ON ga_raw.user_activity (company_id, stripe_customer_id);

-- =====================================================================
-- ANALYTICS ENUMS (STRIPE/REVENUE/BILLING)
-- =====================================================================

CREATE TYPE analytics.customer_status AS ENUM ('active', 'trialing', 'at_risk', 'churned');

CREATE TYPE analytics.billing_interval AS ENUM ('day', 'week', 'month', 'year', 'other');

CREATE TYPE analytics.subscription_status AS ENUM (
    'trialing',
    'active',
    'past_due',
    'canceled',
    'unpaid',
    'incomplete',
    'incomplete_expired',
    'paused'
);

CREATE TYPE analytics.invoice_status_enum AS ENUM (
    'draft',
    'open',
    'paid',
    'uncollectible',
    'void'
);

CREATE TYPE analytics.revenue_event_type AS ENUM (
    'invoice_paid',
    'refund',
    'chargeback',
    'adjustment'
);

CREATE TYPE analytics.payment_status AS ENUM (
    'succeeded',
    'failed',
    'requires_action',
    'canceled'
);

-- =====================================================================
-- ANALYTICS TABLES: CUSTOMERS / PLANS / SUBSCRIPTIONS / INVOICES
-- =====================================================================

CREATE TABLE analytics.customers (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id         UUID NOT NULL
        REFERENCES core.companies(id) ON DELETE CASCADE,
    stripe_customer_id TEXT NOT NULL,

    email              TEXT,
    name               TEXT,
    first_seen_at      TIMESTAMPTZ,
    last_seen_at       TIMESTAMPTZ,
    status             analytics.customer_status,
    segments           JSONB,  -- {"region":"US","size":"SMB"} etc.

    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (company_id, stripe_customer_id)
);

CREATE INDEX analytics_customers_company_status_idx
    ON analytics.customers (company_id, status);

CREATE INDEX analytics_customers_company_email_idx
    ON analytics.customers (company_id, email);

CREATE TABLE analytics.plans (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id         UUID NOT NULL
        REFERENCES core.companies(id) ON DELETE CASCADE,

    stripe_price_id    TEXT NOT NULL,
    stripe_product_id  TEXT,
    name               TEXT NOT NULL,

    billing_interval   analytics.billing_interval NOT NULL,
    unit_amount_cents  INTEGER NOT NULL,
    currency           TEXT NOT NULL,

    is_active          BOOLEAN NOT NULL DEFAULT TRUE,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (company_id, stripe_price_id)
);

CREATE INDEX analytics_plans_company_active_idx
    ON analytics.plans (company_id, is_active);

CREATE TABLE analytics.subscriptions (
    id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id             UUID NOT NULL
        REFERENCES core.companies(id) ON DELETE CASCADE,

    stripe_subscription_id TEXT NOT NULL,
    customer_id            UUID NOT NULL
        REFERENCES analytics.customers(id) ON DELETE CASCADE,
    plan_id                UUID
        REFERENCES analytics.plans(id),

    status                 analytics.subscription_status NOT NULL,
    quantity               INTEGER,

    start_date             DATE,
    cancel_at              DATE,
    canceled_at            DATE,
    current_period_start   TIMESTAMPTZ,
    current_period_end     TIMESTAMPTZ,

    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (company_id, stripe_subscription_id)
);

CREATE INDEX analytics_subscriptions_company_status_idx
    ON analytics.subscriptions (company_id, status);

CREATE INDEX analytics_subscriptions_customer_idx
    ON analytics.subscriptions (customer_id);

CREATE TABLE analytics.invoices (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id              UUID NOT NULL
        REFERENCES core.companies(id) ON DELETE CASCADE,

    stripe_invoice_id       TEXT NOT NULL,
    customer_id             UUID
        REFERENCES analytics.customers(id),
    subscription_id         UUID
        REFERENCES analytics.subscriptions(id),

    status                  analytics.invoice_status_enum NOT NULL,
    due_date                DATE,
    paid_at                 TIMESTAMPTZ,

    currency                TEXT NOT NULL,
    subtotal_cents          INTEGER NOT NULL DEFAULT 0,
    tax_cents               INTEGER NOT NULL DEFAULT 0,
    total_cents             INTEGER NOT NULL DEFAULT 0,
    amount_paid_cents       INTEGER NOT NULL DEFAULT 0,
    amount_remaining_cents  INTEGER NOT NULL DEFAULT 0,

    is_past_due             BOOLEAN NOT NULL DEFAULT FALSE,

    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (company_id, stripe_invoice_id)
);

CREATE INDEX analytics_invoices_company_status_idx
    ON analytics.invoices (company_id, status);

CREATE INDEX analytics_invoices_company_pastdue_idx
    ON analytics.invoices (company_id, is_past_due);

CREATE INDEX analytics_invoices_customer_idx
    ON analytics.invoices (customer_id);

CREATE TABLE analytics.invoice_line_items (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id         UUID NOT NULL
        REFERENCES analytics.invoices(id) ON DELETE CASCADE,
    plan_id            UUID
        REFERENCES analytics.plans(id),

    description        TEXT,
    quantity           INTEGER,
    unit_amount_cents  INTEGER,
    amount_cents       INTEGER,

    created_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX analytics_invoice_line_items_invoice_idx
    ON analytics.invoice_line_items (invoice_id);

-- =====================================================================
-- ANALYTICS TABLES: REVENUE EVENTS & PAYMENT ATTEMPTS
-- =====================================================================

CREATE TABLE analytics.revenue_events (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id         UUID NOT NULL
        REFERENCES core.companies(id) ON DELETE CASCADE,

    customer_id        UUID
        REFERENCES analytics.customers(id),
    subscription_id    UUID
        REFERENCES analytics.subscriptions(id),
    plan_id            UUID
        REFERENCES analytics.plans(id),

    event_type         analytics.revenue_event_type NOT NULL,
    occurred_at        TIMESTAMPTZ NOT NULL,
    amount_cents       INTEGER NOT NULL,       -- + revenue, - refund
    currency           TEXT NOT NULL,

    stripe_object_type TEXT NOT NULL,          -- 'invoice', 'charge', 'refund'
    stripe_object_id   TEXT NOT NULL,

    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (company_id, stripe_object_type, stripe_object_id)
);

CREATE INDEX analytics_revenue_events_company_time_idx
    ON analytics.revenue_events (company_id, occurred_at);

CREATE INDEX analytics_revenue_events_company_type_idx
    ON analytics.revenue_events (company_id, event_type);

CREATE TABLE analytics.payment_attempts (
    id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id               UUID NOT NULL
        REFERENCES core.companies(id) ON DELETE CASCADE,

    customer_id              UUID
        REFERENCES analytics.customers(id),
    subscription_id          UUID
        REFERENCES analytics.subscriptions(id),

    stripe_payment_intent_id TEXT,
    stripe_charge_id         TEXT,

    attempted_at             TIMESTAMPTZ NOT NULL,
    status                   analytics.payment_status NOT NULL,
    failure_code             TEXT,
    failure_message          TEXT,

    amount_cents             INTEGER NOT NULL,
    currency                 TEXT NOT NULL,
    is_retry                 BOOLEAN NOT NULL DEFAULT FALSE,

    created_at               TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX analytics_payment_attempts_company_time_idx
    ON analytics.payment_attempts (company_id, attempted_at);

CREATE INDEX analytics_payment_attempts_company_status_idx
    ON analytics.payment_attempts (company_id, status);

-- =====================================================================
-- ANALYTICS TABLES: ACQUISITION / FUNNEL (GA4 + STRIPE)
-- =====================================================================

CREATE TABLE analytics.acquisition_daily (
    company_id      UUID NOT NULL
        REFERENCES core.companies(id) ON DELETE CASCADE,
    date            DATE NOT NULL,
    channel_group   TEXT,

    sessions        INTEGER NOT NULL DEFAULT 0,
    signups         INTEGER NOT NULL DEFAULT 0,
    new_customers   INTEGER NOT NULL DEFAULT 0,
    new_mrr_cents   INTEGER NOT NULL DEFAULT 0,

    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    PRIMARY KEY (company_id, date, channel_group)
);

CREATE INDEX analytics_acquisition_company_date_idx
    ON analytics.acquisition_daily (company_id, date);

CREATE TABLE analytics.funnel_daily (
    company_id       UUID NOT NULL
        REFERENCES core.companies(id) ON DELETE CASCADE,
    date             DATE NOT NULL,

    visits           INTEGER NOT NULL DEFAULT 0,
    signups          INTEGER NOT NULL DEFAULT 0,
    started_checkout INTEGER NOT NULL DEFAULT 0,
    paid             INTEGER NOT NULL DEFAULT 0,

    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),

    PRIMARY KEY (company_id, date)
);

-- 0. Schemas (if not created yet)
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS core;

-- 1) Company & Plan monthly metrics
CREATE TABLE analytics.company_monthly_metrics (
    company_id               UUID NOT NULL
        REFERENCES core.companies(id) ON DELETE CASCADE,
    month                    DATE NOT NULL,  -- e.g. '2025-01-01'
    currency                 TEXT NOT NULL,

    mrr_cents                INTEGER NOT NULL DEFAULT 0,
    arr_cents                INTEGER NOT NULL DEFAULT 0,

    new_mrr_cents            INTEGER NOT NULL DEFAULT 0,
    expansion_mrr_cents      INTEGER NOT NULL DEFAULT 0,
    contraction_mrr_cents    INTEGER NOT NULL DEFAULT 0,
    churned_mrr_cents        INTEGER NOT NULL DEFAULT 0,

    nrr_percent              NUMERIC(6,2),   -- e.g. 123.45
    active_customers         INTEGER NOT NULL DEFAULT 0,
    churn_rate_percent       NUMERIC(6,2),   -- e.g. 4.50

    created_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at               TIMESTAMPTZ NOT NULL DEFAULT now(),

    PRIMARY KEY (company_id, month)
);

CREATE INDEX company_monthly_metrics_month_idx
    ON analytics.company_monthly_metrics (month);


CREATE TABLE analytics.plan_monthly_metrics (
    company_id            UUID NOT NULL
        REFERENCES core.companies(id) ON DELETE CASCADE,
    plan_id               UUID NOT NULL
        REFERENCES analytics.plans(id) ON DELETE CASCADE,
    month                 DATE NOT NULL,

    mrr_cents             INTEGER NOT NULL DEFAULT 0,
    subscribers           INTEGER NOT NULL DEFAULT 0,
    churn_rate_percent    NUMERIC(6,2),
    growth_rate_percent   NUMERIC(6,2),

    created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),

    PRIMARY KEY (company_id, plan_id, month)
);

CREATE INDEX plan_monthly_metrics_company_month_idx
    ON analytics.plan_monthly_metrics (company_id, month);


-- 2) Cohorts & retention
CREATE TYPE analytics.cohort_type AS ENUM (
    'signup_month',       -- clientes agrupados por mes de alta
    'first_payment_month' -- o por primer pago, si lo quieres después
);

CREATE TABLE analytics.cohort_definitions (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id            UUID NOT NULL
        REFERENCES core.companies(id) ON DELETE CASCADE,

    cohort_type           analytics.cohort_type NOT NULL,
    cohort_month          DATE NOT NULL,   -- e.g. '2025-01-01'

    size_customers        INTEGER NOT NULL DEFAULT 0,
    size_mrr_cents        INTEGER NOT NULL DEFAULT 0,

    created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (company_id, cohort_type, cohort_month)
);

CREATE INDEX cohort_definitions_company_idx
    ON analytics.cohort_definitions (company_id);


CREATE TABLE analytics.cohort_retention (
    cohort_id                  UUID NOT NULL
        REFERENCES analytics.cohort_definitions(id) ON DELETE CASCADE,
    months_since_start         INTEGER NOT NULL,  -- 0,1,2,...

    retained_customers         INTEGER NOT NULL DEFAULT 0,
    retained_mrr_cents         INTEGER NOT NULL DEFAULT 0,

    retention_percent_customers NUMERIC(6,2),   -- e.g. 85.50
    retention_percent_mrr      NUMERIC(6,2),

    created_at                 TIMESTAMPTZ NOT NULL DEFAULT now(),

    PRIMARY KEY (cohort_id, months_since_start)
);

CREATE INDEX cohort_retention_months_idx
    ON analytics.cohort_retention (months_since_start);


-- 3) Pre-churn insights
CREATE TABLE analytics.pre_churn_insights (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id            UUID NOT NULL
        REFERENCES core.companies(id) ON DELETE CASCADE,

    period_start          DATE NOT NULL,       -- e.g. cohort base month or “analysis month”
    period_end            DATE NOT NULL,

    summary               TEXT,                -- human-readable summary
    details               JSONB,               -- structured info, e.g. {top_pages_before_churn: [...]}

    created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (company_id, period_start, period_end)
);

CREATE INDEX pre_churn_insights_company_period_idx
    ON analytics.pre_churn_insights (company_id, period_start);


-- 4) Billing daily metrics
CREATE TABLE analytics.billing_daily (
    company_id          UUID NOT NULL
        REFERENCES core.companies(id) ON DELETE CASCADE,
    date                DATE NOT NULL,

    payment_attempts    INTEGER NOT NULL DEFAULT 0,
    payment_success     INTEGER NOT NULL DEFAULT 0,
    payment_failed      INTEGER NOT NULL DEFAULT 0,

    refunds_cents       INTEGER NOT NULL DEFAULT 0,
    mrr_at_risk_cents   INTEGER NOT NULL DEFAULT 0,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

    PRIMARY KEY (company_id, date)
);

CREATE INDEX billing_daily_company_date_idx
    ON analytics.billing_daily (company_id, date);


-- 5) Customer aggregates
CREATE TABLE analytics.customer_aggregates (
    customer_id             UUID PRIMARY KEY
        REFERENCES analytics.customers(id) ON DELETE CASCADE,
    company_id              UUID NOT NULL
        REFERENCES core.companies(id) ON DELETE CASCADE,

    current_mrr_cents       INTEGER NOT NULL DEFAULT 0,
    lifetime_revenue_cents  INTEGER NOT NULL DEFAULT 0,

    first_seen_at           TIMESTAMPTZ,
    last_activity_at        TIMESTAMPTZ,

    status                  analytics.customer_status,   -- mirror / override analytics.customers.status
    primary_plan_id         UUID
        REFERENCES analytics.plans(id),

    segments                JSONB,       -- normalized + denormalized info
    recent_pages            TEXT[],      -- ['/dashboard','/billing','/pricing']
    notes                   TEXT,

    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX customer_aggregates_company_idx
    ON analytics.customer_aggregates (company_id);

CREATE INDEX customer_aggregates_status_idx
    ON analytics.customer_aggregates (status);


-- 6) Portfolio snapshots
CREATE TABLE analytics.company_portfolio_snapshots (
    company_id                   UUID NOT NULL
        REFERENCES core.companies(id) ON DELETE CASCADE,
    month                        DATE NOT NULL,   -- e.g. '2025-01-01'

    arr_cents                    INTEGER NOT NULL DEFAULT 0,
    mrr_cents                    INTEGER NOT NULL DEFAULT 0,
    mrr_growth_rate_percent      NUMERIC(6,2),    -- MRR growth vs prev month
    nrr_percent                  NUMERIC(6,2),
    churn_rate_percent           NUMERIC(6,2),

    payment_success_rate         NUMERIC(6,2),
    mrr_at_risk_cents            INTEGER NOT NULL DEFAULT 0,

    visit_to_signup_rate_percent NUMERIC(6,2),    -- from acquisition_daily/funnel_daily

    created_at                   TIMESTAMPTZ NOT NULL DEFAULT now(),

    PRIMARY KEY (company_id, month)
);

CREATE INDEX portfolio_snapshots_month_idx
    ON analytics.company_portfolio_snapshots (month);


-- 7) Alerts
CREATE TYPE analytics.alert_severity AS ENUM ('info', 'warning', 'critical');

CREATE TYPE analytics.alert_category AS ENUM (
    'billing',
    'revenue',
    'retention',
    'acquisition',
    'integration'
);

CREATE TABLE analytics.alerts (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id     UUID NOT NULL
        REFERENCES core.companies(id) ON DELETE CASCADE,

    severity       analytics.alert_severity NOT NULL,
    category       analytics.alert_category NOT NULL,

    message        TEXT NOT NULL,

    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at    TIMESTAMPTZ,

    -- Optional: store some raw metrics that triggered the alert for debugging
    context        JSONB
);

CREATE INDEX alerts_company_created_idx
    ON analytics.alerts (company_id, created_at DESC);

CREATE INDEX alerts_severity_idx
    ON analytics.alerts (severity);


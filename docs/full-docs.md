Here’s a self-contained overview you can hand to another AI as “project docs”.

---

# Ace Portfolio Intelligence – Project Documentation (Summary)

## 1. Product Overview

**Working name:** Ace Portfolio Intelligence
**Context:** Internal analytics product for Ace Ventures (VC / fintech investor).

**Core idea:**
Aggregate data from portfolio companies’ tools (starting with Stripe and GA4) into a single platform to:

* Evaluate **company health** (MRR, growth, churn, NRR).
* Understand **retention & cohorts**.
* Analyze **unit economics** (LTV, CAC, payback) once marketing data is integrated.
* Provide **portfolio-level** insights and alerts for Ace partners.

We are currently in an **early backend + UI prototype** stage:

* Backend: FastAPI service that connects to Stripe and GA4 via OAuth and can fetch basic data.
* Frontend: Next.js 13+ App Router project with mock-data dashboards that reflect the target UX.

---

## 2. High-Level Architecture

### 2.1. Current scope

* **Backend** (Python, FastAPI)

  * OAuth flows + token storage (in-memory for now) for:

    * Stripe (Connect OAuth)
    * Google Analytics 4 (Google OAuth + GA4 Data API)
  * Simple read endpoints:

    * Stripe: list charges for a connected account.
    * GA4: run a basic report (activeUsers by channel).

* **Frontend** (Next.js + React)

  * React Query + Recharts-based dashboard UI.
  * Currently uses **mock data** for:

    * Portfolio view
    * Company overview (MRR, NRR, churn, etc.)
  * Designed to be wired later to real backend endpoints with minimal changes.

### 2.2. Future architecture (planned)

* Introduce a **persistent DB** (likely Postgres) with canonical schemas:

  * `company`, `integration_account`, `customer`, `product`, `price`, `subscription`, `subscription_item`, `invoice`, `revenue_event`, etc.
* Build **ingestion jobs**:

  * Pull + upsert data from Stripe (and later GA4, Ads, HubSpot…).
* Compute **derived metrics & aggregates**:

  * Per-company & per-portfolio metrics (MRR, ARR, NRR, churn, cohort retention).
* Replace mock data in UI with real API endpoints.

---

## 3. Backend (FastAPI) – Details

### 3.1. Tech stack

* **Language:** Python
* **Framework:** FastAPI
* **Auth & API clients:**

  * `stripe` Python SDK
  * `requests` for Google OAuth + GA4 Data API
* **Config:** `python-dotenv` for `.env` loading
* **CORS:** `fastapi.middleware.cors.CORSMiddleware`

### 3.2. Environment variables

**Stripe:**

* `STRIPE_SECRET_KEY` – platform secret key (`sk_...`)
* `STRIPE_CLIENT_ID` – Stripe Connect client ID (`ca_...`)

**Google / GA4:**

* `GOOGLE_CLIENT_ID`
* `GOOGLE_CLIENT_SECRET`
* `GOOGLE_REDIRECT_URI` – e.g. `http://localhost:8000/ga/oauth/callback`
* `GA4_PROPERTY_ID` – numeric GA4 property ID
* `GA_SCOPE` – `https://www.googleapis.com/auth/analytics.readonly` (constant in code)

**Frontend redirect:**

* `FRONTEND_URL` – e.g. `http://localhost:5173` (or `http://localhost:3000` depending on frontend)

### 3.3. Backend structure (conceptual)

We discussed this structure (actual code is close to this):

```text
backend/
  app/
    main.py                 # FastAPI app, includes routers
    core/
      config.py             # Settings & env validation
    api/
      routes/
        health.py           # /health
        stripe.py           # Stripe OAuth + charges endpoints
        ga.py               # GA4 OAuth + basic report endpoints
    integrations/
      stripe_oauth.py       # Stripe OAuth + helper functions
      ga4_oauth.py          # Google OAuth + GA4 report helpers
    storage/
      connections.py        # In-memory token stores (for now)
```

### 3.4. Config object

In `core/config.py`, we centralize loading and validating env vars:

* `Settings` class with attributes:

  * `STRIPE_SECRET_KEY`, `STRIPE_CLIENT_ID`
  * `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`
  * `GA4_PROPERTY_ID`
  * `FRONTEND_URL`
  * `GA_SCOPE`
* `settings.validate()` throws if required vars are missing.

### 3.5. In-memory token storage (to be replaced by DB)

In `storage/connections.py`:

* `GA_CONNECTIONS: Dict[str, Dict[str, Any]]`
* `STRIPE_CONNECTED_ACCOUNTS: Dict[str, Dict[str, Any]]`
* Helper functions:

  * `save_ga_tokens(connection_id, tokens)`
  * `get_ga_access_token(connection_id)`
  * `save_stripe_account(account_id, data)`
  * `get_stripe_access_token(account_id)`

**Note:** This is **demo-only**, to be replaced with a real `integration_account` table.

### 3.6. Stripe integration (OAuth + charges)

**Usage pattern:**

1. Frontend calls `/stripe/oauth/url` to get a Connect URL.
2. User logs into Stripe & approves.
3. Stripe redirects to `/stripe/oauth/callback?code=...`.
4. Backend exchanges `code` for tokens and stores them (in-memory).
5. Frontend can then call `/stripe/{account_id}/charges` to list charges.

**Key functions:**

In `integrations/stripe_oauth.py`:

* `build_stripe_oauth_url(state: str) -> str`

  * Builds URL: `https://connect.stripe.com/oauth/authorize?...`
  * Uses `STRIPE_CLIENT_ID`, `redirect_uri`, `scope="read_write"`.

* `handle_stripe_oauth_callback(code: str) -> account_id`

  * Calls `stripe.OAuth.token(grant_type="authorization_code", code=code)`.
  * Extracts `stripe_user_id` (account id) and tokens.
  * Stores in `STRIPE_CONNECTED_ACCOUNTS`.

* `list_charges_for_account(account_id: str, limit: int)`

  * Uses the connected account’s `access_token` as `api_key` in `stripe.Charge.list`.

**Endpoints in `api/routes/stripe.py`:**

* `GET /stripe/oauth/url`

  * Returns `{ url: "<connect-oauth-url>" }`.

* `GET /stripe/oauth/callback`

  * Handles `code` and `error`.
  * On success: redirects to `${FRONTEND_URL}/integrations/stripe/success?account_id=<acct_...>`.

* `GET /stripe/{account_id}/charges?limit=N`

  * Returns `{ items: [...] }` (list of Stripe charges).

### 3.7. GA4 integration (OAuth + basic report)

**Usage pattern:**

1. Frontend calls `/ga/oauth/url` to get Google OAuth URL.
2. User logs in, grants Analytics read access.
3. Google redirects to `/ga/oauth/callback?code=...`.
4. Backend exchanges `code` for tokens and stores them (in-memory under `connection_id="default"`).
5. Frontend can then call `/ga/default/basic-report?days=N` to get a GA4 report.

**Key functions in `integrations/ga4_oauth.py`:**

* `build_ga_oauth_url(state: str) -> str`

  * Builds Google OAuth URL with:

    * `scope=analytics.readonly`
    * `access_type=offline`
    * `prompt=consent` (to get refresh token).

* `exchange_ga_code_for_tokens(code: str) -> connection_id`

  * POST to `https://oauth2.googleapis.com/token` with:

    * `grant_type=authorization_code`
    * `client_id`, `client_secret`, `redirect_uri`.
  * Stores resulting tokens in `GA_CONNECTIONS["default"]`.
  * Returns `"default"`.

* `run_basic_ga_report(connection_id: str, days: int)`

  * Uses GA4 Data API `runReport` endpoint:

    * URL: `https://analyticsdata.googleapis.com/v1beta/properties/{GA4_PROPERTY_ID}:runReport`
    * Example request body:

      * `dateRanges: [{ startDate: "<N>daysAgo", endDate: "today" }]`
      * `dimensions: [{ name: "sessionDefaultChannelGroup" }]`
      * `metrics: [{ name: "activeUsers" }]`
  * Auth with `Authorization: Bearer <access_token>`.

**Endpoints in `api/routes/ga.py`:**

* `GET /ga/oauth/url`

  * Returns `{ url: "<google-oauth-url>" }`.

* `GET /ga/oauth/callback`

  * Handles `code` and `error`.
  * On success: redirects to `${FRONTEND_URL}/integrations/ga4/success?connection_id=default`.

* `GET /ga/{connection_id}/basic-report?days=N`

  * Returns raw GA4 `runReport` JSON.

---

## 4. Data Model – Planned Canonical Schema (High-Level)

Planned Postgres-style tables (not yet fully implemented; this is the target schema other AIs can build towards):

* `company`

  * Represents one portfolio company (tenant).

* `integration_account`

  * Links a `company` to a provider (e.g., Stripe).
  * Stores tokens/credentials (encrypted at app layer).
  * Fields: `company_id`, `provider`, `provider_account_id`, `access_token`, `refresh_token`, `scope`, `livemode`.

* `customer`

  * End-customer paying the portfolio company.
  * Key fields: `company_id`, `external_id` (e.g. Stripe `cus_...`), `external_source="stripe"`, `email`, `name`, `country`, `created_at`, `metadata`.

* `product` & `price`

  * From Stripe `Product` & `Price`.
  * Represent plans / SKUs with pricing and intervals.

* `subscription` & `subscription_item`

  * Represent recurring relationships.
  * Key fields: `status`, `started_at`, `canceled_at`, `current_period_start`, `current_period_end`.

* `invoice`

  * Represents billed amounts, whether paid, due, etc.

* `revenue_event`

  * Central **fact table**: payments + refunds.
  * Fields:

    * `external_id`, `external_type` (`'charge'`, `'refund'`, `'invoice_payment'`).
    * Links: `customer_id`, `subscription_id`, `invoice_id`.
    * `occurred_at`, `amount`, `currency`, `status`, `is_recurring`.
  * Used for revenue over time, LTV, cohort revenue retention.

* (Later) `balance_transaction`

  * For fees and cash-based KPIs.

This schema is designed to support:

* Per-company metrics: MRR, ARR, churn, NRR, cohorts.
* Portfolio-level aggregation: ranking companies by growth, NRR, etc.

---

## 5. Frontend (Next.js) – Details

### 5.1. Tech stack

* **Framework:** Next.js (App Router, `src/app`).
* **Language:** TypeScript.
* **State / data:** `@tanstack/react-query`.
* **Charts:** `recharts`.
* **Styling:** Tailwind-like utility classes used in examples (can be swapped / refined).

### 5.2. Current routing / pages

Using the App Router:

* `src/app/layout.tsx`

  * Wraps all pages with `<Providers>` (React Query).
  * Basic global styles (dark background etc.).

* `src/app/providers.tsx`

  * `"use client"` component.
  * Wraps children with `<QueryClientProvider>`.

* `src/app/page.tsx`

  * Redirects `/` → `/portfolio`.

* `src/app/portfolio/page.tsx`

  * **Portfolio overview** page.
  * Uses `usePortfolioMetrics` hook with mock data.
  * Shows:

    * Summary text (company count, total ARR).
    * Table of companies (name, ARR, growth, NRR, churn, health).
  * Each company row links to its overview at `/companies/[companyId]/overview`.

* `src/app/companies/[companyId]/overview/page.tsx`

  * **Company overview** page.
  * Uses `useCompanyOverview(companyId, filters)` with mock data.
  * Displays:

    * KPI cards: MRR, ARR, NRR, active customers, churn rate.
    * MRR movements chart (stacked area by new/expansion/contraction/churn).

### 5.3. Types & mock data

`src/types/metrics.ts` defines shared types:

* `TimeRangeKey`, `OverviewFilters`
* `MrrSeriesPoint`
* `CompanyOverviewMetrics`
* `PortfolioCompanyRow`
* `PortfolioMetrics`

`src/mocks/companyOverview.ts`:

* Single `MOCK_COMPANY_OVERVIEW: CompanyOverviewMetrics` with sample MRR series.

`src/mocks/portfolioMetrics.ts`:

* `MOCK_PORTFOLIO_METRICS: PortfolioMetrics` with:

  * `totalArr`, `avgNrrPercent`, `companyCount`
  * A small list of `companies` with ARR, growth, NRR, etc.

### 5.4. Hooks (React Query + mock data)

All hooks are client components (`"use client"`).

* `useCompanyOverview(companyId, filters)`

  * Query key: `["companyOverview", companyId, filters]`.
  * Returns `CompanyOverviewMetrics` after a fake delay (simulated network).
  * For now: returns `MOCK_COMPANY_OVERVIEW` overridden with `companyId`.

* `usePortfolioMetrics()`

  * Query key: `["portfolioMetrics"]`.
  * Returns `MOCK_PORTFOLIO_METRICS` after fake delay.

Later, these `queryFn` functions will be replaced with real `fetch` calls to FastAPI endpoints (e.g., `/api/company/:id/overview`, `/api/portfolio/metrics`), with the same return types.

### 5.5. Components

**KPI card**
`src/components/kpis/KpiCard.tsx`:

* Small reusable card with:

  * Label (e.g. “MRR”)
  * Main value (e.g. `$17,000`)
  * Optional helper text (e.g. `▲ 13.3% vs prev`)

**MRR area chart**
`src/components/charts/MrrAreaChart.tsx` (Recharts):

* Renders an `AreaChart` with `MrrSeriesPoint[]`:

  * X-axis: `date`
  * Stacked areas:

    * `new`
    * `expansion`
    * `contraction`
    * `churn`

These are wired into the Company overview page.

---

## 6. How Everything Connects (Intended Flow)

1. **Integrations:**

   * User (founder or Ace) connects their company’s Stripe and GA4 accounts to the backend using OAuth.
   * Backend stores provider tokens associated with an `integration_account` (currently in-memory dicts).

2. **Ingestion (future work):**

   * Background tasks periodically fetch Stripe data (customers, subscriptions, invoices, charges) and insert into canonical DB tables.
   * Later, GA4 & other tools are integrated the same way.

3. **Metrics computation (future work):**

   * Queries / materialized views compute:

     * MRR, ARR, NRR, churn, LTV, etc.
     * Portfolio-level aggregates.

4. **Frontend:**

   * Calls API endpoints via React Query hooks to get:

     * Portfolio metrics.
     * Company-level overview & detailed metrics.
   * Renders dashboards (KPI cards, MRR charts, cohorts, acquisition performance).

5. **Current prototype:**

   * Backend OAuth flows + simple Stripe/GA4 read endpoints are working.
   * Frontend uses mock data but has the **final UX shape** for portfolio + company overview pages.

---

## 7. Suggested Workstreams for Another AI

If you hand this doc to another AI, here are good independent threads:

1. **Backend – DB & ingestion**

   * Design and implement the canonical schema in Postgres (tables listed above).
   * Implement a `sync_stripe(company_id)` job that:

     * Uses `integration_account` tokens.
     * Fetches Stripe objects and upserts into DB.
   * Expose a `/companies/{id}/overview` API that:

     * Computes and returns `CompanyOverviewMetrics` from DB.

2. **Backend – GA4 integration**

   * Wrap `run_basic_ga_report` in a more generic GA4 service.
   * Plan & implement mapping of GA4 data into a canonical acquisition/events model.

3. **Frontend – API wiring**

   * Replace mock hooks (`useCompanyOverview`, `usePortfolioMetrics`) with real `fetch` calls.
   * Add error & loading skeletons; add filter controls (time range, segments).

4. **Frontend – additional pages**

   * Implement `CompanyRevenuePage`, `CompanyCohortsPage`, `CompanyAcquisitionPage` using the same patterns (types + hooks + Recharts).

5. **Security & persistence**

   * Replace in-memory token stores with:

     * `integration_account` table.
     * Encryption at rest for tokens.
   * Add basic auth / multi-tenant context on the backend.

---

You can paste this entire document into another AI and say something like:

> “This is the current state & design of our Ace Portfolio Intelligence project. Use it as context to implement X (e.g., the Stripe ingestion pipeline, or new frontend pages).”

That should give it enough structure to work without re-deriving everything from scratch.

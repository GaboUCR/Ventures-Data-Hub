# app/api/routes/companies.py
from __future__ import annotations

from datetime import date, timedelta
from enum import Enum
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, func, and_
from sqlalchemy.exc import SQLAlchemyError
from statistics import median

from app.api.deps.auth import get_current_user, CurrentUser
from app.db.session import engine
from app.db.tables import (
    companies,
    company_monthly_metrics,
    billing_daily,
    acquisition_daily,
    plan_monthly_metrics,
    retention_cohorts,
    pre_churn_insights,
)


router = APIRouter(prefix="/companies", tags=["companies"])


# --------- Types for query params / responses ---------

class TimeRange(str, Enum):
    last_30_days = "last_30_days"
    last_90_days = "last_90_days"
    last_12_months = "last_12_months"


class MrrSeriesPoint(BaseModel):
    date: date
    total: float
    new: float
    expansion: float
    contraction: float
    churn: float


class CompanyOverviewResponse(BaseModel):
    companyName: str
    currency: str

    mrr: float
    arr: float
    mrrChangePercent: float
    arrChangePercent: float
    nrrPercent: float
    activeCustomers: int
    churnRatePercent: float

    mrrSeries: List[MrrSeriesPoint]


class TrafficSnapshot(BaseModel):
    sessions: int
    signups: int
    signupConversionRate: float


class BillingSnapshot(BaseModel):
    paymentSuccessRate: float
    atRiskMrr: float
    refundRate: float


class OverviewSnapshotsResponse(BaseModel):
    traffic: TrafficSnapshot
    billing: BillingSnapshot


class PlanRow(BaseModel):
    planId: str
    planName: str
    mrr: float
    subscribers: int
    churnRatePercent: float
    growthRatePercent: float


class RevenueResponse(BaseModel):
    currency: str
    mrr: float
    newMrr: float
    expansionMrr: float
    churnedMrr: float
    mrrSeries: List[MrrSeriesPoint]
    plans: List[PlanRow]

class CohortCell(BaseModel):
    cohortMonth: date
    monthIndex: int          # months since signup
    retainedPercent: float   # 0–100


class CohortsResponse(BaseModel):
    retention6mPercent: float
    retention12mPercent: float
    medianTimeToChurnMonths: float
    heatmap: list[CohortCell]
    preChurnInsights: list[str]

# --------- Helpers ---------

def _ensure_company_access(company_id: str, user: CurrentUser) -> None:
    """
    Very simple access rule for now:
    - Ace admin (global_role == 'admin') can see any company
    - Company user can only see their own company_id from token
    """
    if user.global_role == "admin":
        return
    if not user.company_id or user.company_id != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to access this company",
        )


def _compute_start_date(time_range: TimeRange) -> date:
    today = date.today()
    if time_range == TimeRange.last_30_days:
        return today - timedelta(days=30)
    if time_range == TimeRange.last_90_days:
        return today - timedelta(days=90)
    if time_range == TimeRange.last_12_months:
        return today - timedelta(days=365)
    return today - timedelta(days=90)


def _safe_pct_change(current: float, previous: float | None) -> float:
    if previous is None or previous == 0:
        return 0.0
    return (current - previous) / previous * 100.0


# --------- /companies/{id}/overview ---------

@router.get("/{company_id}/overview", response_model=CompanyOverviewResponse)
def get_company_overview(
    company_id: str,
    time_range: TimeRange = Query(TimeRange.last_90_days),
    currency: str = Query("USD"),
    current_user: CurrentUser = Depends(get_current_user),
):
    _ensure_company_access(company_id, current_user)

    start_date = _compute_start_date(time_range)
    start_month = date(start_date.year, start_date.month, 1)

    try:
        with engine.begin() as conn:
            # 1) Company name
            c_stmt = select(companies.c.name).where(companies.c.id == company_id)
            c_row = conn.execute(c_stmt).first()
            if not c_row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Company not found",
                )
            company_name = c_row.name

            # 2) Monthly metrics for this company (all rows, ordered by month)
            m_stmt = (
                select(company_monthly_metrics)
                .where(company_monthly_metrics.c.company_id == company_id)
                .order_by(company_monthly_metrics.c.month.asc())
            )
            m_rows = conn.execute(m_stmt).all()

            if not m_rows:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No metrics found for this company",
                )

            # Last row = most recent month
            last = m_rows[-1]
            prev = m_rows[-2] if len(m_rows) >= 2 else None

            # 3) Filter months for the requested range for the chart
            series_rows = [r for r in m_rows if r.month >= start_month]
            if not series_rows:
                # fallback to last up to 12 months
                series_rows = m_rows[-12:]

    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"DB error fetching overview: {e}",
        )

    # Convert cents to currency units
    last_mrr = (last.mrr_cents or 0) / 100.0
    last_arr = (last.arr_cents or 0) / 100.0
    prev_mrr = (prev.mrr_cents or 0) / 100.0 if prev else None
    prev_arr = (prev.arr_cents or 0) / 100.0 if prev else None

    mrr_change = _safe_pct_change(last_mrr, prev_mrr)
    arr_change = _safe_pct_change(last_arr, prev_arr)

    series: list[MrrSeriesPoint] = []
    for r in series_rows:
        series.append(
            MrrSeriesPoint(
                date=r.month,
                total=(r.mrr_cents or 0) / 100.0,
                new=(r.new_mrr_cents or 0) / 100.0,
                expansion=(r.expansion_mrr_cents or 0) / 100.0,
                contraction=(r.contraction_mrr_cents or 0) / 100.0,
                churn=(r.churned_mrr_cents or 0) / 100.0,
            )
        )

    return CompanyOverviewResponse(
        companyName=company_name,
        currency=last.currency or currency,
        mrr=last_mrr,
        arr=last_arr,
        mrrChangePercent=mrr_change,
        arrChangePercent=arr_change,
        nrrPercent=float(last.nrr_percent or 0.0),
        activeCustomers=int(last.active_customers or 0),
        churnRatePercent=float(last.churn_rate_percent or 0.0),
        mrrSeries=series,
    )


@router.get("/{company_id}/overview/snapshots", response_model=OverviewSnapshotsResponse)
def get_company_overview_snapshots(
    company_id: str,
    time_range: TimeRange = Query(TimeRange.last_90_days),
    current_user: CurrentUser = Depends(get_current_user),
):
    _ensure_company_access(company_id, current_user)

    start_date = _compute_start_date(time_range)
    today = date.today()

    try:
        with engine.begin() as conn:
            # --- Traffic (GA4 → acquisition_daily) ---
            a_stmt = (
                select(
                    func.coalesce(func.sum(acquisition_daily.c.sessions), 0).label("sessions"),
                    func.coalesce(func.sum(acquisition_daily.c.signups), 0).label("signups"),
                )
                .where(acquisition_daily.c.company_id == company_id)
                .where(
                    and_(
                        acquisition_daily.c.date >= start_date,
                        acquisition_daily.c.date <= today,
                    )
                )
            )
            a_row = conn.execute(a_stmt).first()
            sessions = int(a_row.sessions or 0)
            signups = int(a_row.signups or 0)

            # --- Billing (Stripe → billing_daily) ---
            b_stmt = (
                select(
                    func.coalesce(func.sum(billing_daily.c.payment_attempts), 0).label("attempts"),
                    func.coalesce(func.sum(billing_daily.c.payment_success), 0).label("success"),
                    func.coalesce(func.sum(billing_daily.c.payment_failed), 0).label("failed"),
                    func.coalesce(func.sum(billing_daily.c.refunds_cents), 0).label("refunds_cents"),
                    func.coalesce(func.max(billing_daily.c.mrr_at_risk_cents), 0).label("at_risk_cents"),
                )
                .where(billing_daily.c.company_id == company_id)
                .where(
                    and_(
                        billing_daily.c.date >= start_date,
                        billing_daily.c.date <= today,
                    )
                )
            )
            b_row = conn.execute(b_stmt).first()

    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"DB error fetching snapshots: {e}",
        )

    # Traffic snapshot
    if sessions > 0:
        signup_conversion = (signups / sessions) * 100.0
    else:
        signup_conversion = 0.0

    traffic = TrafficSnapshot(
        sessions=sessions,
        signups=signups,
        signupConversionRate=signup_conversion,
    )

    # Billing snapshot
    attempts = int(b_row.attempts or 0)
    success = int(b_row.success or 0)
    refunds_cents = int(b_row.refunds_cents or 0)
    at_risk_cents = int(b_row.at_risk_cents or 0)

    if attempts > 0:
        payment_success_rate = (success / attempts) * 100.0
    else:
        payment_success_rate = 0.0

    # Very simple refund rate: refunds vs attempts (can refine later)
    if attempts > 0:
        refund_rate = (refunds_cents / max(attempts, 1))  # arbitrary; TODO refine
    else:
        refund_rate = 0.0

    billing = BillingSnapshot(
        paymentSuccessRate=payment_success_rate,
        atRiskMrr=at_risk_cents / 100.0,
        refundRate=refund_rate,
    )

    return OverviewSnapshotsResponse(
        traffic=traffic,
        billing=billing,
    )


@router.get("/{company_id}/revenue", response_model=RevenueResponse)
def get_company_revenue(
    company_id: str,
    time_range: TimeRange = Query(TimeRange.last_90_days),
    currency: str = Query("USD"),
    current_user: CurrentUser = Depends(get_current_user),
):
    _ensure_company_access(company_id, current_user)

    start_date = _compute_start_date(time_range)
    start_month = date(start_date.year, start_date.month, 1)

    try:
        with engine.begin() as conn:
            # 1) Monthly metrics (same base as overview)
            m_stmt = (
                select(company_monthly_metrics)
                .where(company_monthly_metrics.c.company_id == company_id)
                .order_by(company_monthly_metrics.c.month.asc())
            )
            m_rows = conn.execute(m_stmt).all()

            if not m_rows:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No revenue metrics found for this company",
                )

            last = m_rows[-1]
            series_rows = [r for r in m_rows if r.month >= start_month]
            if not series_rows:
                series_rows = m_rows[-12:]

            # 2) Plan metrics
            p_stmt = (
                select(plan_monthly_metrics)
                .where(plan_monthly_metrics.c.company_id == company_id)
                .order_by(plan_monthly_metrics.c.month.asc())
            )
            p_rows = conn.execute(p_stmt).all()

    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"DB error fetching revenue: {e}",
        )

    # ---- Headline KPIs (from last monthly metrics row) ----
    last_mrr = (last.mrr_cents or 0) / 100.0
    new_mrr = (last.new_mrr_cents or 0) / 100.0
    expansion_mrr = (last.expansion_mrr_cents or 0) / 100.0
    churned_mrr = (last.churned_mrr_cents or 0) / 100.0

    cur_currency = last.currency or currency

    # ---- Series for chart ----
    series: list[MrrSeriesPoint] = []
    for r in series_rows:
        series.append(
            MrrSeriesPoint(
                date=r.month,
                total=(r.mrr_cents or 0) / 100.0,
                new=(r.new_mrr_cents or 0) / 100.0,
                expansion=(r.expansion_mrr_cents or 0) / 100.0,
                contraction=(r.contraction_mrr_cents or 0) / 100.0,
                churn=(r.churned_mrr_cents or 0) / 100.0,
            )
        )

    # ---- Plan performance (latest month only) ----
    plan_rows: list[PlanRow] = []
    if p_rows:
        latest_month = max(r.month for r in p_rows)
        latest_plans = [r for r in p_rows if r.month == latest_month]

        for r in latest_plans:
            plan_rows.append(
                PlanRow(
                    planId=r.plan_id,
                    planName=r.plan_name,
                    mrr=(r.mrr_cents or 0) / 100.0,
                    subscribers=int(r.subscribers or 0),
                    churnRatePercent=float(r.churn_rate_percent or 0.0),
                    growthRatePercent=float(r.growth_rate_percent or 0.0),
                )
            )

    return RevenueResponse(
        currency=cur_currency,
        mrr=last_mrr,
        newMrr=new_mrr,
        expansionMrr=expansion_mrr,
        churnedMrr=churned_mrr,
        mrrSeries=series,
        plans=plan_rows,
    )

@router.get("/{company_id}/cohorts", response_model=CohortsResponse)
def get_company_cohorts(
    company_id: str,
    time_range: TimeRange = Query(TimeRange.last_12_months),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Returns:
    - 6-month retention (avg of cohorts with at least 6 months)
    - 12-month retention (avg of cohorts with at least 12 months)
    - Median time to churn (month when retention drops <= 50%, across cohorts)
    - Cohort heatmap cells
    - Simple pre-churn insights (top N rows from pre_churn_insights)
    """
    _ensure_company_access(company_id, current_user)

    start_date = _compute_start_date(time_range)
    start_cohort_month = date(start_date.year, start_date.month, 1)

    try:
        with engine.begin() as conn:
            # 1) All cohort rows for this company
            rc_stmt = (
                select(retention_cohorts)
                .where(retention_cohorts.c.company_id == company_id)
                .order_by(
                    retention_cohorts.c.cohort_month.asc(),
                    retention_cohorts.c.months_since_signup.asc(),
                )
            )
            rc_rows = conn.execute(rc_stmt).all()

            # Optional: filter out very old cohorts, keep last ~12–18
            rc_rows = [r for r in rc_rows if r.cohort_month >= start_cohort_month]

            # 2) Pre-churn insights
            pci_stmt = (
                select(pre_churn_insights.c.text)
                .where(pre_churn_insights.c.company_id == company_id)
                .order_by(pre_churn_insights.c.rank.asc())
                .limit(5)
            )
            pci_rows = conn.execute(pci_stmt).all()

    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"DB error fetching cohorts: {e}",
        )

    if not rc_rows:
        # No cohort data yet
        return CohortsResponse(
            retention6mPercent=0.0,
            retention12mPercent=0.0,
            medianTimeToChurnMonths=0.0,
            heatmap=[],
            preChurnInsights=[r.text for r in pci_rows],
        )

    # ---- Build heatmap ----
    heatmap: list[CohortCell] = []
    for r in rc_rows:
        heatmap.append(
            CohortCell(
                cohortMonth=r.cohort_month,
                monthIndex=int(r.months_since_signup),
                retainedPercent=float(r.mrr_retained_percent or 0.0),
            )
        )

    # ---- Compute 6m and 12m retention ----
    def avg_retention_at(month_index: int) -> float:
        values: list[float] = []
        for r in rc_rows:
            if int(r.months_since_signup) == month_index and r.mrr_retained_percent is not None:
                values.append(float(r.mrr_retained_percent))
        if not values:
            return 0.0
        return sum(values) / len(values)

    retention_6m = avg_retention_at(6)
    retention_12m = avg_retention_at(12)

    # ---- Median time to churn (retention <= 50%) ----
    cohorts_by_month: dict[date, list] = {}
    for r in rc_rows:
        cohorts_by_month.setdefault(r.cohort_month, []).append(r)

    churn_months: list[float] = []
    for cohort_month, rows in cohorts_by_month.items():
        # sort by months_since_signup
        ordered = sorted(rows, key=lambda row: row.months_since_signup)
        churn_point: float | None = None
        for row in ordered:
            if row.mrr_retained_percent is None:
                continue
            if float(row.mrr_retained_percent) <= 50.0:
                churn_point = float(row.months_since_signup)
                break
        if churn_point is not None:
            churn_months.append(churn_point)

    if churn_months:
        median_churn = float(median(churn_months))
    else:
        median_churn = 0.0

    pre_churn_texts = [r.text for r in pci_rows]

    return CohortsResponse(
        retention6mPercent=retention_6m,
        retention12mPercent=retention_12m,
        medianTimeToChurnMonths=median_churn,
        heatmap=heatmap,
        preChurnInsights=pre_churn_texts,
    )

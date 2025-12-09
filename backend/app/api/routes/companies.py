# app/api/routes/companies.py
from __future__ import annotations

from datetime import date, timedelta
from enum import Enum
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, func, and_
from sqlalchemy.exc import SQLAlchemyError

from app.api.deps.auth import get_current_user, CurrentUser
from app.db.session import engine
from app.db.tables import (
    companies,
    company_monthly_metrics,
    billing_daily,
    acquisition_daily,
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

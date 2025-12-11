# app/api/routes/portfolio.py
from datetime import date
from statistics import median
from typing import Literal, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.api.deps.auth import get_current_user, CurrentUser
from app.db.session import engine
from app.db.tables import companies, company_monthly_metrics

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


class PortfolioCompanyRow(BaseModel):
    companyId: str
    companyName: str
    stage: str | None = None
    sector: str | None = None
    mrr: float
    arr: float
    growthPercent: float
    nrrPercent: float
    churnRatePercent: float
    category: Literal["rocketship", "leaky_bucket", "flat_but_solid", "at_risk"]


class PortfolioSummary(BaseModel):
    totalCompanies: int
    rocketships: int
    leakyBuckets: int
    flatButSolid: int
    atRisk: int
    portfolioArr: float
    medianGrowthPercent: float
    medianNrrPercent: float


class PortfolioOverviewResponse(BaseModel):
    summary: PortfolioSummary
    companies: list[PortfolioCompanyRow]


def _ensure_portfolio_access(user: CurrentUser) -> None:
    # Adjust if your CurrentUser model uses a different field name
    role = getattr(user, "global_role", None) or getattr(user, "role", None)
    if role not in ("admin", "ace_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to view the portfolio.",
        )


def _classify_company(
    growth: float, nrr: float, churn: float
) -> Literal["rocketship", "leaky_bucket", "flat_but_solid", "at_risk"]:
    """
    Simple heuristic:
    - Rocketship: growth >= 10% AND NRR >= 120% AND churn <= 5%
    - Leaky bucket: growth >= 10% AND NRR < 100%
    - Flat but solid: growth < 10% AND NRR >= 110%
    - At risk: everything else
    """
    if growth >= 10.0 and nrr >= 120.0 and churn <= 5.0:
        return "rocketship"
    if growth >= 10.0 and nrr < 100.0:
        return "leaky_bucket"
    if growth < 10.0 and nrr >= 110.0:
        return "flat_but_solid"
    return "at_risk"


@router.get("/overview", response_model=PortfolioOverviewResponse)
def get_portfolio_overview(
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Portfolio-level view:
    - One row per company with latest metrics
    - Portfolio summary (counts by category, total ARR, median growth/NRR)
    """
    _ensure_portfolio_access(current_user)

    try:
        with engine.begin() as conn:
            # 1) Fetch all companies
            company_rows = conn.execute(
                select(
                    companies.c.id,
                    companies.c.name,
                    companies.c.stage,
                    companies.c.sector,
                )
            ).all()

            # 2) Fetch all monthly metrics
            metrics_rows = conn.execute(
                select(
                    company_monthly_metrics.c.company_id,
                    company_monthly_metrics.c.month,
                    company_monthly_metrics.c.mrr_cents,
                    company_monthly_metrics.c.arr_cents,
                    company_monthly_metrics.c.nrr_percent,
                    company_monthly_metrics.c.churn_rate_percent,
                )
            ).all()

    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"DB error fetching portfolio overview: {e}",
        )

    # Group metrics by company_id in Python
    metrics_by_company: Dict[str, List] = {}
    for r in metrics_rows:
        cid = str(r.company_id)
        metrics_by_company.setdefault(cid, []).append(r)

    companies_out: list[PortfolioCompanyRow] = []
    growth_values: list[float] = []
    nrr_values: list[float] = []
    total_arr = 0.0

    rocketships = 0
    leaky_buckets = 0
    flat_but_solid = 0
    at_risk = 0

    for c in company_rows:
        cid = str(c.id)
        mlist = metrics_by_company.get(cid)
        if not mlist:
            # No metrics for this company yet → skip from portfolio metrics
            continue

        # Sort by month ascending, so last two are prev & latest
        mlist_sorted = sorted(mlist, key=lambda r: r.month)
        latest = mlist_sorted[-1]
        prev = mlist_sorted[-2] if len(mlist_sorted) >= 2 else None

        latest_mrr = int(latest.mrr_cents or 0)
        latest_arr = int(latest.arr_cents or 0)
        nrr = float(latest.nrr_percent or 0.0)
        churn = float(latest.churn_rate_percent or 0.0)

        if prev:
            prev_mrr = int(prev.mrr_cents or 0)
            if prev_mrr > 0:
                growth = ((latest_mrr - prev_mrr) / prev_mrr) * 100.0
            else:
                growth = 0.0
        else:
            growth = 0.0

        category = _classify_company(growth, nrr, churn)

        if category == "rocketship":
            rocketships += 1
        elif category == "leaky_bucket":
            leaky_buckets += 1
        elif category == "flat_but_solid":
            flat_but_solid += 1
        else:
            at_risk += 1

        mrr_float = latest_mrr / 100.0
        arr_float = latest_arr / 100.0

        total_arr += arr_float
        growth_values.append(growth)
        nrr_values.append(nrr)

        companies_out.append(
            PortfolioCompanyRow(
                companyId=cid,
                companyName=c.name,
                stage=c.stage,
                sector=c.sector,
                mrr=mrr_float,
                arr=arr_float,
                growthPercent=growth,
                nrrPercent=nrr,
                churnRatePercent=churn,
                category=category,
            )
        )

    median_growth = float(median(growth_values)) if growth_values else 0.0
    median_nrr = float(median(nrr_values)) if nrr_values else 0.0

    summary = PortfolioSummary(
        totalCompanies=len(companies_out),
        rocketships=rocketships,
        leakyBuckets=leaky_buckets,
        flatButSolid=flat_but_solid,
        atRisk=at_risk,
        portfolioArr=total_arr,
        medianGrowthPercent=median_growth,
        medianNrrPercent=median_nrr,
    )

    return PortfolioOverviewResponse(summary=summary, companies=companies_out)

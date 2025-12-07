// src/app/portfolio/page.tsx
"use client";

import { useState, useMemo } from "react";
import Link from "next/link";

import { KpiCard } from "@/components/kpis/KpiCard";
import { PortfolioGrowthRetentionChart } from "@/components/charts/PortfolioGrowthRetentionChart";
import { PortfolioCompanyTable } from "@/components/table/PortfolioCompanyTable";
import { usePortfolioOverview } from "@/hooks/usePortfolioOverview";
import {
  PortfolioCompany,
  PortfolioAlert,
  PortfolioCompanyRow,
} from "@/types/metrics";import { PortfolioTable } from "@/components/portfolio/PortfolioTable";

import { usePortfolioMetrics } from "@/hooks/usePortfolioMetrics";

type StageFilter = "all" | "pre_seed" | "seed" | "series_a" | "series_b" | "other";
type IntegrationFilter = "all" | "stripe_and_ga4" | "stripe_only" | "ga4_only" | "none";
type OwnerFilter = "all" | "Julia" | "Marcos" | "Ana";

export default function PortfolioPage() {
  const { data, isLoading, error } = usePortfolioOverview();

  const [stageFilter, setStageFilter] = useState<StageFilter>("all");
  const [ownerFilter, setOwnerFilter] = useState<OwnerFilter>("all");
  const [integrationFilter, setIntegrationFilter] =
    useState<IntegrationFilter>("all");

  const currency = "USD";

  if (isLoading) return <div className="p-6">Loading portfolio…</div>;
  if (error || !data) return <div className="p-6 text-red-400">Failed to load portfolio.</div>;

  const filteredCompanies = useMemo(
    () => applyFilters(data.companies, { stageFilter, ownerFilter, integrationFilter }),
    [data.companies, stageFilter, ownerFilter, integrationFilter]
  );

  const tableRows: PortfolioCompanyRow[] = useMemo(
    () => filteredCompanies.map(toPortfolioCompanyRow),
    [filteredCompanies]
  );

  const summary = computeSummary(filteredCompanies);
  const integrationSummary = computeIntegrationSummary(filteredCompanies);
  const topPerformers = computeTopPerformers(filteredCompanies);
  const atRisk = computeAtRiskCompanies(filteredCompanies);
  const emerging = computeEmergingWinners(filteredCompanies);

  return (
    <div className="px-4 py-6 sm:px-6 lg:px-8">
      <div className="mx-auto flex max-w-6xl flex-col gap-6">
        {/* Header */}
        <header className="space-y-3 rounded-3xl border border-slate-800 bg-gradient-to-r from-emerald-500/10 via-sky-500/10 to-transparent p-5 shadow-sm">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h1 className="text-2xl font-semibold text-slate-50">
                Portfolio overview
              </h1>
              <p className="mt-1 text-sm text-slate-300">
                Cross-company view of growth, retention & billing health.
              </p>
            </div>
            <div className="text-xs text-slate-400">
              <Link href="/" className="hover:text-slate-200">
                Home
              </Link>
            </div>
          </div>

          {/* Top KPIs */}
          <section className="space-y-3">
            <h2 className="text-xs font-medium uppercase tracking-wide text-slate-400">
              Portfolio snapshot (filtered)
            </h2>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              <KpiCard
                label="Total ARR"
                value={`${currency} ${summary.totalArr.toLocaleString()}`}
                helper="Sum across filtered companies"
                tone="neutral"
              />
              <KpiCard
                label="Portfolio growth"
                value={`${summary.portfolioGrowthPercent.toFixed(1)}%`}
                helper="Average MRR growth rate"
                tone={summary.portfolioGrowthPercent >= 0 ? "positive" : "negative"}
              />
              <KpiCard
                label="Median NRR"
                value={`${summary.medianNrrPercent.toFixed(1)}%`}
                helper="Net revenue retention"
                tone={summary.medianNrrPercent >= 120 ? "positive" : "neutral"}
              />
              <KpiCard
                label="MRR at risk"
                value={`${currency} ${summary.totalMrrAtRisk.toLocaleString()}`}
                helper="From past-due invoices"
                tone={summary.totalMrrAtRisk === 0 ? "positive" : "negative"}
              />
            </div>
          </section>
        </header>

        {/* Filters + middle row */}
        <section className="grid gap-4 lg:grid-cols-[2fr,1.4fr]">
          {/* Left: chart */}
          <div className="space-y-3">
            <PortfolioGrowthRetentionChart companies={filteredCompanies} />
          </div>

          {/* Right: filters + integration summary + alerts summary */}
          <div className="space-y-4">
            {/* Filters */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 text-sm">
              <h3 className="mb-3 text-sm font-medium text-slate-100">
                Filters
              </h3>
              <div className="grid gap-3 md:grid-cols-3">
                <div className="space-y-1">
                  <label className="text-xs text-slate-400">Stage</label>
                  <select
                    value={stageFilter}
                    onChange={(e) =>
                      setStageFilter(e.target.value as StageFilter)
                    }
                    className="w-full rounded-xl border border-slate-700 bg-slate-900 px-2 py-1 text-xs text-slate-100"
                  >
                    <option value="all">All</option>
                    <option value="pre_seed">Pre-seed</option>
                    <option value="seed">Seed</option>
                    <option value="series_a">Series A</option>
                    <option value="series_b">Series B</option>
                    <option value="other">Other</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="text-xs text-slate-400">Owner</label>
                  <select
                    value={ownerFilter}
                    onChange={(e) =>
                      setOwnerFilter(e.target.value as OwnerFilter)
                    }
                    className="w-full rounded-xl border border-slate-700 bg-slate-900 px-2 py-1 text-xs text-slate-100"
                  >
                    <option value="all">All</option>
                    <option value="Julia">Julia</option>
                    <option value="Marcos">Marcos</option>
                    <option value="Ana">Ana</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="text-xs text-slate-400">Integrations</label>
                  <select
                    value={integrationFilter}
                    onChange={(e) =>
                      setIntegrationFilter(e.target.value as IntegrationFilter)
                    }
                    className="w-full rounded-xl border border-slate-700 bg-slate-900 px-2 py-1 text-xs text-slate-100"
                  >
                    <option value="all">All</option>
                    <option value="stripe_and_ga4">Stripe + GA4</option>
                    <option value="stripe_only">Stripe only</option>
                    <option value="ga4_only">GA4 only</option>
                    <option value="none">No integrations</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Integration completeness */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 text-sm text-slate-100">
              <h3 className="mb-2 text-sm font-medium">Integration completeness</h3>
              <p className="mb-3 text-xs text-slate-400">
                Within the current filter.
              </p>
              <div className="grid grid-cols-2 gap-3 text-xs">
                <StatPill
                  label="Stripe + GA4"
                  value={integrationSummary.stripeAndGa4}
                />
                <StatPill
                  label="Stripe only"
                  value={integrationSummary.stripeOnly}
                />
                <StatPill label="GA4 only" value={integrationSummary.ga4Only} />
                <StatPill label="No integrations" value={integrationSummary.none} />
              </div>
            </div>

            {/* Alerts summary (just count + quick list) */}
            <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 text-sm">
              <h3 className="mb-2 text-sm font-medium text-slate-100">
                Recent alerts
              </h3>
              <AlertsList alerts={data.alerts} />
            </div>
          </div>
        </section>

        {/* Bottom: three tables */}
        <section className="space-y-4">
          <div className="grid gap-4 lg:grid-cols-3">
            <div className="space-y-2">
              <h2 className="text-sm font-medium text-slate-200">Top performers</h2>
              <p className="text-xs text-slate-400">
                Strong growth & NRR, reasonably low churn.
              </p>
              <PortfolioCompanyTable
                companies={topPerformers}
                currency={currency}
                emptyLabel="No top performers in this segment (yet)."
              />
            </div>

            <div className="space-y-2">
              <h2 className="text-sm font-medium text-slate-200">At risk</h2>
              <p className="text-xs text-slate-400">
                High churn, low NRR or elevated MRR at risk.
              </p>
              <PortfolioCompanyTable
                companies={atRisk}
                currency={currency}
                emptyLabel="No clearly at-risk companies in this segment."
              />
            </div>

            <div className="space-y-2">
              <h2 className="text-sm font-medium text-slate-200">Emerging winners</h2>
              <p className="text-xs text-slate-400">
                Smaller ARR but strong growth & retention.
              </p>
              <PortfolioCompanyTable
                companies={emerging}
                currency={currency}
                emptyLabel="No emerging winners under current filters."
              />
            </div>
          </div>
          
          <div className="space-y-2">
            <h2 className="text-sm font-medium text-slate-200">All companies in view</h2>
            <p className="text-xs text-slate-400">
              Filtered portfolio list with ARR, growth, retention and overall health score
              for each company.
            </p>
            <PortfolioTable data={tableRows} />
          </div>

        </section>
      </div>
    </div>
  );
}

/* ── Helpers ───────────────────────────────────────────────────────────── */

function applyFilters(
  companies: PortfolioCompany[],
  {
    stageFilter,
    ownerFilter,
    integrationFilter,
  }: {
    stageFilter: StageFilter;
    ownerFilter: OwnerFilter;
    integrationFilter: IntegrationFilter;
  }
): PortfolioCompany[] {
  return companies.filter((c) => {
    if (stageFilter !== "all" && c.stage !== stageFilter) return false;
    if (ownerFilter !== "all" && c.owner !== ownerFilter) return false;

    if (integrationFilter !== "all") {
      const stripeConnected = c.integrations.stripe === "connected";
      const ga4Connected = c.integrations.ga4 === "connected";

      if (integrationFilter === "stripe_and_ga4" && !(stripeConnected && ga4Connected)) {
        return false;
      }
      if (integrationFilter === "stripe_only" && !(stripeConnected && !ga4Connected)) {
        return false;
      }
      if (integrationFilter === "ga4_only" && !(!stripeConnected && ga4Connected)) {
        return false;
      }
      if (integrationFilter === "none" && (stripeConnected || ga4Connected)) {
        return false;
      }
    }

    return true;
  });
}

function computeSummary(companies: PortfolioCompany[]) {
  if (companies.length === 0) {
    return {
      totalArr: 0,
      portfolioGrowthPercent: 0,
      medianNrrPercent: 0,
      totalMrrAtRisk: 0,
    };
  }

  const totalArr = companies.reduce((sum, c) => sum + c.arr, 0);
  const totalGrowth = companies.reduce((sum, c) => sum + c.mrrGrowthRatePercent, 0);
  const portfolioGrowthPercent = totalGrowth / companies.length;

  const sortedNrr = [...companies].map((c) => c.nrrPercent).sort((a, b) => a - b);
  const mid = Math.floor(sortedNrr.length / 2);
  const medianNrrPercent =
    sortedNrr.length % 2 === 0
      ? (sortedNrr[mid - 1] + sortedNrr[mid]) / 2
      : sortedNrr[mid];

  const totalMrrAtRisk = companies.reduce((sum, c) => sum + c.mrrAtRisk, 0);

  return {
    totalArr,
    portfolioGrowthPercent,
    medianNrrPercent,
    totalMrrAtRisk,
  };
}

function computeIntegrationSummary(companies: PortfolioCompany[]) {
  let stripeAndGa4 = 0;
  let stripeOnly = 0;
  let ga4Only = 0;
  let none = 0;

  companies.forEach((c) => {
    const stripe = c.integrations.stripe === "connected";
    const ga4 = c.integrations.ga4 === "connected";

    if (stripe && ga4) stripeAndGa4++;
    else if (stripe && !ga4) stripeOnly++;
    else if (!stripe && ga4) ga4Only++;
    else none++;
  });

  return {
    totalCompanies: companies.length,
    stripeAndGa4,
    stripeOnly,
    ga4Only,
    none,
  };
}

function computeTopPerformers(companies: PortfolioCompany[]) {
  const scored = companies
    .map((c) => ({
      company: c,
      score:
        c.mrrGrowthRatePercent * 0.4 +
        (c.nrrPercent - 100) * 0.4 -
        c.churnRatePercent * 0.2,
    }))
    .sort((a, b) => b.score - a.score);

  return scored.slice(0, 5).map((s) => s.company);
}

function computeAtRiskCompanies(companies: PortfolioCompany[]) {
  return companies
    .filter(
      (c) =>
        c.churnRatePercent > 8 ||
        c.nrrPercent < 100 ||
        c.paymentSuccessRate < 94 ||
        c.mrrGrowthRatePercent < 0 ||
        c.mrrAtRisk > c.mrr * 0.2
    )
    .sort((a, b) => b.mrrAtRisk - a.mrrAtRisk)
    .slice(0, 5);
}

function computeEmergingWinners(companies: PortfolioCompany[]) {
  return companies
    .filter(
      (c) =>
        c.arr < 1_000_000 &&
        c.mrrGrowthRatePercent > 20 &&
        c.nrrPercent >= 120 &&
        c.churnRatePercent <= 6
    )
    .sort((a, b) => b.mrrGrowthRatePercent - a.mrrGrowthRatePercent)
    .slice(0, 5);
}

/* ── Small UI helpers ─────────────────────────────────────────────────── */

function StatPill({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-xl border border-slate-700 bg-slate-900 px-3 py-2">
      <p className="text-[11px] text-slate-400">{label}</p>
      <p className="text-sm font-semibold text-slate-100">{value}</p>
    </div>
  );
}

function AlertsList({ alerts }: { alerts: PortfolioAlert[] }) {
  if (!alerts.length) {
    return (
      <p className="text-xs text-slate-400">
        No alerts for the selected companies.
      </p>
    );
  }

  return (
    <ul className="space-y-2 text-xs">
      {alerts.slice(0, 5).map((a) => (
        <li
          key={a.id}
          className="rounded-xl border border-slate-800 bg-slate-900/80 px-3 py-2"
        >
          <div className="mb-1 flex items-center justify-between gap-2">
            <span className="font-medium text-slate-100">{a.companyName}</span>
            <span className={severityBadgeClass(a.severity)}>
              {a.severity.toUpperCase()}
            </span>
          </div>
          <p className="text-slate-300">{a.message}</p>
        </li>
      ))}
    </ul>
  );
}

function severityBadgeClass(severity: PortfolioAlert["severity"]) {
  if (severity === "critical")
    return "inline-flex items-center rounded-full bg-red-500/20 px-2 py-0.5 text-[10px] font-semibold text-red-300";
  if (severity === "warning")
    return "inline-flex items-center rounded-full bg-amber-500/20 px-2 py-0.5 text-[10px] font-semibold text-amber-300";
  return "inline-flex items-center rounded-full bg-sky-500/20 px-2 py-0.5 text-[10px] font-semibold text-sky-300";
}

function toPortfolioCompanyRow(c: PortfolioCompany): PortfolioCompanyRow {
  return {
    companyId: c.id,
    companyName: c.name,
    arr: c.arr,
    growthRatePercent: c.mrrGrowthRatePercent,
    nrrPercent: c.nrrPercent,
    churnRatePercent: c.churnRatePercent,
    healthScore: computeHealthScore(c),
  };
}

function computeHealthScore(c: PortfolioCompany): number {
  // Simple composite score: growth + retention – churn, clamped 0–100
  const score =
    50 +
    c.mrrGrowthRatePercent * 0.4 +
    (c.nrrPercent - 100) * 0.3 -
    c.churnRatePercent * 0.3;

  return Math.max(0, Math.min(100, Math.round(score)));
}

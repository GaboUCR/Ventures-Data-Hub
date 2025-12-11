// src/app/portfolio/page.tsx
"use client";

import Link from "next/link";
import { usePortfolioOverview } from "@/hooks/usePortfolioOverview";
import { KpiCard } from "@/components/kpis/KpiCard";
import { PortfolioScatterChart } from "@/components/charts/PortfolioScatterChart";
import { PortfolioCompanyTable } from "@/components/table/PortfolioCompanyTable";

export default function PortfolioPage() {
  const { data, isLoading, error } = usePortfolioOverview();

  if (isLoading) return <div className="p-6">Loading portfolio…</div>;
  if (error || !data)
    return <div className="p-6 text-red-400">Failed to load portfolio.</div>;

  const { summary, companies } = data;

  return (
    <div className="px-4 py-6 sm:px-6 lg:px-8">
      <div className="mx-auto flex max-w-6xl flex-col gap-6">
        {/* Header */}
        <header className="space-y-3 rounded-3xl border border-slate-800 bg-gradient-to-r from-emerald-500/10 via-sky-500/10 to-transparent p-5 shadow-sm">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h1 className="text-2xl font-semibold text-slate-50">
                Ace portfolio
              </h1>
              <p className="mt-1 text-sm text-slate-300">
                Health view across all companies
              </p>
            </div>
          </div>
        </header>

        {/* Top KPIs */}
        <section className="space-y-3">
          <h2 className="text-sm font-medium text-slate-200">
            Portfolio summary
          </h2>
          <div className="grid gap-4 md:grid-cols-4">
            <KpiCard
              label="Total companies"
              value={summary.totalCompanies.toString()}
              helper="In portfolio"
              tone="neutral"
            />
            <KpiCard
              label="Portfolio ARR"
              value={`USD ${summary.portfolioArr.toLocaleString(undefined, {
                minimumFractionDigits: 0,
                maximumFractionDigits: 0,
              })}`}
              helper="Latest annualized recurring revenue"
              tone="neutral"
            />
            <KpiCard
              label="Median growth"
              value={`${summary.medianGrowthPercent.toFixed(1)}%`}
              helper="Median MRR growth"
              tone={summary.medianGrowthPercent >= 10 ? "positive" : "neutral"}
            />
            <KpiCard
              label="Median NRR"
              value={`${summary.medianNrrPercent.toFixed(1)}%`}
              helper="Median net revenue retention"
              tone={summary.medianNrrPercent >= 120 ? "positive" : "neutral"}
            />
          </div>
        </section>

        {/* Category distribution */}
        <section className="space-y-3">
          <h2 className="text-sm font-medium text-slate-200">
            Company categories
          </h2>
          <div className="grid gap-4 md:grid-cols-4">
            <KpiCard
              label="Rocketships"
              value={summary.rocketships.toString()}
              helper="High growth & strong retention"
              tone={summary.rocketships > 0 ? "positive" : "neutral"}
            />
            <KpiCard
              label="Leaky buckets"
              value={summary.leakyBuckets.toString()}
              helper="Growth with weak retention"
              tone={summary.leakyBuckets > 0 ? "negative" : "neutral"}
            />
            <KpiCard
              label="Flat but solid"
              value={summary.flatButSolid.toString()}
              helper="Strong retention, modest growth"
              tone="neutral"
            />
            <KpiCard
              label="At risk"
              value={summary.atRisk.toString()}
              helper="Low growth and weak retention"
              tone={summary.atRisk > 0 ? "negative" : "neutral"}
            />
          </div>
        </section>

        {/* Scatter + table */}
        <section className="grid gap-4 lg:grid-cols-[1.3fr,1.7fr]">
          <div className="space-y-3">
            <h2 className="text-sm font-medium text-slate-200">
              Growth vs retention
            </h2>
            <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
              <PortfolioScatterChart companies={companies} />
            </div>
          </div>

          <div className="space-y-3">
            <h2 className="text-sm font-medium text-slate-200">
              Companies
            </h2>
            <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
              <PortfolioCompanyTable rows={companies} />
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}

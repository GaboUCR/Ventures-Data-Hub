// src/app/companies/[companyId]/cohorts/page.tsx
"use client";

import { useParams } from "next/navigation";
import type { OverviewFilters } from "@/types/metrics";
import { useCompanyCohorts } from "@/hooks/useCompanyCohorts";
import { CohortHeatmap } from "@/components/charts/CohortHeatmap";
import { KpiCard } from "@/components/kpis/KpiCard";
import { CompanyTabs } from "@/components/companies/CompanyTabs"; // if you extracted it
import Link from "next/link";

export default function CompanyCohortsPage() {
  const params = useParams<{ companyId: string }>();
  const companyId = params.companyId ?? "comp_1";

  const filters: OverviewFilters = {
    timeRange: "last_12_months",
    currency: "USD",
  };

  const { data, isLoading, error } = useCompanyCohorts(companyId, filters);

  if (isLoading) return <div className="p-6">Loading cohorts…</div>;
  if (error || !data)
    return <div className="p-6 text-red-400">Failed to load cohorts.</div>;

  return (
    <div className="px-4 py-6 sm:px-6 lg:px-8">
      <div className="mx-auto flex max-w-6xl flex-col gap-6">
        {/* You can reuse your company header; here’s a minimal breadcrumb/header example */}
        <header className="space-y-3 rounded-3xl border border-slate-800 bg-gradient-to-r from-emerald-500/10 via-sky-500/10 to-transparent p-5 shadow-sm">
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <Link href="/portfolio" className="hover:text-slate-200">
              Portfolio
            </Link>
            <span>›</span>
            <span className="text-slate-300">Company</span>
          </div>

          <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
            <div>
              <h1 className="text-2xl font-semibold text-slate-50">
                Cohorts & retention
              </h1>
              <p className="mt-1 text-sm text-slate-300">
                Signup cohorts · last 12 months
              </p>
            </div>
          </div>

          <CompanyTabs companyId={companyId} active="cohorts" />
        </header>

        {/* KPIs */}
        <section className="space-y-3">
          <h2 className="text-sm font-medium text-slate-200">
            Retention summary
          </h2>
          <div className="grid gap-4 md:grid-cols-3">
            <KpiCard
              label="6-month retention"
              value={`${data.retention6mPercent.toFixed(1)}%`}
              helper="Average MRR retained at month 6"
              tone={data.retention6mPercent >= 70 ? "positive" : "neutral"}
            />
            <KpiCard
              label="12-month retention"
              value={`${data.retention12mPercent.toFixed(1)}%`}
              helper="Average MRR retained at month 12"
              tone={data.retention12mPercent >= 60 ? "positive" : "neutral"}
            />
            <KpiCard
              label="Median time to churn"
              value={`${data.medianTimeToChurnMonths.toFixed(1)} mo`}
              helper="When MRR typically drops below 50%"
              tone={data.medianTimeToChurnMonths >= 8 ? "positive" : "neutral"}
            />
          </div>
        </section>

        {/* Heatmap + pre-churn insights */}
        <section className="grid gap-4 lg:grid-cols-[2fr,1fr]">
          <div className="space-y-3">
            <h2 className="text-sm font-medium text-slate-200">
              Cohort heatmap
            </h2>
            <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
              <CohortHeatmap data={data.heatmap} />
            </div>
          </div>

          <div className="space-y-3">
            <h2 className="text-sm font-medium text-slate-200">
              Pre-churn behavior
            </h2>
            <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 text-sm text-slate-300">
              {data.preChurnInsights.length === 0 ? (
                <p className="text-slate-400">
                  No pre-churn insights available yet.
                </p>
              ) : (
                <ul className="space-y-2">
                  {data.preChurnInsights.map((insight, idx) => (
                    <li key={idx}>• {insight}</li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}

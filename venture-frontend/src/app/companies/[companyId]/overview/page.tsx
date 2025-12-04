// src/app/companies/[companyId]/overview/page.tsx
"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCompanyOverview } from "@/hooks/useCompanyOverview";
import { useOverviewSnapshots } from "@/hooks/useOverviewSnapshots";
import { KpiCard } from "@/components/kpis/KpiCard";
import { MrrAreaChart } from "@/components/charts/MrrAreaChart";
import { OverviewFilters } from "@/types/metrics";

const timeRangeLabels: Record<OverviewFilters["timeRange"], string> = {
  last_30_days: "Last 30 days",
  last_90_days: "Last 90 days",
  last_12_months: "Last 12 months",
};

export default function CompanyOverviewPage() {
  const params = useParams<{ companyId: string }>();
  const companyId = params.companyId ?? "comp_1";

  const filters: OverviewFilters = {
    timeRange: "last_90_days",
    currency: "USD",
  };

  const {
    data,
    isLoading: isOverviewLoading,
    error: overviewError,
  } = useCompanyOverview(companyId, filters);

  const {
    data: snapshots,
    isLoading: isSnapshotsLoading,
    error: snapshotsError,
  } = useOverviewSnapshots(companyId, filters);

  if (isOverviewLoading || isSnapshotsLoading) {
    return <div className="p-6">Loading overview…</div>;
  }

  if (overviewError || !data || snapshotsError || !snapshots) {
    return <div className="p-6 text-red-400">Failed to load overview.</div>;
  }

  const timeRangeLabel = timeRangeLabels[filters.timeRange];

  return (
    <div className="px-4 py-6 sm:px-6 lg:px-8">
      <div className="mx-auto flex max-w-6xl flex-col gap-6">
        {/* ── Header: company name, breadcrumbs, tabs ────────────────────────────── */}
        <header className="space-y-3 rounded-3xl border border-slate-800 bg-gradient-to-r from-emerald-500/10 via-sky-500/10 to-transparent p-5 shadow-sm">
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <Link href="/portfolio" className="hover:text-slate-200">
              Portfolio
            </Link>
            <span>›</span>
            <span className="text-slate-300">{data.companyName}</span>
          </div>

          <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
            <div>
              <h1 className="text-2xl font-semibold text-slate-50">
                {data.companyName}
              </h1>
              <p className="mt-1 text-sm text-slate-300">
                Company overview · {timeRangeLabel}
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-2 text-xs">
              <span className="inline-flex items-center rounded-full border border-emerald-500/40 bg-emerald-500/10 px-3 py-1 font-medium text-emerald-300">
                ● Test data
              </span>
              <span className="rounded-full border border-slate-700 bg-slate-900/70 px-3 py-1 text-slate-300">
                Last updated: 5 min ago
              </span>
            </div>
          </div>

          {/* Tabs row */}
          <div className="mt-4 flex flex-wrap gap-2 text-sm">
            <TabChip href={`/companies/${companyId}/overview`} active>
              Overview
            </TabChip>
            <TabChip href={`/companies/${companyId}/revenue`}>Revenue</TabChip>
            <TabChip href={`/companies/${companyId}/cohorts`}>Cohorts</TabChip>
            <TabChip href={`/companies/${companyId}/acquisition`}>Acquisition</TabChip>
            <TabChip href={`/companies/${companyId}/integrations`}>Integrations</TabChip>
          </div>
        </header>

        {/* Filters row */}
        <section className="flex flex-wrap items-center justify-between gap-3">
          <div className="text-sm text-slate-400">
            Showing metrics in{" "}
            <span className="font-medium text-slate-200">{data.currency}</span>
          </div>
          <div className="flex items-center gap-2 text-xs">
            <button className="rounded-full border border-slate-700 bg-slate-900 px-3 py-1 text-slate-200">
              {timeRangeLabel}
            </button>
            {/* Later: dropdown for changing time range / segments */}
          </div>
        </section>

        {/* KPI row */}
        <section className="space-y-3">
          <h2 className="text-sm font-medium text-slate-200">Key metrics</h2>
          <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-5">
            <KpiCard
              label="MRR"
              value={`${data.currency} ${data.mrr.toLocaleString()}`}
              helper={`${data.mrrChangePercent > 0 ? "▲" : "▼"} ${data.mrrChangePercent.toFixed(
                1
              )}% vs previous period`}
              tone={data.mrrChangePercent >= 0 ? "positive" : "negative"}
            />
            <KpiCard
              label="ARR"
              value={`${data.currency} ${data.arr.toLocaleString()}`}
              helper={`${data.arrChangePercent.toFixed(1)}% vs previous period`}
              tone={data.arrChangePercent >= 0 ? "positive" : "negative"}
            />
            <KpiCard
              label="Net revenue retention"
              value={`${data.nrrPercent.toFixed(1)}%`}
              helper={data.nrrPercent >= 120 ? "Top quartile retention" : "Below ideal 120%+"}
              tone={data.nrrPercent >= 120 ? "positive" : "neutral"}
            />
            <KpiCard
              label="Active customers"
              value={data.activeCustomers.toLocaleString()}
              helper="Current billing customers"
              tone="neutral"
            />
            <KpiCard
              label="Churn rate"
              value={`${data.churnRatePercent.toFixed(1)}%`}
              helper={data.churnRatePercent <= 5 ? "Within healthy range" : "Watch closely"}
              tone={data.churnRatePercent <= 5 ? "positive" : "negative"}
            />
          </div>
        </section>

        {/* MRR chart + highlights */}
        <section className="grid gap-4 lg:grid-cols-[2fr,1fr]">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-medium text-slate-200">MRR dynamics</h2>
              <div className="flex gap-1 text-xs">
                <button className="rounded-full border border-slate-700 bg-slate-900 px-3 py-1 text-slate-200">
                  Stack by movement
                </button>
              </div>
            </div>
            <MrrAreaChart data={data.mrrSeries} />
          </div>

          <div className="space-y-3">
            <h2 className="text-sm font-medium text-slate-200">Highlights</h2>
            <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 text-sm text-slate-300">
              <ul className="space-y-2">
                <li>• MRR grew {data.mrrChangePercent.toFixed(1)}% over the selected period.</li>
                <li>
                  • NRR at {data.nrrPercent.toFixed(1)}% indicates{" "}
                  {data.nrrPercent >= 120
                    ? "strong expansion and retention."
                    : "room to improve expansion/churn."}
                </li>
                <li>
                  • Current churn rate of {data.churnRatePercent.toFixed(1)}% is{" "}
                  {data.churnRatePercent <= 5
                    ? "within a healthy range for SaaS."
                    : "above typical SaaS benchmarks."}
                </li>
              </ul>
            </div>
          </div>
        </section>

        {/* NEW: GA4 + Stripe snapshots */}
        <section className="space-y-6">
          {/* Traffic & signup snapshot (GA4) */}
          <div className="space-y-3">
            <h2 className="text-sm font-medium text-slate-200">Traffic & signup snapshot</h2>
            <div className="grid gap-4 md:grid-cols-3">
              <KpiCard
                label="Sessions"
                value={snapshots.traffic.sessions.toLocaleString()}
                helper="GA4 sessions for the selected period"
                tone="neutral"
              />
              <KpiCard
                label="Signups"
                value={snapshots.traffic.signups.toLocaleString()}
                helper="Users who completed signup"
                tone="neutral"
              />
              <KpiCard
                label="Signup conversion"
                value={`${snapshots.traffic.signupConversionRate.toFixed(1)}%`}
                helper="Signups / sessions"
                tone={
                  snapshots.traffic.signupConversionRate >= 5
                    ? "positive"
                    : snapshots.traffic.signupConversionRate >= 3
                    ? "neutral"
                    : "negative"
                }
              />
            </div>
          </div>

          {/* Billing health snapshot (Stripe) */}
          <div className="space-y-3">
            <h2 className="text-sm font-medium text-slate-200">Billing health snapshot</h2>
            <div className="grid gap-4 md:grid-cols-3">
              <KpiCard
                label="Payment success rate"
                value={`${snapshots.billing.paymentSuccessRate.toFixed(1)}%`}
                helper="Share of successful payment attempts"
                tone={snapshots.billing.paymentSuccessRate >= 95 ? "positive" : "negative"}
              />
              <KpiCard
                label="MRR at risk"
                value={`${data.currency} ${snapshots.billing.atRiskMrr.toLocaleString()}`}
                helper="Past-due subscription invoices"
                tone={snapshots.billing.atRiskMrr === 0 ? "positive" : "negative"}
              />
              <KpiCard
                label="Refund rate"
                value={`${snapshots.billing.refundRate.toFixed(1)}%`}
                helper="Refunds / total revenue"
                tone={snapshots.billing.refundRate <= 5 ? "neutral" : "negative"}
              />
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}

// Simple tab pill component
function TabChip({
  href,
  children,
  active = false,
}: {
  href: string;
  children: React.ReactNode;
  active?: boolean;
}) {
  return (
    <Link
      href={href}
      className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-medium transition-colors ${
        active
          ? "bg-slate-900/80 text-slate-100 shadow-sm border border-slate-700"
          : "text-slate-300 hover:bg-slate-900/60 border border-transparent"
      }`}
    >
      {children}
    </Link>
  );
}

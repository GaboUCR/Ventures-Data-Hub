// src/app/companies/[companyId]/revenue/page.tsx
"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCompanyRevenue } from "@/hooks/useCompanyRevenue";
import { KpiCard } from "@/components/kpis/KpiCard";
import { MrrAreaChart } from "@/components/charts/MrrAreaChart";
import { PlanBreakdownTable } from "@/components/table/PlanBreakdownTable";
import { OverviewFilters } from "@/types/metrics";

const timeRangeLabels: Record<OverviewFilters["timeRange"], string> = {
  last_30_days: "Last 30 days",
  last_90_days: "Last 90 days",
  last_12_months: "Last 12 months",
};

export default function CompanyRevenuePage() {
  const params = useParams<{ companyId: string }>();
  const companyId = params.companyId ?? "comp_1";

  const filters: OverviewFilters = {
    timeRange: "last_90_days",
    currency: "USD",
  };

  const { data, isLoading, error } = useCompanyRevenue(companyId, filters);

  if (isLoading) {
    return <div className="p-6">Loading revenue…</div>;
  }

  if (error || !data) {
    return <div className="p-6 text-red-400">Failed to load revenue.</div>;
  }

  const timeRangeLabel = timeRangeLabels[filters.timeRange];

  return (
    <div className="px-4 py-6 sm:px-6 lg:px-8">
      <div className="mx-auto flex max-w-6xl flex-col gap-6">
        {/* Header: company + breadcrumb + tabs */}
        <header className="space-y-3 rounded-3xl border border-slate-800 bg-gradient-to-r from-emerald-500/10 via-sky-500/10 to-transparent p-5 shadow-sm">
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <Link href="/portfolio" className="hover:text-slate-200">
              Portfolio
            </Link>
            <span>›</span>
            <span className="text-slate-300">{/* company name could come from separate hook later */}Company</span>
          </div>

          <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
            <div>
              <h1 className="text-2xl font-semibold text-slate-50">Revenue & subscriptions</h1>
              <p className="mt-1 text-sm text-slate-300">
                Stripe subscriptions & MRR · {timeRangeLabel}
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

          {/* Tabs row (same as overview, with Revenue active) */}
          <div className="mt-4 flex flex-wrap gap-2 text-sm">
            <TabChip href={`/companies/${companyId}/overview`}>Overview</TabChip>
            <TabChip href={`/companies/${companyId}/revenue`} active>
              Revenue
            </TabChip>
            <TabChip href={`/companies/${companyId}/cohorts`}>Cohorts</TabChip>
            <TabChip href={`/companies/${companyId}/acquisition`}>Acquisition</TabChip>
            <TabChip href={`/companies/${companyId}/integrations`}>Integrations</TabChip>
          </div>
        </header>

        {/* Filters row */}
        <section className="flex flex-wrap items-center justify-between gap-3">
          <div className="text-sm text-slate-400">
            Showing revenue in{" "}
            <span className="font-medium text-slate-200">{data.currency}</span>
          </div>
          <div className="flex items-center gap-2 text-xs">
            <button className="rounded-full border border-slate-700 bg-slate-900 px-3 py-1 text-slate-200">
              {timeRangeLabel}
            </button>
          </div>
        </section>

        {/* Headline KPIs */}
        <section className="space-y-3">
          <h2 className="text-sm font-medium text-slate-200">MRR breakdown</h2>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <KpiCard
              label="Current MRR"
              value={`${data.currency} ${data.currentMrr.toLocaleString()}`}
              helper="End of current period"
              tone="neutral"
            />
            <KpiCard
              label="New MRR"
              value={`${data.currency} ${data.newMrr.toLocaleString()}`}
              helper="From brand new customers"
              tone={data.newMrr > 0 ? "positive" : "neutral"}
            />
            <KpiCard
              label="Expansion MRR"
              value={`${data.currency} ${data.expansionMrr.toLocaleString()}`}
              helper="Upgrades & add-ons"
              tone={data.expansionMrr > 0 ? "positive" : "neutral"}
            />
            <KpiCard
              label="Churned MRR"
              value={`${data.currency} ${data.churnedMrr.toLocaleString()}`}
              helper="Lost from cancellations/downgrades"
              tone={data.churnedMrr > 0 ? "negative" : "neutral"}
            />
          </div>
        </section>

        {/* MRR chart + plan breakdown */}
        <section className="grid gap-4 lg:grid-cols-[2fr,1.5fr]">
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
            <h2 className="text-sm font-medium text-slate-200">Plan performance</h2>
            <PlanBreakdownTable rows={data.planBreakdown} currency={data.currency} />
          </div>
        </section>
      </div>
    </div>
  );
}

// Local TabChip (you can extract to a shared component later)
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

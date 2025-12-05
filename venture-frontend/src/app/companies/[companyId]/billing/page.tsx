// src/app/companies/[companyId]/billing/page.tsx
"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { KpiCard } from "@/components/kpis/KpiCard";
import { PaymentHealthChart } from "@/components/charts/PaymentHealthChart";
import { PastDueInvoicesTable } from "@/components/table/PastDueInvoicesTable";
import { useCompanyBillingHealth } from "@/hooks/useCompanyBillingHealth";
import { OverviewFilters } from "@/types/metrics";

const timeRangeLabels: Record<OverviewFilters["timeRange"], string> = {
  last_30_days: "Last 30 days",
  last_90_days: "Last 90 days",
  last_12_months: "Last 12 months",
};

export default function CompanyBillingPage() {
  const params = useParams<{ companyId: string }>();
  const companyId = params.companyId ?? "comp_1";

  const filters: OverviewFilters = {
    timeRange: "last_30_days",
    currency: "USD",
  };

  const { data, isLoading, error } = useCompanyBillingHealth(companyId, filters);

  if (isLoading) return <div className="p-6">Loading billing health…</div>;
  if (error || !data) return <div className="p-6 text-red-400">Failed to load billing health.</div>;

  const timeRangeLabel = timeRangeLabels[filters.timeRange];

  return (
    <div className="px-4 py-6 sm:px-6 lg:px-8">
      <div className="mx-auto flex max-w-6xl flex-col gap-6">
        {/* Header */}
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
                Billing & payment health
              </h1>
              <p className="mt-1 text-sm text-slate-300">
                Stripe charges, failures & dunning · {timeRangeLabel}
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

          {/* Tabs */}
          <div className="mt-4 flex flex-wrap gap-2 text-sm">
            <TabChip href={`/companies/${companyId}/overview`}>Overview</TabChip>
            <TabChip href={`/companies/${companyId}/revenue`}>Revenue</TabChip>
            <TabChip href={`/companies/${companyId}/cohorts`}>Cohorts</TabChip>
            <TabChip href={`/companies/${companyId}/acquisition`}>Acquisition</TabChip>
            <TabChip href={`/companies/${companyId}/billing`} active>
              Billing
            </TabChip>
            <TabChip href={`/companies/${companyId}/integrations`}>Integrations</TabChip>
          </div>
        </header>

        {/* Filters row */}
        <section className="flex flex-wrap items-center justify-between gap-3">
          <div className="text-sm text-slate-400">
            Based on{" "}
            <span className="font-medium text-slate-200">Stripe invoices & charges</span>
          </div>
          <div className="flex items-center gap-2 text-xs">
            <button className="rounded-full border border-slate-700 bg-slate-900 px-3 py-1 text-slate-200">
              {timeRangeLabel}
            </button>
          </div>
        </section>

        {/* KPIs */}
        <section className="space-y-3">
          <h2 className="text-sm font-medium text-slate-200">Billing health snapshot</h2>
          <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-4">
            <KpiCard
              label="Payment success rate"
              value={`${data.successRate.toFixed(1)}%`}
              helper="Share of successful payment attempts"
              tone={data.successRate >= 95 ? "positive" : "negative"}
            />
            <KpiCard
              label="Failed payments"
              value={data.failedPayments.toString()}
              helper="In the selected period"
              tone={data.failedPayments === 0 ? "positive" : "negative"}
            />
            <KpiCard
              label="MRR at risk"
              value={`${data.currency} ${data.atRiskMrr.toLocaleString()}`}
              helper="Past-due invoices linked to subscriptions"
              tone={data.atRiskMrr === 0 ? "positive" : "negative"}
            />
            <KpiCard
              label="Refund rate"
              value={`${data.refundRate.toFixed(1)}%`}
              helper="Refunded / total revenue"
              tone={data.refundRate <= 5 ? "neutral" : "negative"}
            />
          </div>
        </section>

        {/* Chart + table */}
        <section className="grid gap-4 lg:grid-cols-[2fr,1.3fr]">
          <div className="space-y-3">
            <PaymentHealthChart data={data.series} />
          </div>

          <div className="space-y-3">
            <h2 className="text-sm font-medium text-slate-200">Past-due invoices</h2>
            <PastDueInvoicesTable rows={data.pastDueInvoices} currency={data.currency} />
          </div>
        </section>
      </div>
    </div>
  );
}

// Local TabChip
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

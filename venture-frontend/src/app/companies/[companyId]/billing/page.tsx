"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import type { OverviewFilters } from "@/types/metrics";
import { useCompanyBillingHealth } from "@/hooks/useCompanyBillingHealth";
import { KpiCard } from "@/components/kpis/KpiCard";
import { PaymentHealthChart } from "@/components/charts/PaymentHealthChart";
import { PastDueInvoicesTable } from "@/components/table/PastDueInvoicesTable";
import { CompanyTabs } from "@/components/companies/CompanyTabs";

export default function CompanyBillingPage() {
  const params = useParams<{ companyId: string }>();
  const companyId = params.companyId ?? "comp_1";

  const filters: OverviewFilters = {
    timeRange: "last_30_days",
    currency: "USD",
  };

  const { data, isLoading, error } = useCompanyBillingHealth(companyId, filters);

  if (isLoading) return <div className="p-6">Loading billing…</div>;
  if (error || !data)
    return <div className="p-6 text-red-400">Failed to load billing.</div>;

  return (
    <div className="px-4 py-6 sm:px-6 lg:px-8">
      <div className="mx-auto flex max-w-6xl flex-col gap-6">
        {/* Header */}
        <header className="space-y-3 rounded-3xl border border-slate-800 bg-gradient-to-r from-rose-500/10 via-amber-500/10 to-transparent p-5 shadow-sm">
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <Link href="/portfolio" className="hover:text-slate-200">
              Portfolio
            </Link>
            <span>›</span>
            <span className="text-slate-300">Billing</span>
          </div>

          <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
            <div>
              <h1 className="text-2xl font-semibold text-slate-50">
                Billing health
              </h1>
              <p className="mt-1 text-sm text-slate-300">
                Payment reliability · last 30 days
              </p>
            </div>
          </div>

          <CompanyTabs companyId={companyId} active="billing" />
        </header>

        {/* KPIs */}
        <section className="space-y-3">
          <h2 className="text-sm font-medium text-slate-200">Billing summary</h2>
          <div className="grid gap-4 md:grid-cols-3">
            <KpiCard
              label="Payment success rate"
              value={`${data.paymentSuccessRate.toFixed(1)}%`}
              helper="Successful payment attempts"
              tone={data.paymentSuccessRate >= 95 ? "positive" : "negative"}
            />
            <KpiCard
              label="Failed payments"
              value={data.failedPayments.toLocaleString()}
              helper="Failed attempts in period"
              tone={data.failedPayments === 0 ? "positive" : "negative"}
            />
            <KpiCard
              label="MRR at risk"
              value={`USD ${data.mrrAtRisk.toLocaleString(undefined, {
                minimumFractionDigits: 0,
                maximumFractionDigits: 0,
              })}`}
              helper="Past-due subscription invoices"
              tone={data.mrrAtRisk === 0 ? "positive" : "negative"}
            />
          </div>
        </section>

        {/* Chart + table */}
        <section className="grid gap-4 lg:grid-cols-[2fr,1.4fr]">
          <div className="space-y-3">
            <h2 className="text-sm font-medium text-slate-200">
              Payment health over time
            </h2>
            <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
              <PaymentHealthChart data={data.healthSeries} />
            </div>
          </div>

          <div className="space-y-3">
            <h2 className="text-sm font-medium text-slate-200">
              Past-due invoices
            </h2>
            <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
              <PastDueInvoicesTable rows={data.pastDueInvoices} />
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}

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

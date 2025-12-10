// src/app/companies/[companyId]/acquisition/page.tsx
"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import type { OverviewFilters } from "@/types/metrics";
import { useCompanyAcquisition } from "@/hooks/useCompanyAcquisition";
import { KpiCard } from "@/components/kpis/KpiCard";
import { FunnelSteps } from "@/components/charts/FunnelSteps";
import { ChannelPerformanceTable } from "@/components/table/ChannelPerformanceTable";
import { CompanyTabs } from "@/components/companies/CompanyTabs";

export default function CompanyAcquisitionPage() {
  const params = useParams<{ companyId: string }>();
  const companyId = params.companyId ?? "comp_1";

  const filters: OverviewFilters = {
    timeRange: "last_90_days",
    currency: "USD",
  };

  const { data, isLoading, error } = useCompanyAcquisition(companyId, filters);

  if (isLoading) return <div className="p-6">Loading acquisition…</div>;
  if (error || !data)
    return <div className="p-6 text-red-400">Failed to load acquisition.</div>;

  return (
    <div className="px-4 py-6 sm:px-6 lg:px-8">
      <div className="mx-auto flex max-w-6xl flex-col gap-6">
        {/* Header (you can unify this with Overview/Revnue header) */}
        <header className="space-y-3 rounded-3xl border border-slate-800 bg-gradient-to-r from-sky-500/10 via-emerald-500/10 to-transparent p-5 shadow-sm">
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <Link href="/portfolio" className="hover:text-slate-200">
              Portfolio
            </Link>
            <span>›</span>
            <span className="text-slate-300">Company acquisition</span>
          </div>

          <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
            <div>
              <h1 className="text-2xl font-semibold text-slate-50">
                Acquisition
              </h1>
              <p className="mt-1 text-sm text-slate-300">
                Channels & funnels · last 90 days
              </p>
            </div>
          </div>

          <CompanyTabs companyId={companyId} active="acquisition" />
        </header>

        {/* KPIs */}
        <section className="space-y-3">
          <h2 className="text-sm font-medium text-slate-200">
            Acquisition summary
          </h2>
          <div className="grid gap-4 md:grid-cols-4">
            <KpiCard
              label="Sessions"
              value={data.sessions.toLocaleString()}
              helper="GA4 sessions in period"
              tone="neutral"
            />
            <KpiCard
              label="Signups"
              value={data.signups.toLocaleString()}
              helper="Completed signups"
              tone="neutral"
            />
            <KpiCard
              label="New paying customers"
              value={data.newPayingCustomers.toLocaleString()}
              helper="First-time payers"
              tone="neutral"
            />
            <KpiCard
              label="Visit → signup"
              value={`${data.visitToSignupRate.toFixed(1)}%`}
              helper="Signups / sessions"
              tone={
                data.visitToSignupRate >= 5
                  ? "positive"
                  : data.visitToSignupRate >= 3
                  ? "neutral"
                  : "negative"
              }
            />
          </div>
        </section>

        {/* Funnel + channels */}
        <section className="grid gap-4 lg:grid-cols-[1.2fr,1.8fr]">
          <div className="space-y-3">
            <h2 className="text-sm font-medium text-slate-200">
              Funnel performance
            </h2>
            <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
              <FunnelSteps steps={data.steps} />
            </div>
          </div>

          <div className="space-y-3">
            <h2 className="text-sm font-medium text-slate-200">
              Channel performance
            </h2>
            <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
              <ChannelPerformanceTable rows={data.channels} currency={filters.currency} />
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

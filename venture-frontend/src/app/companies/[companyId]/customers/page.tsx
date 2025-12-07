// src/app/companies/[companyId]/customers/page.tsx
"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

import { KpiCard } from "@/components/kpis/KpiCard";
import { CompanyTabs } from "@/components/companies/CompanyTabs";
import { CustomerListTable } from "@/components/table/CustomerListTable";
import { CustomerDetailDrawer } from "@/components/customers/CustomerDetailDrawer";

import { useCompanyCustomers } from "@/hooks/useCompanyCustomers";
import { CustomerDetail, OverviewFilters } from "@/types/metrics";

const timeRangeLabels: Record<OverviewFilters["timeRange"], string> = {
  last_30_days: "Last 30 days",
  last_90_days: "Last 90 days",
  last_12_months: "Last 12 months",
};

export default function CompanyCustomersPage() {
  const params = useParams<{ companyId: string }>();
  const companyId = params.companyId ?? "comp_1";

  const filters: OverviewFilters = {
    timeRange: "last_90_days",
    currency: "USD",
  };

  const { data, isLoading, error } = useCompanyCustomers(companyId, filters);
  const [selectedCustomerId, setSelectedCustomerId] = useState<string | null>(null);

  if (isLoading) {
    return <div className="p-6">Loading customers…</div>;
  }

  if (error || !data) {
    return <div className="p-6 text-red-400">Failed to load customers.</div>;
  }

  const timeRangeLabel = timeRangeLabels[filters.timeRange];

  const selectedRow = data.rows.find((r) => r.id === selectedCustomerId) || null;

  // For mock purposes, enrich row → detail
  const selectedCustomer: CustomerDetail | null = selectedRow
    ? {
        ...selectedRow,
        planName:
          selectedRow.currentMrr >= 2000
            ? "Enterprise"
            : selectedRow.currentMrr >= 500
            ? "Growth"
            : selectedRow.currentMrr > 0
            ? "Starter"
            : "Former customer",
        segments:
          selectedRow.email.includes("inc") || selectedRow.email.includes("corp")
            ? ["Mid-market", "US", "Self-serve"]
            : ["SMB", "Global", "Self-serve"],
        recentPages:
          selectedRow.status === "churned"
            ? ["/pricing", "/account/cancel", "/support"]
            : ["/dashboard", "/usage", "/billing"],
        notes:
          selectedRow.status === "at_risk"
            ? "Spike in payment failures and reduced product usage over the last 30 days."
            : undefined,
      }
    : null;

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
                Customers & account 360°
              </h1>
              <p className="mt-1 text-sm text-slate-300">
                Stripe customers, subscriptions & GA4 activity · {timeRangeLabel}
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

          <CompanyTabs companyId={companyId} active="customers" />
        </header>

        {/* Filters row */}
        <section className="flex flex-wrap items-center justify-between gap-3">
          <div className="text-sm text-slate-400">
            Joined from{" "}
            <span className="font-medium text-slate-200">Stripe & GA4</span>
          </div>
          <div className="flex items-center gap-2 text-xs">
            <button className="rounded-full border border-slate-700 bg-slate-900 px-3 py-1 text-slate-200">
              {timeRangeLabel}
            </button>
          </div>
        </section>

        {/* Summary KPIs */}
        <section className="space-y-3">
          <h2 className="text-sm font-medium text-slate-200">Customer snapshot</h2>
          <div className="grid gap-4 md:grid-cols-3">
            <KpiCard
              label="Total customers"
              value={data.totalCustomers.toLocaleString()}
              helper="All paying & historical Stripe customers"
              tone="neutral"
            />
            <KpiCard
              label="New customers"
              value={data.newCustomersThisPeriod.toLocaleString()}
              helper="New in the selected period"
              tone={data.newCustomersThisPeriod > 0 ? "positive" : "neutral"}
            />
            <KpiCard
              label="High-value customers"
              value={data.highValueCustomers.toLocaleString()}
              helper="LTV above your threshold"
              tone={data.highValueCustomers > 0 ? "positive" : "neutral"}
            />
          </div>
        </section>

        {/* Table + detail drawer */}
        <section className="grid gap-4 lg:grid-cols-[2fr,1.4fr]">
          <div className="space-y-3">
            <h2 className="text-sm font-medium text-slate-200">Customer list</h2>
            <CustomerListTable
              rows={data.rows}
              currency={data.currency}
              onRowClick={setSelectedCustomerId}
            />
          </div>

          <div className="space-y-3">
            <h2 className="text-sm font-medium text-slate-200">Customer detail</h2>
            <CustomerDetailDrawer customer={selectedCustomer} currency={data.currency} />
          </div>
        </section>
      </div>
    </div>
  );
}

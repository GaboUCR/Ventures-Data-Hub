// src/app/companies/[companyId]/customers/page.tsx
"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import type { OverviewFilters } from "@/types/metrics";
import { useCompanyCustomers, useCustomerDetail } from "@/hooks/useCompanyCustomers";
import { KpiCard } from "@/components/kpis/KpiCard";
import { CustomerListTable } from "@/components/table/CustomerListTable";
import { CustomerDetailDrawer } from "@/components/customers/CustomerDetailDrawer";
import { CompanyTabs } from "@/components/companies/CompanyTabs"; // if you extracted it

export default function CompanyCustomersPage() {
  const params = useParams<{ companyId: string }>();
  const companyId = params.companyId ?? "comp_1";

  const filters: OverviewFilters = {
    timeRange: "last_90_days",
    currency: "USD",
  };

  const { data, isLoading, error } = useCompanyCustomers(companyId, filters);
  const [selectedCustomerId, setSelectedCustomerId] = useState<string | null>(null);

  const {
    data: selectedCustomer,
    isLoading: isDetailLoading,
  } = useCustomerDetail(companyId, selectedCustomerId);

  if (isLoading) return <div className="p-6">Loading customers…</div>;
  if (error || !data)
    return <div className="p-6 text-red-400">Failed to load customers.</div>;

  const { summary, customers } = data;

  return (
    <>
      <div className="px-4 py-6 sm:px-6 lg:px-8">
        <div className="mx-auto flex max-w-6xl flex-col gap-6">
          {/* Header */}
          <header className="space-y-3 rounded-3xl border border-slate-800 bg-gradient-to-r from-purple-500/10 via-sky-500/10 to-transparent p-5 shadow-sm">
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <Link href="/portfolio" className="hover:text-slate-200">
                Portfolio
              </Link>
              <span>›</span>
              <span className="text-slate-300">Customers</span>
            </div>

            <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
              <div>
                <h1 className="text-2xl font-semibold text-slate-50">
                  Customers
                </h1>
                <p className="mt-1 text-sm text-slate-300">
                  Active & historical customers · last 90 days for new signups
                </p>
              </div>
            </div>

            <CompanyTabs companyId={companyId} active="customers" />
          </header>

          {/* Summary KPIs */}
          <section className="space-y-3">
            <h2 className="text-sm font-medium text-slate-200">
              Customer summary
            </h2>
            <div className="grid gap-4 md:grid-cols-3">
              <KpiCard
                label="Total customers"
                value={summary.totalCustomers.toLocaleString()}
                helper="All-time customers"
                tone="neutral"
              />
              <KpiCard
                label="New this period"
                value={summary.newCustomers.toLocaleString()}
                helper="First seen in selected time range"
                tone={summary.newCustomers > 0 ? "positive" : "neutral"}
              />
              <KpiCard
                label="High-value customers"
                value={summary.highValueCustomers.toLocaleString()}
                helper="LTV above threshold"
                tone={summary.highValueCustomers > 0 ? "positive" : "neutral"}
              />
            </div>
          </section>

          {/* Customer list */}
          <section className="space-y-3">
            <h2 className="text-sm font-medium text-slate-200">
              Customers
            </h2>
            <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
              <CustomerListTable
                rows={customers}
                onRowClick={(id) => setSelectedCustomerId(id)}
              />
            </div>
          </section>
        </div>
      </div>

      <CustomerDetailDrawer
        customer={isDetailLoading ? null : selectedCustomer ?? null}
        onClose={() => setSelectedCustomerId(null)}
      />
    </>
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

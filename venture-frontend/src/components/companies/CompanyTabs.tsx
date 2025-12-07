// src/components/companies/CompanyTabs.tsx
"use client";

import Link from "next/link";

export type CompanyTabKey =
  | "overview"
  | "revenue"
  | "cohorts"
  | "acquisition"
  | "billing"
  | "customers";

interface CompanyTabsProps {
  companyId: string;
  active: CompanyTabKey;
  className?: string;
}

export function CompanyTabs({ companyId, active, className = "" }: CompanyTabsProps) {
  return (
    <div className={`mt-4 flex flex-wrap gap-2 text-sm ${className}`}>
      <TabChip
        href={`/companies/${companyId}/overview`}
        active={active === "overview"}
      >
        Overview
      </TabChip>
      <TabChip
        href={`/companies/${companyId}/revenue`}
        active={active === "revenue"}
      >
        Revenue
      </TabChip>
      <TabChip
        href={`/companies/${companyId}/cohorts`}
        active={active === "cohorts"}
      >
        Cohorts
      </TabChip>
      <TabChip
        href={`/companies/${companyId}/acquisition`}
        active={active === "acquisition"}
      >
        Acquisition
      </TabChip>
      <TabChip
        href={`/companies/${companyId}/billing`}
        active={active === "billing"}
      >
        Billing
      </TabChip>
      <TabChip
        href={`/companies/${companyId}/customers`}
        active={active === "customers"}
      >
        Customers
      </TabChip>
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

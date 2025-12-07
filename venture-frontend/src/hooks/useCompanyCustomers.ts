// src/hooks/useCompanyCustomers.ts
"use client";

import { useQuery } from "@tanstack/react-query";
import {
  CompanyCustomersMetrics,
  CustomerRow,
  OverviewFilters,
} from "@/types/metrics";

const fakeDelay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export function useCompanyCustomers(companyId: string, _filters: OverviewFilters) {
  return useQuery<CompanyCustomersMetrics>({
    queryKey: ["companyCustomers", companyId, _filters],
    queryFn: async () => {
      await fakeDelay(300);

      const rows: CustomerRow[] = [
        {
          id: "cus_001",
          email: "alice@example.com",
          name: "Alice Nguyen",
          currentMrr: 120,
          lifetimeRevenue: 960,
          firstSeenAt: "2024-01-15",
          lastActivityAt: "2025-02-01",
          status: "active",
        },
        {
          id: "cus_002",
          email: "billing@acme-inc.com",
          name: "Acme Inc.",
          currentMrr: 2200,
          lifetimeRevenue: 22000,
          firstSeenAt: "2023-09-10",
          lastActivityAt: "2025-01-30",
          status: "at_risk",
        },
        {
          id: "cus_003",
          email: "ops@workflowx.io",
          name: "WorkflowX",
          currentMrr: 750,
          lifetimeRevenue: 6000,
          firstSeenAt: "2024-05-02",
          lastActivityAt: "2025-01-20",
          status: "trialing",
        },
        {
          id: "cus_004",
          email: "churned@oldco.io",
          name: "OldCo",
          currentMrr: 0,
          lifetimeRevenue: 1800,
          firstSeenAt: "2023-01-05",
          lastActivityAt: "2024-03-14",
          status: "churned",
        },
      ];

      const metrics: CompanyCustomersMetrics = {
        companyId,
        companyName: "Acme SaaS", // mock
        currency: "USD",
        totalCustomers: rows.length,
        newCustomersThisPeriod: 8,
        highValueCustomers: 2,
        rows,
      };

      return metrics;
    },
  });
}

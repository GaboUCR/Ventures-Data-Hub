// src/hooks/useCompanyBillingHealth.ts
"use client";

import { useQuery } from "@tanstack/react-query";
import {
  CompanyBillingMetrics,
  OverviewFilters,
  PaymentHealthPoint,
  PastDueRow,
} from "@/types/metrics";

const fakeDelay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export function useCompanyBillingHealth(companyId: string, _filters: OverviewFilters) {
  return useQuery<CompanyBillingMetrics>({
    queryKey: ["billingHealth", companyId, _filters],
    queryFn: async () => {
      await fakeDelay(300);

      const series: PaymentHealthPoint[] = [
        { date: "2025-01-01", success: 190, failed: 6 },
        { date: "2025-01-08", success: 210, failed: 7 },
        { date: "2025-01-15", success: 205, failed: 4 },
        { date: "2025-01-22", success: 220, failed: 5 },
      ];

      const pastDueInvoices: PastDueRow[] = [
        { id: "inv_001", customer: "alice@example.com", amount: 300, daysLate: 7 },
        { id: "inv_002", customer: "billing@acme-inc.com", amount: 900, daysLate: 15 },
        { id: "inv_003", customer: "ops@workflowx.io", amount: 1100, daysLate: 30 },
      ];

      const metrics: CompanyBillingMetrics = {
        companyId,
        companyName: "Acme SaaS", // mock
        currency: "USD",
        successRate: 96.7,
        failedPayments: 22,
        atRiskMrr: 2300,
        refundRate: 2.1,
        series,
        pastDueInvoices,
      };

      return metrics;
    },
  });
}

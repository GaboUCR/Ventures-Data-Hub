// src/hooks/useCompanyRevenue.ts
"use client";

import { useQuery } from "@tanstack/react-query";
import { CompanyRevenueMetrics, OverviewFilters, MrrSeriesPoint, PlanRow } from "@/types/metrics";

const fakeDelay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export function useCompanyRevenue(companyId: string, _filters: OverviewFilters) {
  return useQuery<CompanyRevenueMetrics>({
    queryKey: ["companyRevenue", companyId, _filters],
    queryFn: async () => {
      await fakeDelay(300);

      // Mock MRR series (same structure as overview)
      const mrrSeries: MrrSeriesPoint[] = [
        { date: "2025-01-01", total: 10000, new: 3000, expansion: 1000, contraction: -500, churn: -500 },
        { date: "2025-02-01", total: 12000, new: 2500, expansion: 1500, contraction: -700, churn: -300 },
        { date: "2025-03-01", total: 15000, new: 3500, expansion: 2000, contraction: -800, churn: -700 },
        { date: "2025-04-01", total: 17000, new: 2800, expansion: 1800, contraction: -600, churn: -1000 },
      ];

      const planBreakdown: PlanRow[] = [
        {
          planId: "price_starter",
          planName: "Starter",
          mrr: 4000,
          subscribers: 120,
          churnRatePercent: 6.5,
          growthRatePercent: 12.3,
        },
        {
          planId: "price_growth",
          planName: "Growth",
          mrr: 9000,
          subscribers: 160,
          churnRatePercent: 3.2,
          growthRatePercent: 18.7,
        },
        {
          planId: "price_enterprise",
          planName: "Enterprise",
          mrr: 4000,
          subscribers: 60,
          churnRatePercent: 1.4,
          growthRatePercent: 22.1,
        },
      ];

      return {
        companyId,
        currency: "USD",
        currentMrr: 17000,
        newMrr: 2800,
        expansionMrr: 1800,
        churnedMrr: 1000,
        mrrSeries,
        planBreakdown,
      };
    },
  });
}

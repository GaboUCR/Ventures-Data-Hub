// src/hooks/useOverviewSnapshots.ts
"use client";

import { useQuery } from "@tanstack/react-query";
import { OverviewFilters, OverviewSnapshots } from "@/types/metrics";

const fakeDelay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export function useOverviewSnapshots(
  companyId: string,
  _filters: OverviewFilters
) {
  return useQuery<OverviewSnapshots>({
    queryKey: ["overviewSnapshots", companyId, _filters],
    queryFn: async () => {
      await fakeDelay(250);

      // MOCK DATA — later this will come from Stripe + GA4
      return {
        traffic: {
          sessions: 18234,
          signups: 742,
          signupConversionRate: (742 / 18234) * 100, // ~4.1%
        },
        billing: {
          paymentSuccessRate: 96.8,
          atRiskMrr: 2300, // assume same currency as overview
          refundRate: 2.3,
        },
      };
    },
  });
}

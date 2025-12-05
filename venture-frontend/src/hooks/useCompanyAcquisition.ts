// src/hooks/useCompanyAcquisition.ts
"use client";

import { useQuery } from "@tanstack/react-query";
import {
  CompanyAcquisitionMetrics,
  OverviewFilters,
  ChannelRow,
  FunnelStep,
} from "@/types/metrics";

const fakeDelay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export function useCompanyAcquisition(companyId: string, _filters: OverviewFilters) {
  return useQuery<CompanyAcquisitionMetrics>({
    queryKey: ["companyAcquisition", companyId, _filters],
    queryFn: async () => {
      await fakeDelay(300);

      const sessions = 18500;
      const signups = 780;
      const newPayingCustomers = 190;
      const visitToSignupRate = (signups / sessions) * 100;

      const steps: FunnelStep[] = [
        { label: "Visits", count: sessions },
        { label: "Signups", count: signups },
        { label: "Started checkout", count: 420 },
        { label: "Paid", count: newPayingCustomers },
      ];

      const channels: ChannelRow[] = [
        {
          channel: "Organic Search",
          sessions: 8000,
          signups: 360,
          newCustomers: 90,
          newMrr: 7000,
        },
        {
          channel: "Paid Search",
          sessions: 4500,
          signups: 210,
          newCustomers: 55,
          newMrr: 5200,
        },
        {
          channel: "Referral",
          sessions: 2600,
          signups: 130,
          newCustomers: 30,
          newMrr: 3100,
        },
        {
          channel: "Direct",
          sessions: 3400,
          signups: 80,
          newCustomers: 15,
          newMrr: 1600,
        },
      ];

      const metrics: CompanyAcquisitionMetrics = {
        companyId,
        companyName: "Acme SaaS", // mock for now
        currency: "USD",
        sessions,
        signups,
        newPayingCustomers,
        visitToSignupRate,
        steps,
        channels,
      };

      return metrics;
    },
  });
}

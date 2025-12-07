// src/hooks/usePortfolioOverview.ts
"use client";

import { useQuery } from "@tanstack/react-query";
import { PortfolioOverviewData, PortfolioCompany, PortfolioAlert } from "@/types/metrics";

const fakeDelay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export function usePortfolioOverview() {
  return useQuery<PortfolioOverviewData>({
    queryKey: ["portfolioOverview"],
    queryFn: async () => {
      await fakeDelay(300);

      const companies: PortfolioCompany[] = [
        {
          id: "comp_finpay",
          name: "FinPay",
          stage: "series_a",
          sector: "Fintech",
          owner: "Julia",
          arr: 1_800_000,
          mrr: 150_000,
          mrrGrowthRatePercent: 14.5,
          nrrPercent: 128,
          churnRatePercent: 4.2,
          paymentSuccessRate: 97.5,
          mrrAtRisk: 8_500,
          visitToSignupRate: 4.8,
          integrations: { stripe: "connected", ga4: "connected" },
        },
        {
          id: "comp_greenlogix",
          name: "GreenLogix",
          stage: "seed",
          sector: "Climate SaaS",
          owner: "Marcos",
          arr: 420_000,
          mrr: 35_000,
          mrrGrowthRatePercent: 27.3,
          nrrPercent: 135,
          churnRatePercent: 3.1,
          paymentSuccessRate: 96.2,
          mrrAtRisk: 3_200,
          visitToSignupRate: 5.3,
          integrations: { stripe: "connected", ga4: "connected" },
        },
        {
          id: "comp_nanocloud",
          name: "NanoCloud",
          stage: "series_b",
          sector: "DevTools",
          owner: "Julia",
          arr: 3_200_000,
          mrr: 270_000,
          mrrGrowthRatePercent: 9.2,
          nrrPercent: 118,
          churnRatePercent: 6.8,
          paymentSuccessRate: 93.5,
          mrrAtRisk: 22_000,
          visitToSignupRate: 3.1,
          integrations: { stripe: "connected", ga4: "missing" },
        },
        {
          id: "comp_stackflow",
          name: "StackFlow",
          stage: "seed",
          sector: "B2B SaaS",
          owner: "Ana",
          arr: 300_000,
          mrr: 25_000,
          mrrGrowthRatePercent: 35.4,
          nrrPercent: 142,
          churnRatePercent: 2.9,
          paymentSuccessRate: 98.1,
          mrrAtRisk: 1_100,
          visitToSignupRate: 6.2,
          integrations: { stripe: "connected", ga4: "connected" },
        },
        {
          id: "comp_mercuryhealth",
          name: "Mercury Health",
          stage: "series_a",
          sector: "Healthtech",
          owner: "Marcos",
          arr: 900_000,
          mrr: 75_000,
          mrrGrowthRatePercent: -3.5,
          nrrPercent: 96,
          churnRatePercent: 9.7,
          paymentSuccessRate: 91.3,
          mrrAtRisk: 18_600,
          visitToSignupRate: 2.4,
          integrations: { stripe: "connected", ga4: "connected" },
        },
        {
          id: "comp_insightly",
          name: "Insightly AI",
          stage: "pre_seed",
          sector: "AI tooling",
          owner: "Ana",
          arr: 120_000,
          mrr: 10_000,
          mrrGrowthRatePercent: 48.9,
          nrrPercent: 152,
          churnRatePercent: 4.9,
          paymentSuccessRate: 95.8,
          mrrAtRisk: 400,
          visitToSignupRate: 5.9,
          integrations: { stripe: "missing", ga4: "connected" },
        },
      ];

      const alerts: PortfolioAlert[] = [
        {
          id: "alert_1",
          companyId: "comp_mercuryhealth",
          companyName: "Mercury Health",
          severity: "critical",
          category: "billing",
          message: "Payment success rate dropped below 92% and MRR at risk exceeds $15k.",
          createdAt: "2025-02-01T10:15:00Z",
        },
        {
          id: "alert_2",
          companyId: "comp_nanocloud",
          companyName: "NanoCloud",
          severity: "warning",
          category: "retention",
          message: "NRR is below 120% and churn has trended up for two consecutive months.",
          createdAt: "2025-01-29T08:03:00Z",
        },
        {
          id: "alert_3",
          companyId: "comp_insightly",
          companyName: "Insightly AI",
          severity: "info",
          category: "integration",
          message: "Stripe not connected yet · only GA4 is sending data.",
          createdAt: "2025-01-27T17:40:00Z",
        },
      ];

      const data: PortfolioOverviewData = {
        companies,
        alerts,
      };

      return data;
    },
  });
}

// src/mocks/portfolioMetrics.ts
import { PortfolioMetrics } from "@/types/metrics";

export const MOCK_PORTFOLIO_METRICS: PortfolioMetrics = {
  totalArr: 5_000_000,
  avgNrrPercent: 122,
  companyCount: 12,
  companies: [
    {
      companyId: "comp_1",
      companyName: "Acme SaaS",
      arr: 2_000_000,
      growthRatePercent: 85,
      nrrPercent: 125,
      churnRatePercent: 3.5,
      healthScore: 92,
    },
    {
      companyId: "comp_2",
      companyName: "GreenTech Cloud",
      arr: 800_000,
      growthRatePercent: 60,
      nrrPercent: 118,
      churnRatePercent: 4.1,
      healthScore: 86,
    },
    {
      companyId: "comp_3",
      companyName: "WorkflowX",
      arr: 2_200_000,
      growthRatePercent: 45,
      nrrPercent: 110,
      churnRatePercent: 6.0,
      healthScore: 78,
    },
  ],
};

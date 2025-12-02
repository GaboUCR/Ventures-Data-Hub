// src/mocks/companyOverview.ts
import { CompanyOverviewMetrics, MrrSeriesPoint } from "@/types/metrics";

const mockMrrSeries: MrrSeriesPoint[] = [
  { date: "2025-01-01", total: 10000, new: 3000, expansion: 1000, contraction: -500, churn: -500 },
  { date: "2025-02-01", total: 12000, new: 2500, expansion: 1500, contraction: -700, churn: -300 },
  { date: "2025-03-01", total: 15000, new: 3500, expansion: 2000, contraction: -800, churn: -700 },
  { date: "2025-04-01", total: 17000, new: 2800, expansion: 1800, contraction: -600, churn: -1000 },
];

export const MOCK_COMPANY_OVERVIEW: CompanyOverviewMetrics = {
  companyId: "comp_1",
  companyName: "Acme SaaS",
  currency: "USD",
  mrr: 17000,
  arr: 17000 * 12,
  nrrPercent: 118,
  churnRatePercent: 4.2,
  activeCustomers: 340,
  mrrChangePercent: 13.3,
  arrChangePercent: 13.3,
  mrrSeries: mockMrrSeries,
};

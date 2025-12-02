// src/mocks/companyRevenue.ts
import {
  CompanyRevenueMetrics,
  MrrSeriesPoint,
  RevenueSeriesPoint,
  PlanBreakdownRow,
} from "../types/metrics";

const mockMrrSeries: MrrSeriesPoint[] = [
  { date: "2025-01-01", total: 10000, new: 3000, expansion: 1000, contraction: -500, churn: -500 },
  { date: "2025-02-01", total: 12000, new: 2500, expansion: 1500, contraction: -700, churn: -300 },
  { date: "2025-03-01", total: 15000, new: 3500, expansion: 2000, contraction: -800, churn: -700 },
  { date: "2025-04-01", total: 17000, new: 2800, expansion: 1800, contraction: -600, churn: -1000 },
];

const mockRevenueSeries: RevenueSeriesPoint[] = [
  { date: "2025-01-01", totalRevenue: 11000, refunds: -500 },
  { date: "2025-02-01", totalRevenue: 13000, refunds: -700 },
  { date: "2025-03-01", totalRevenue: 16000, refunds: -600 },
  { date: "2025-04-01", totalRevenue: 19000, refunds: -800 },
];

const mockPlanBreakdown: PlanBreakdownRow[] = [
  { planName: "Starter", mrr: 4000, customers: 120, churnRatePercent: 6.5 },
  { planName: "Growth", mrr: 9000, customers: 160, churnRatePercent: 3.2 },
  { planName: "Enterprise", mrr: 4000, customers: 60, churnRatePercent: 1.4 },
];

export const MOCK_COMPANY_REVENUE: CompanyRevenueMetrics = {
  companyId: "comp_1",
  currency: "USD",
  mrrSeries: mockMrrSeries,
  revenueSeries: mockRevenueSeries,
  planBreakdown: mockPlanBreakdown,
};

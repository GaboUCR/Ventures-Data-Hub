// src/types/metrics.ts

export type TimeRangeKey = "last_30_days" | "last_90_days" | "last_12_months";

export interface OverviewFilters {
  timeRange: TimeRangeKey;
  currency: string;
}

export interface MrrSeriesPoint {
  date: string;        // ISO date
  total: number;
  new: number;
  expansion: number;
  contraction: number;
  churn: number;
}

export interface CompanyRevenueMetrics {
  companyId: string;
  currency: string;

  // Headline KPIs
  currentMrr: number;
  newMrr: number;
  expansionMrr: number;
  churnedMrr: number;

  // Chart data
  mrrSeries: MrrSeriesPoint[];

  // Table
  planBreakdown: PlanRow[];
}

export interface CompanyOverviewMetrics {
  companyId: string;
  companyName: string;
  currency: string;

  mrr: number;
  arr: number;
  nrrPercent: number;
  churnRatePercent: number;
  activeCustomers: number;

  mrrChangePercent: number;
  arrChangePercent: number;

  mrrSeries: MrrSeriesPoint[];
}

export interface PortfolioCompanyRow {
  companyId: string;
  companyName: string;
  arr: number;
  growthRatePercent: number;
  nrrPercent: number;
  churnRatePercent: number;
  healthScore: number;
}

export interface PortfolioMetrics {
  totalArr: number;
  avgNrrPercent: number;
  companyCount: number;
  companies: PortfolioCompanyRow[];
}

export interface OverviewSnapshots {
  traffic: {
    sessions: number;
    signups: number;
    signupConversionRate: number; // 0–100 (%)
  };
  billing: {
    paymentSuccessRate: number;   // 0–100 (%)
    atRiskMrr: number;           // in the company's currency minor units or just number
    refundRate: number;          // 0–100 (%)
  };
}

export interface PlanRow {
  planId: string;
  planName: string;
  mrr: number;
  subscribers: number;
  churnRatePercent: number;
  growthRatePercent: number;
}

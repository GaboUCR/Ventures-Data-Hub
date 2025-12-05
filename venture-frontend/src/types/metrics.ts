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

export interface CohortCell {
  cohortLabel: string;        // e.g. "2025-01" or "Jan 2025"
  monthOffset: number;        // 0 = signup month, 1 = month+1, etc.
  retentionPercent: number;   // 0–100
}

export interface CompanyCohortMetrics {
  companyId: string;
  companyName: string;

  sixMonthRetentionPercent: number;
  twelveMonthRetentionPercent: number;
  medianMonthsToChurn: number;

  cohortCells: CohortCell[];
  preChurnInsights: string[];
}

export interface ChannelRow {
  channel: string;       // e.g. "Organic Search"
  sessions: number;
  signups: number;
  newCustomers: number;
  newMrr: number;        // in currency units
}

export interface FunnelStep {
  label: string;         // e.g. "Visits"
  count: number;         // absolute count
}

export interface CompanyAcquisitionMetrics {
  companyId: string;
  companyName: string;
  currency: string;

  sessions: number;
  signups: number;
  newPayingCustomers: number;
  visitToSignupRate: number; // 0–100

  steps: FunnelStep[];
  channels: ChannelRow[];
}

// src/types/metrics.ts

export interface PaymentHealthPoint {
  date: string;   // e.g. "2025-01-01"
  success: number;
  failed: number;
}

export interface PastDueRow {
  id: string;         // invoice id
  customer: string;   // email or name
  amount: number;     // currency units
  daysLate: number;
}

export interface CompanyBillingMetrics {
  companyId: string;
  companyName: string;
  currency: string;

  successRate: number;    // %
  failedPayments: number; // count in period
  atRiskMrr: number;      // currency
  refundRate: number;     // %

  series: PaymentHealthPoint[];
  pastDueInvoices: PastDueRow[];
}

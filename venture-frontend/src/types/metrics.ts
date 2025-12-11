// src/types/metrics.ts

export type TimeRange = "last_30_days" | "last_90_days" | "last_12_months";

export type OverviewFilters = {
  timeRange: TimeRange;
  currency: string;
};

export type MrrSeriesPoint = {
  date: string; // ISO date from backend
  total: number;
  new: number;
  expansion: number;
  contraction: number;
  churn: number;
};


export type CompanyRevenue = {
  currency: string;
  mrr: number;
  newMrr: number;
  expansionMrr: number;
  churnedMrr: number;
  mrrSeries: MrrSeriesPoint[];
  plans: PlanRow[];
};


export type CompanyOverview = {
  companyName: string;
  currency: string;

  mrr: number;
  arr: number;
  mrrChangePercent: number;
  arrChangePercent: number;
  nrrPercent: number;
  activeCustomers: number;
  churnRatePercent: number;

  mrrSeries: MrrSeriesPoint[];
};

export interface PortfolioMetrics {
  totalArr: number;
  avgNrrPercent: number;
  companyCount: number;
  companies: PortfolioCompanyRow[];
}

export type OverviewSnapshots = {
  traffic: {
    sessions: number;
    signups: number;
    signupConversionRate: number;
  };
  billing: {
    paymentSuccessRate: number;
    atRiskMrr: number;
    refundRate: number;
  };
};

export type PlanRow = {
  planId: string;
  planName: string;
  mrr: number;
  subscribers: number;
  churnRatePercent: number;
  growthRatePercent: number;
};

export type CohortCell = {
  cohortMonth: string;   // ISO date string
  monthIndex: number;    // months since signup
  retainedPercent: number; // 0–100
};

export type CompanyCohorts = {
  retention6mPercent: number;
  retention12mPercent: number;
  medianTimeToChurnMonths: number;
  heatmap: CohortCell[];
  preChurnInsights: string[];
};

export type ChannelRow = {
  channel: string;
  sessions: number;
  signups: number;
  newCustomers: number;
  newMrr: number;
};

export type FunnelStep = {
  label: string;
  count: number;
};

export type CompanyAcquisition = {
  sessions: number;
  signups: number;
  newPayingCustomers: number;
  visitToSignupRate: number;
  steps: FunnelStep[];
  channels: ChannelRow[];
};

// src/types/metrics.ts

export type PaymentHealthPoint = {
  date: string;   // ISO date
  success: number;
  failed: number;
};

export type PastDueInvoiceRow = {
  invoiceId: string;
  customerName: string | null;
  customerEmail: string | null;
  amount: number;
  currency: string;
  daysLate: number;
};

export type CompanyBilling = {
  paymentSuccessRate: number;
  failedPayments: number;
  mrrAtRisk: number;
  healthSeries: PaymentHealthPoint[];
  pastDueInvoices: PastDueInvoiceRow[];
};

// src/types/metrics.ts

export type CustomerStatus = "active" | "trialing" | "at_risk" | "churned";

export type CustomerRow = {
  customerId: string;
  email: string | null;
  name: string | null;
  currentMrr: number;
  lifetimeRevenue: number;
  firstSeenAt: string | null;   // ISO
  lastActivityAt: string | null;
  status: string;
  isHighValue: boolean;
};

export type CustomerDetail = CustomerRow; // extend later if you add more fields

export type CompanyCustomers = {
  summary: {
    totalCustomers: number;
    newCustomers: number;
    highValueCustomers: number;
  };
  customers: CustomerRow[];
};


export type IntegrationStatus = "connected" | "missing" | "error";

export interface PortfolioCompany {
  id: string;
  name: string;
  stage: "pre_seed" | "seed" | "series_a" | "series_b" | "other";
  sector: string;
  owner: string; // partner / account owner

  arr: number;                    // annual recurring revenue
  mrr: number;                    // monthly recurring revenue
  mrrGrowthRatePercent: number;   // e.g. 18.4
  nrrPercent: number;             // net revenue retention
  churnRatePercent: number;       // logo or MRR churn
  paymentSuccessRate: number;     // billing health
  mrrAtRisk: number;              // from past-due invoices
  visitToSignupRate?: number;     // GA4 conversion, optional

  integrations: {
    stripe: IntegrationStatus;
    ga4: IntegrationStatus;
  };
}

export interface PortfolioAlert {
  id: string;
  companyId: string;
  companyName: string;
  severity: "info" | "warning" | "critical";
  category: "billing" | "revenue" | "retention" | "acquisition" | "integration";
  message: string;
  createdAt: string; // ISO
}

export type PortfolioSummary = {
  totalCompanies: number;
  rocketships: number;
  leakyBuckets: number;
  flatButSolid: number;
  atRisk: number;
  portfolioArr: number;
  medianGrowthPercent: number;
  medianNrrPercent: number;
};

export type PortfolioOverview = {
  summary: PortfolioSummary;
  companies: PortfolioCompanyRow[];
};

// src/types/metrics.ts

export type PortfolioCompanyCategory =
  | "rocketship"
  | "leaky_bucket"
  | "flat_but_solid"
  | "at_risk";

export type PortfolioCompanyRow = {
  companyId: string;
  companyName: string;
  stage: string | null;
  sector: string | null;
  mrr: number;
  arr: number;
  growthPercent: number;
  nrrPercent: number;
  churnRatePercent: number;
  category: PortfolioCompanyCategory;
};

// src/hooks/useCompanyCohorts.ts
"use client";

import { useQuery } from "@tanstack/react-query";
import { CompanyCohortMetrics, CohortCell, OverviewFilters } from "@/types/metrics";

const fakeDelay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export function useCompanyCohorts(companyId: string, _filters: OverviewFilters) {
  return useQuery<CompanyCohortMetrics>({
    queryKey: ["companyCohorts", companyId, _filters],
    queryFn: async () => {
      await fakeDelay(300);

      // Mock cohorts: 4 signup cohorts, 0–5 months of retention
      const cohorts = ["2024-11", "2024-12", "2025-01", "2025-02"];

      const cohortCells: CohortCell[] = [
        // 2024-11 cohort
        { cohortLabel: "2024-11", monthOffset: 0, retentionPercent: 100 },
        { cohortLabel: "2024-11", monthOffset: 1, retentionPercent: 92 },
        { cohortLabel: "2024-11", monthOffset: 2, retentionPercent: 86 },
        { cohortLabel: "2024-11", monthOffset: 3, retentionPercent: 80 },
        { cohortLabel: "2024-11", monthOffset: 4, retentionPercent: 74 },
        { cohortLabel: "2024-11", monthOffset: 5, retentionPercent: 70 },

        // 2024-12 cohort
        { cohortLabel: "2024-12", monthOffset: 0, retentionPercent: 100 },
        { cohortLabel: "2024-12", monthOffset: 1, retentionPercent: 90 },
        { cohortLabel:  "2024-12", monthOffset: 2, retentionPercent: 84 },
        { cohortLabel: "2024-12", monthOffset: 3, retentionPercent: 77 },
        { cohortLabel: "2024-12", monthOffset: 4, retentionPercent: 71 },

        // 2025-01 cohort
        { cohortLabel: "2025-01", monthOffset: 0, retentionPercent: 100 },
        { cohortLabel: "2025-01", monthOffset: 1, retentionPercent: 93 },
        { cohortLabel: "2025-01", monthOffset: 2, retentionPercent: 88 },
        { cohortLabel: "2025-01", monthOffset: 3, retentionPercent: 83 },

        // 2025-02 cohort
        { cohortLabel: "2025-02", monthOffset: 0, retentionPercent: 100 },
        { cohortLabel: "2025-02", monthOffset: 1, retentionPercent: 95 },
        { cohortLabel: "2025-02", monthOffset: 2, retentionPercent: 91 },
      ];

      const preChurnInsights = [
        "Users who churned often visited /pricing and /account/cancel in the 7 days before cancel.",
        "Churned customers had 40–60% fewer sessions in the last month compared to retained ones.",
        "A large share of churn is concentrated in the Starter plan during months 2–3.",
      ];

      const metrics: CompanyCohortMetrics = {
        companyId,
        companyName: "Acme SaaS", // mock; later this can come from backend or a shared meta hook
        sixMonthRetentionPercent: 74.5,
        twelveMonthRetentionPercent: 63.2,
        medianMonthsToChurn: 10.2,
        cohortCells,
        preChurnInsights,
      };

      return metrics;
    },
  });
}

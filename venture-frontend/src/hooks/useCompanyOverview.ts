"use client";

import { useQuery } from "@tanstack/react-query";
import { CompanyOverviewMetrics, OverviewFilters } from "@/types/metrics";
import { MOCK_COMPANY_OVERVIEW } from "@/mocks/companyOverview";

const fakeDelay = (ms: number) => new Promise((r) => setTimeout(r, ms));

export function useCompanyOverview(companyId: string, filters: OverviewFilters) {
  return useQuery<CompanyOverviewMetrics>({
    queryKey: ["companyOverview", companyId, filters],
    queryFn: async () => {
      await fakeDelay(300);
      return { ...MOCK_COMPANY_OVERVIEW, companyId };
    },
  });
}

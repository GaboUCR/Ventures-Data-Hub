// src/hooks/useCompanyRevenue.ts
import { useQuery } from "@tanstack/react-query";
import { CompanyRevenueMetrics, OverviewFilters } from "../types/metrics";
import { MOCK_COMPANY_REVENUE } from "../mocks/companyRevenue";

function fakeDelay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export function useCompanyRevenue(companyId: string, filters: OverviewFilters) {
  return useQuery<CompanyRevenueMetrics>({
    queryKey: ["companyRevenue", companyId, filters],
    queryFn: async () => {
      await fakeDelay(300);
      return { ...MOCK_COMPANY_REVENUE, companyId };
    },
  });
}

"use client";

import { useQuery } from "@tanstack/react-query";
import { PortfolioMetrics } from "@/types/metrics";
import { MOCK_PORTFOLIO_METRICS } from "@/mocks/portfolioMetrics";

const fakeDelay = (ms: number) => new Promise((r) => setTimeout(r, ms));

export function usePortfolioMetrics() {
  return useQuery<PortfolioMetrics>({
    queryKey: ["portfolioMetrics"],
    queryFn: async () => {
      await fakeDelay(300);
      return MOCK_PORTFOLIO_METRICS;
    },
  });
}

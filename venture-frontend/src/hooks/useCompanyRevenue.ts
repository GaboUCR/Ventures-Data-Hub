// src/hooks/useCompanyRevenue.ts
"use client";

import { useQuery } from "@tanstack/react-query";
import { API_BASE_URL } from "@/lib/config";
import { useAuth } from "@/context/AuthContext";
import type { CompanyRevenue, OverviewFilters } from "@/types/metrics";

async function fetchCompanyRevenue(
  token: string,
  companyId: string,
  filters: OverviewFilters
): Promise<CompanyRevenue> {
  const params = new URLSearchParams({
    time_range: filters.timeRange,
    currency: filters.currency,
  });

  const res = await fetch(
    `${API_BASE_URL}/companies/${companyId}/revenue?${params.toString()}`,
    {
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
    }
  );

  if (!res.ok) {
    let detail = "Failed to load company revenue";
    try {
      const body = await res.json();
      if (body?.detail) {
        detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
      }
    } catch {
      // ignore
    }
    throw new Error(detail);
  }

  return (await res.json()) as CompanyRevenue;
}

export function useCompanyRevenue(companyId: string, filters: OverviewFilters) {
  const { token } = useAuth();

  return useQuery<CompanyRevenue, Error>({
    queryKey: ["companyRevenue", companyId, filters],
    queryFn: () => {
      if (!token) throw new Error("Not authenticated");
      return fetchCompanyRevenue(token, companyId, filters);
    },
    enabled: Boolean(token && companyId),
  });
}

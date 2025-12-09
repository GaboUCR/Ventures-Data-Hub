// src/hooks/useCompanyOverview.ts
"use client";

import { useQuery } from "@tanstack/react-query";
import { API_BASE_URL } from "@/lib/config";
import { useAuth } from "@/context/AuthContext";
import type { CompanyOverview, OverviewFilters } from "@/types/metrics";

async function fetchCompanyOverview(
  token: string,
  companyId: string,
  filters: OverviewFilters
): Promise<CompanyOverview> {
  const params = new URLSearchParams({
    time_range: filters.timeRange,
    currency: filters.currency,
  });

  const res = await fetch(
    `${API_BASE_URL}/companies/${companyId}/overview?${params.toString()}`,
    {
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
    }
  );

  if (!res.ok) {
    let detail = "Failed to load company overview";
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

  const data = (await res.json()) as CompanyOverview;

  // If you ever need to massage the data (e.g. ensure date is a string), do it here
  return data;
}

export function useCompanyOverview(companyId: string, filters: OverviewFilters) {
  const { token } = useAuth();

  return useQuery<CompanyOverview, Error>({
    queryKey: ["companyOverview", companyId, filters],
    queryFn: () => {
      if (!token) throw new Error("Not authenticated");
      return fetchCompanyOverview(token, companyId, filters);
    },
    enabled: Boolean(token && companyId),
  });
}

// src/hooks/useCompanyCohorts.ts
"use client";

import { useQuery } from "@tanstack/react-query";
import { API_BASE_URL } from "@/lib/config";
import { useAuth } from "@/context/AuthContext";
import type { CompanyCohorts, OverviewFilters } from "@/types/metrics";

async function fetchCompanyCohorts(
  token: string,
  companyId: string,
  filters: OverviewFilters
): Promise<CompanyCohorts> {
  const params = new URLSearchParams({
    time_range: filters.timeRange,
  });

  const res = await fetch(
    `${API_BASE_URL}/companies/${companyId}/cohorts?${params.toString()}`,
    {
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
    }
  );

  if (!res.ok) {
    let detail = "Failed to load cohorts";
    try {
      const body = await res.json();
      if (body?.detail) {
        detail =
          typeof body.detail === "string"
            ? body.detail
            : JSON.stringify(body.detail);
      }
    } catch {
      // ignore
    }
    throw new Error(detail);
  }

  return (await res.json()) as CompanyCohorts;
}

export function useCompanyCohorts(companyId: string, filters: OverviewFilters) {
  const { token } = useAuth();

  return useQuery<CompanyCohorts, Error>({
    queryKey: ["companyCohorts", companyId, filters],
    queryFn: () => {
      if (!token) throw new Error("Not authenticated");
      return fetchCompanyCohorts(token, companyId, filters);
    },
    enabled: Boolean(token && companyId),
  });
}

// src/hooks/useCompanyAcquisition.ts
"use client";

import { useQuery } from "@tanstack/react-query";
import { API_BASE_URL } from "@/lib/config";
import { useAuth } from "@/context/AuthContext";
import type { CompanyAcquisition, OverviewFilters } from "@/types/metrics";

async function fetchCompanyAcquisition(
  token: string,
  companyId: string,
  filters: OverviewFilters
): Promise<CompanyAcquisition> {
  const params = new URLSearchParams({
    time_range: filters.timeRange,
  });

  const res = await fetch(
    `${API_BASE_URL}/companies/${companyId}/acquisition?${params.toString()}`,
    {
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
    }
  );

  if (!res.ok) {
    let detail = "Failed to load acquisition";
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

  return (await res.json()) as CompanyAcquisition;
}

export function useCompanyAcquisition(
  companyId: string,
  filters: OverviewFilters
) {
  const { token } = useAuth();

  return useQuery<CompanyAcquisition, Error>({
    queryKey: ["companyAcquisition", companyId, filters],
    queryFn: () => {
      if (!token) throw new Error("Not authenticated");
      return fetchCompanyAcquisition(token, companyId, filters);
    },
    enabled: Boolean(token && companyId),
  });
}

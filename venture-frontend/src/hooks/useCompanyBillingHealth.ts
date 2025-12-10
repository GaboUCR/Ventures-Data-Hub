// src/hooks/useCompanyBillingHealth.ts
"use client";

import { useQuery } from "@tanstack/react-query";
import { API_BASE_URL } from "@/lib/config";
import { useAuth } from "@/context/AuthContext";
import type { CompanyBilling, OverviewFilters } from "@/types/metrics";

async function fetchCompanyBilling(
  token: string,
  companyId: string,
  filters: OverviewFilters
): Promise<CompanyBilling> {
  const params = new URLSearchParams({
    time_range: filters.timeRange,
  });

  const res = await fetch(
    `${API_BASE_URL}/companies/${companyId}/billing?${params.toString()}`,
    {
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
    }
  );

  if (!res.ok) {
    let detail = "Failed to load billing health";
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

  return (await res.json()) as CompanyBilling;
}

export function useCompanyBillingHealth(
  companyId: string,
  filters: OverviewFilters
) {
  const { token } = useAuth();

  return useQuery<CompanyBilling, Error>({
    queryKey: ["companyBilling", companyId, filters],
    queryFn: () => {
      if (!token) throw new Error("Not authenticated");
      return fetchCompanyBilling(token, companyId, filters);
    },
    enabled: Boolean(token && companyId),
  });
}

// src/hooks/useOverviewSnapshots.ts
"use client";

import { useQuery } from "@tanstack/react-query";
import { API_BASE_URL } from "@/lib/config";
import { useAuth } from "@/context/AuthContext";
import type { OverviewFilters, OverviewSnapshots } from "@/types/metrics";

async function fetchOverviewSnapshots(
  token: string,
  companyId: string,
  filters: OverviewFilters
): Promise<OverviewSnapshots> {
  const params = new URLSearchParams({
    time_range: filters.timeRange,
  });

  const res = await fetch(
    `${API_BASE_URL}/companies/${companyId}/overview/snapshots?${params.toString()}`,
    {
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
    }
  );

  if (!res.ok) {
    let detail = "Failed to load overview snapshots";
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

  return (await res.json()) as OverviewSnapshots;
}

export function useOverviewSnapshots(companyId: string, filters: OverviewFilters) {
  const { token } = useAuth();

  return useQuery<OverviewSnapshots, Error>({
    queryKey: ["overviewSnapshots", companyId, filters],
    queryFn: () => {
      if (!token) throw new Error("Not authenticated");
      return fetchOverviewSnapshots(token, companyId, filters);
    },
    enabled: Boolean(token && companyId),
  });
}

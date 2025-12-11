// src/hooks/usePortfolioOverview.ts
"use client";

import { useQuery } from "@tanstack/react-query";
import { API_BASE_URL } from "@/lib/config";
import { useAuth } from "@/context/AuthContext";
import type { PortfolioOverview } from "@/types/metrics";

async function fetchPortfolioOverview(token: string): Promise<PortfolioOverview> {
  const res = await fetch(`${API_BASE_URL}/portfolio/overview`, {
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
  });

  if (!res.ok) {
    let detail = "Failed to load portfolio overview";
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

  return (await res.json()) as PortfolioOverview;
}

export function usePortfolioOverview() {
  const { token } = useAuth();

  return useQuery<PortfolioOverview, Error>({
    queryKey: ["portfolioOverview"],
    queryFn: () => {
      if (!token) throw new Error("Not authenticated");
      return fetchPortfolioOverview(token);
    },
    enabled: Boolean(token),
  });
}

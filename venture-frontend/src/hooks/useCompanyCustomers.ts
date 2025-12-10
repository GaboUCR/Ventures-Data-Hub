// src/hooks/useCompanyCustomers.ts
"use client";

import { useQuery } from "@tanstack/react-query";
import { API_BASE_URL } from "@/lib/config";
import { useAuth } from "@/context/AuthContext";
import type { CompanyCustomers, OverviewFilters, CustomerDetail } from "@/types/metrics";

async function fetchCompanyCustomers(
  token: string,
  companyId: string,
  filters: OverviewFilters
): Promise<CompanyCustomers> {
  const params = new URLSearchParams({
    time_range: filters.timeRange,
  });

  const res = await fetch(
    `${API_BASE_URL}/companies/${companyId}/customers?${params.toString()}`,
    {
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
    }
  );

  if (!res.ok) {
    let detail = "Failed to load customers";
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

  return (await res.json()) as CompanyCustomers;
}

async function fetchCustomerDetail(
  token: string,
  companyId: string,
  customerId: string
): Promise<CustomerDetail> {
  const res = await fetch(
    `${API_BASE_URL}/companies/${companyId}/customers/${customerId}`,
    {
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
    }
  );

  if (!res.ok) {
    let detail = "Failed to load customer detail";
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

  return (await res.json()) as CustomerDetail;
}

export function useCompanyCustomers(
  companyId: string,
  filters: OverviewFilters
) {
  const { token } = useAuth();

  const baseQuery = useQuery<CompanyCustomers, Error>({
    queryKey: ["companyCustomers", companyId, filters],
    queryFn: () => {
      if (!token) throw new Error("Not authenticated");
      return fetchCompanyCustomers(token, companyId, filters);
    },
    enabled: Boolean(token && companyId),
  });

  return baseQuery;
}

export function useCustomerDetail(
  companyId: string,
  customerId: string | null
) {
  const { token } = useAuth();

  return useQuery<CustomerDetail, Error>({
    queryKey: ["customerDetail", companyId, customerId],
    queryFn: () => {
      if (!token || !customerId) throw new Error("Not authenticated");
      return fetchCustomerDetail(token, companyId, customerId);
    },
    enabled: Boolean(token && companyId && customerId),
  });
}

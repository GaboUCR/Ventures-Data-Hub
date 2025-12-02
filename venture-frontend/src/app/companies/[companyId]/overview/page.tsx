"use client";

import { useParams } from "next/navigation";
import { useCompanyOverview } from "@/hooks/useCompanyOverview";
import { KpiCard } from "@/components/kpis/KpiCard.tsx";
import { MrrAreaChart } from "@/components/charts/MrrAreaChart";
import { OverviewFilters } from "@/types/metrics";

export default function CompanyOverviewPage() {
  const params = useParams<{ companyId: string }>();
  const companyId = params.companyId ?? "comp_1";

  const filters: OverviewFilters = {
    timeRange: "last_90_days",
    currency: "USD",
  };

  const { data, isLoading, error } = useCompanyOverview(companyId, filters);

  if (isLoading) return <div className="p-6">Loading overview…</div>;
  if (error || !data) return <div className="p-6 text-red-400">Failed to load overview.</div>;

  return (
    <div className="p-6 space-y-6">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold text-slate-50">{data.companyName}</h1>
        <p className="text-sm text-slate-400">Overview · last 90 days</p>
      </header>

      {/* KPI row */}
      <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-5">
        <KpiCard
          label="MRR"
          value={`${data.currency} ${data.mrr.toLocaleString()}`}
          helper={`${data.mrrChangePercent > 0 ? "▲" : "▼"} ${data.mrrChangePercent.toFixed(1)}% vs prev`}
        />
        <KpiCard
          label="ARR"
          value={`${data.currency} ${data.arr.toLocaleString()}`}
          helper={`${data.arrChangePercent.toFixed(1)}% vs prev`}
        />
        <KpiCard
          label="NRR"
          value={`${data.nrrPercent.toFixed(1)}%`}
          helper={data.nrrPercent >= 120 ? "Excellent retention" : "Room to improve"}
        />
        <KpiCard
          label="Active customers"
          value={data.activeCustomers.toLocaleString()}
        />
        <KpiCard
          label="Churn rate"
          value={`${data.churnRatePercent.toFixed(1)}%`}
        />
      </div>

      <MrrAreaChart data={data.mrrSeries} />
    </div>
  );
}

"use client";

import Link from "next/link";
import { usePortfolioMetrics } from "@/hooks/usePortfolioMetrics";

export default function PortfolioPage() {
  const { data, isLoading, error } = usePortfolioMetrics();

  if (isLoading) return <div className="p-6">Loading portfolio…</div>;
  if (error || !data) return <div className="p-6 text-red-400">Failed to load portfolio.</div>;

  return (
    <div className="p-6 space-y-4">
      <header>
        <h1 className="text-2xl font-semibold text-slate-50">Portfolio</h1>
        <p className="text-sm text-slate-400">
          {data.companyCount} companies · Total ARR ${data.totalArr.toLocaleString()}
        </p>
      </header>

      <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/60">
        <table className="min-w-full text-sm">
          <thead className="border-b border-slate-800 bg-slate-900/80 text-left text-slate-400">
            <tr>
              <th className="px-4 py-2">Company</th>
              <th className="px-4 py-2">ARR</th>
              <th className="px-4 py-2">Growth</th>
              <th className="px-4 py-2">NRR</th>
              <th className="px-4 py-2">Churn</th>
              <th className="px-4 py-2">Health</th>
            </tr>
          </thead>
          <tbody>
            {data.companies.map((c) => (
              <tr
                key={c.companyId}
                className="border-b border-slate-800/60 text-slate-100 hover:bg-slate-800/60"
              >
                <td className="px-4 py-2">
                  <Link href={`/companies/${c.companyId}/overview`} className="underline-offset-2 hover:underline">
                    {c.companyName}
                  </Link>
                </td>
                <td className="px-4 py-2">${c.arr.toLocaleString()}</td>
                <td className="px-4 py-2">{c.growthRatePercent.toFixed(1)}%</td>
                <td className="px-4 py-2">{c.nrrPercent.toFixed(1)}%</td>
                <td className="px-4 py-2">{c.churnRatePercent.toFixed(1)}%</td>
                <td className="px-4 py-2">{c.healthScore}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

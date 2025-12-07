// src/components/tables/PortfolioCompanyTable.tsx
"use client";

import { PortfolioCompany } from "@/types/metrics";

interface PortfolioCompanyTableProps {
  companies: PortfolioCompany[];
  currency: string;
  emptyLabel?: string;
}

export function PortfolioCompanyTable({
  companies,
  currency,
  emptyLabel = "No companies match this segment.",
}: PortfolioCompanyTableProps) {
  return (
    <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/70">
      <table className="min-w-full text-sm">
        <thead className="border-b border-slate-800 bg-slate-900/80 text-left text-slate-400">
          <tr>
            <th className="px-4 py-2">Company</th>
            <th className="px-4 py-2">Stage</th>
            <th className="px-4 py-2">ARR</th>
            <th className="px-4 py-2">MRR growth</th>
            <th className="px-4 py-2">NRR</th>
            <th className="px-4 py-2">Churn</th>
            <th className="px-4 py-2">Payment success</th>
            <th className="px-4 py-2">MRR at risk</th>
          </tr>
        </thead>
        <tbody>
          {companies.length === 0 ? (
            <tr>
              <td
                colSpan={8}
                className="px-4 py-4 text-center text-slate-500"
              >
                {emptyLabel}
              </td>
            </tr>
          ) : (
            companies.map((c) => (
              <tr
                key={c.id}
                className="border-b border-slate-800/60 text-slate-100 last:border-b-0 hover:bg-slate-800/40"
              >
                <td className="px-4 py-2">{c.name}</td>
                <td className="px-4 py-2 capitalize text-xs text-slate-300">
                  {c.stage.replace("_", " ")}
                </td>
                <td className="px-4 py-2">
                  {currency} {c.arr.toLocaleString()}
                </td>
                <td className="px-4 py-2">
                  {c.mrrGrowthRatePercent.toFixed(1)}%
                </td>
                <td className="px-4 py-2">
                  {c.nrrPercent.toFixed(1)}%
                </td>
                <td className="px-4 py-2">
                  {c.churnRatePercent.toFixed(1)}%
                </td>
                <td className="px-4 py-2">
                  {c.paymentSuccessRate.toFixed(1)}%
                </td>
                <td className="px-4 py-2">
                  {currency} {c.mrrAtRisk.toLocaleString()}
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

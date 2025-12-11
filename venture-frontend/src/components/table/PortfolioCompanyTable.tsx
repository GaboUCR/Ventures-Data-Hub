// src/components/tables/PortfolioCompanyTable.tsx
"use client";

import Link from "next/link";
import type { PortfolioCompanyRow } from "@/types/metrics";

export function PortfolioCompanyTable({ rows }: { rows: PortfolioCompanyRow[] }) {
  return (
    <div className="overflow-x-auto text-xs">
      <table className="min-w-full border-collapse">
        <thead>
          <tr className="border-b border-slate-800 text-slate-400">
            <th className="px-2 py-2 text-left font-medium">Company</th>
            <th className="px-2 py-2 text-left font-medium">Stage</th>
            <th className="px-2 py-2 text-left font-medium">Sector</th>
            <th className="px-2 py-2 text-right font-medium">MRR</th>
            <th className="px-2 py-2 text-right font-medium">ARR</th>
            <th className="px-2 py-2 text-right font-medium">Growth</th>
            <th className="px-2 py-2 text-right font-medium">NRR</th>
            <th className="px-2 py-2 text-right font-medium">Churn</th>
            <th className="px-2 py-2 text-left font-medium">Category</th>
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td
                colSpan={9}
                className="px-2 py-4 text-center text-slate-500"
              >
                No companies in portfolio yet.
              </td>
            </tr>
          ) : (
            rows.map((row) => (
              <tr
                key={row.companyId}
                className="border-b border-slate-800/80 hover:bg-slate-900/60"
              >
                <td className="px-2 py-2">
                  <Link
                    href={`/companies/${row.companyId}/overview`}
                    className="text-slate-200 hover:underline"
                  >
                    {row.companyName}
                  </Link>
                </td>
                <td className="px-2 py-2 text-slate-300">
                  {row.stage || "—"}
                </td>
                <td className="px-2 py-2 text-slate-300">
                  {row.sector || "—"}
                </td>
                <td className="px-2 py-2 text-right">
                  {row.mrr.toLocaleString(undefined, {
                    minimumFractionDigits: 0,
                    maximumFractionDigits: 0,
                  })}
                </td>
                <td className="px-2 py-2 text-right">
                  {row.arr.toLocaleString(undefined, {
                    minimumFractionDigits: 0,
                    maximumFractionDigits: 0,
                  })}
                </td>
                <td className="px-2 py-2 text-right">
                  {row.growthPercent.toFixed(1)}%
                </td>
                <td className="px-2 py-2 text-right">
                  {row.nrrPercent.toFixed(1)}%
                </td>
                <td className="px-2 py-2 text-right">
                  {row.churnRatePercent.toFixed(1)}%
                </td>
                <td className="px-2 py-2">
                  <CategoryBadge category={row.category} />
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

function CategoryBadge({ category }: { category: PortfolioCompanyRow["category"] }) {
  const labelMap: Record<string, string> = {
    rocketship: "Rocketship",
    leaky_bucket: "Leaky bucket",
    flat_but_solid: "Flat but solid",
    at_risk: "At risk",
  };

  return (
    <span className="inline-flex rounded-full bg-slate-800/80 px-2 py-0.5 text-[10px] uppercase tracking-wide text-slate-300">
      {labelMap[category] ?? category}
    </span>
  );
}

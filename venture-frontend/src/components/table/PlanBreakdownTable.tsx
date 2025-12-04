// src/components/tables/PlanBreakdownTable.tsx
"use client";

import { PlanRow } from "@/types/metrics";

interface PlanBreakdownTableProps {
  rows: PlanRow[];
  currency: string;
}

export function PlanBreakdownTable({ rows, currency }: PlanBreakdownTableProps) {
  return (
    <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/70">
      <table className="min-w-full text-sm">
        <thead className="border-b border-slate-800 bg-slate-900/80 text-left text-slate-400">
          <tr>
            <th className="px-4 py-2">Plan</th>
            <th className="px-4 py-2">MRR</th>
            <th className="px-4 py-2">Subscribers</th>
            <th className="px-4 py-2">Churn</th>
            <th className="px-4 py-2">Growth</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((plan) => (
            <tr
              key={plan.planId}
              className="border-b border-slate-800/60 text-slate-100 last:border-b-0 hover:bg-slate-800/40"
            >
              <td className="px-4 py-2">{plan.planName}</td>
              <td className="px-4 py-2">
                {currency} {plan.mrr.toLocaleString()}
              </td>
              <td className="px-4 py-2">{plan.subscribers.toLocaleString()}</td>
              <td className="px-4 py-2">{plan.churnRatePercent.toFixed(1)}%</td>
              <td className="px-4 py-2">{plan.growthRatePercent.toFixed(1)}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// src/components/tables/CustomerListTable.tsx
"use client";

import { CustomerRow } from "@/types/metrics";

interface CustomerListTableProps {
  rows: CustomerRow[];
  currency: string;
  onRowClick?: (id: string) => void;
}

export function CustomerListTable({ rows, currency, onRowClick }: CustomerListTableProps) {
  return (
    <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/70">
      <table className="min-w-full text-sm">
        <thead className="border-b border-slate-800 bg-slate-900/80 text-left text-slate-400">
          <tr>
            <th className="px-4 py-2">Customer</th>
            <th className="px-4 py-2">Current MRR</th>
            <th className="px-4 py-2">Lifetime revenue</th>
            <th className="px-4 py-2">First seen</th>
            <th className="px-4 py-2">Last activity</th>
            <th className="px-4 py-2">Status</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const statusColor =
              row.status === "active"
                ? "text-emerald-300 bg-emerald-500/10 border-emerald-500/30"
                : row.status === "trialing"
                ? "text-sky-300 bg-sky-500/10 border-sky-500/30"
                : row.status === "at_risk"
                ? "text-amber-300 bg-amber-500/10 border-amber-500/30"
                : "text-slate-300 bg-slate-700/40 border-slate-600/60";

            return (
              <tr
                key={row.id}
                className="border-b border-slate-800/60 text-slate-100 last:border-b-0 hover:bg-slate-800/40 cursor-pointer"
                onClick={() => onRowClick?.(row.id)}
              >
                <td className="px-4 py-2">
                  <div className="flex flex-col">
                    <span className="font-medium">{row.name}</span>
                    <span className="text-xs text-slate-400">{row.email}</span>
                  </div>
                </td>
                <td className="px-4 py-2">
                  {currency} {row.currentMrr.toLocaleString()}
                </td>
                <td className="px-4 py-2">
                  {currency} {row.lifetimeRevenue.toLocaleString()}
                </td>
                <td className="px-4 py-2 text-xs text-slate-300">
                  {new Date(row.firstSeenAt).toLocaleDateString()}
                </td>
                <td className="px-4 py-2 text-xs text-slate-300">
                  {new Date(row.lastActivityAt).toLocaleDateString()}
                </td>
                <td className="px-4 py-2">
                  <span
                    className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium ${statusColor}`}
                  >
                    {row.status.replace("_", " ")}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

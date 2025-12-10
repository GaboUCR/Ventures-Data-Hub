// src/components/tables/CustomerListTable.tsx
"use client";

import type { CustomerRow } from "@/types/metrics";

export function CustomerListTable({
  rows,
  onRowClick,
}: {
  rows: CustomerRow[];
  onRowClick?: (id: string) => void;
}) {
  return (
    <div className="overflow-x-auto text-xs">
      <table className="min-w-full border-collapse">
        <thead>
          <tr className="border-b border-slate-800 text-slate-400">
            <th className="px-2 py-2 text-left font-medium">Customer</th>
            <th className="px-2 py-2 text-right font-medium">Current MRR</th>
            <th className="px-2 py-2 text-right font-medium">Lifetime revenue</th>
            <th className="px-2 py-2 text-left font-medium">First seen</th>
            <th className="px-2 py-2 text-left font-medium">Last activity</th>
            <th className="px-2 py-2 text-left font-medium">Status</th>
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td
                colSpan={6}
                className="px-2 py-4 text-center text-slate-500"
              >
                No customers found.
              </td>
            </tr>
          ) : (
            rows.map((row) => {
              const firstSeen = row.firstSeenAt
                ? new Date(row.firstSeenAt).toLocaleDateString()
                : "—";
              const lastActivity = row.lastActivityAt
                ? new Date(row.lastActivityAt).toLocaleDateString()
                : "—";

              return (
                <tr
                  key={row.customerId}
                  className="border-b border-slate-800/80 hover:bg-slate-900/60 cursor-pointer"
                  onClick={() => onRowClick?.(row.customerId)}
                >
                  <td className="px-2 py-2">
                    <div className="flex flex-col">
                      <span className="text-slate-200">
                        {row.name || row.email || row.customerId}
                      </span>
                      {row.email && (
                        <span className="text-slate-400">{row.email}</span>
                      )}
                      {row.isHighValue && (
                        <span className="mt-1 inline-flex w-fit rounded-full bg-emerald-500/10 px-2 py-0.5 text-[10px] font-medium text-emerald-300">
                          High value
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-2 py-2 text-right">
                    {row.currentMrr.toLocaleString(undefined, {
                      minimumFractionDigits: 0,
                      maximumFractionDigits: 0,
                    })}
                  </td>
                  <td className="px-2 py-2 text-right">
                    {row.lifetimeRevenue.toLocaleString(undefined, {
                      minimumFractionDigits: 0,
                      maximumFractionDigits: 0,
                    })}
                  </td>
                  <td className="px-2 py-2">{firstSeen}</td>
                  <td className="px-2 py-2">{lastActivity}</td>
                  <td className="px-2 py-2">
                    <span className="inline-flex rounded-full bg-slate-800/80 px-2 py-0.5 text-[10px] uppercase tracking-wide text-slate-300">
                      {row.status}
                    </span>
                  </td>
                </tr>
              );
            })
          )}
        </tbody>
      </table>
    </div>
  );
}

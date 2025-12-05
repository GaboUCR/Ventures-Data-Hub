// src/components/tables/ChannelPerformanceTable.tsx
"use client";

import { ChannelRow } from "@/types/metrics";

interface ChannelPerformanceTableProps {
  rows: ChannelRow[];
  currency: string;
}

export function ChannelPerformanceTable({ rows, currency }: ChannelPerformanceTableProps) {
  return (
    <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/70">
      <table className="min-w-full text-sm">
        <thead className="border-b border-slate-800 bg-slate-900/80 text-left text-slate-400">
          <tr>
            <th className="px-4 py-2">Channel</th>
            <th className="px-4 py-2">Sessions</th>
            <th className="px-4 py-2">Signups</th>
            <th className="px-4 py-2">New customers</th>
            <th className="px-4 py-2">New MRR</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={row.channel}
              className="border-b border-slate-800/60 text-slate-100 last:border-b-0 hover:bg-slate-800/40"
            >
              <td className="px-4 py-2">{row.channel}</td>
              <td className="px-4 py-2">{row.sessions.toLocaleString()}</td>
              <td className="px-4 py-2">{row.signups.toLocaleString()}</td>
              <td className="px-4 py-2">{row.newCustomers.toLocaleString()}</td>
              <td className="px-4 py-2">
                {currency} {row.newMrr.toLocaleString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

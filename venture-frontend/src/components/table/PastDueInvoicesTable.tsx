// src/components/tables/PastDueInvoicesTable.tsx
"use client";

import { PastDueRow } from "@/types/metrics";

interface PastDueInvoicesTableProps {
  rows: PastDueRow[];
  currency: string;
}

export function PastDueInvoicesTable({ rows, currency }: PastDueInvoicesTableProps) {
  return (
    <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/70">
      <table className="min-w-full text-sm">
        <thead className="border-b border-slate-800 bg-slate-900/80 text-left text-slate-400">
          <tr>
            <th className="px-4 py-2">Invoice</th>
            <th className="px-4 py-2">Customer</th>
            <th className="px-4 py-2">Amount</th>
            <th className="px-4 py-2">Days late</th>
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td
                colSpan={4}
                className="px-4 py-4 text-center text-slate-500"
              >
                No past-due invoices 🎉
              </td>
            </tr>
          ) : (
            rows.map((row) => (
              <tr
                key={row.id}
                className="border-b border-slate-800/60 text-slate-100 last:border-b-0 hover:bg-slate-800/40"
              >
                <td className="px-4 py-2 font-mono text-xs">{row.id}</td>
                <td className="px-4 py-2">{row.customer}</td>
                <td className="px-4 py-2">
                  {currency} {row.amount.toLocaleString()}
                </td>
                <td className="px-4 py-2">{row.daysLate}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

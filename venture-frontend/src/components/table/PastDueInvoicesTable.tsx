// src/components/tables/PastDueInvoicesTable.tsx
"use client";

import type { PastDueInvoiceRow } from "@/types/metrics";

export function PastDueInvoicesTable({ rows }: { rows: PastDueInvoiceRow[] }) {
  return (
    <div className="overflow-x-auto text-xs">
      <table className="min-w-full border-collapse">
        <thead>
          <tr className="border-b border-slate-800 text-slate-400">
            <th className="px-2 py-2 text-left font-medium">Invoice</th>
            <th className="px-2 py-2 text-left font-medium">Customer</th>
            <th className="px-2 py-2 text-right font-medium">Amount</th>
            <th className="px-2 py-2 text-right font-medium">Days late</th>
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td
                colSpan={4}
                className="px-2 py-4 text-center text-slate-500"
              >
                No past-due invoices 🎉
              </td>
            </tr>
          ) : (
            rows.map((row) => (
              <tr
                key={row.invoiceId}
                className="border-b border-slate-800/80 hover:bg-slate-900/60"
              >
                <td className="px-2 py-2 text-slate-200">{row.invoiceId}</td>
                <td className="px-2 py-2">
                  <div className="flex flex-col">
                    <span className="text-slate-200">
                      {row.customerName || "—"}
                    </span>
                    {row.customerEmail && (
                      <span className="text-slate-400">
                        {row.customerEmail}
                      </span>
                    )}
                  </div>
                </td>
                <td className="px-2 py-2 text-right">
                  {row.currency}{" "}
                  {row.amount.toLocaleString(undefined, {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })}
                </td>
                <td className="px-2 py-2 text-right">{row.daysLate}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

// src/components/customers/CustomerDetailDrawer.tsx
"use client";

import type { CustomerDetail } from "@/types/metrics";

export function CustomerDetailDrawer({
  customer,
  onClose,
}: {
  customer: CustomerDetail | null;
  onClose?: () => void;
}) {
  if (!customer) return null;

  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-black/40">
      <div className="h-full w-full max-w-md border-l border-slate-800 bg-slate-950/95 p-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div>
            <h2 className="text-sm font-semibold text-slate-100">
              {customer.name || customer.email || customer.customerId}
            </h2>
            {customer.email && (
              <p className="text-xs text-slate-400">{customer.email}</p>
            )}
          </div>
          <button
            onClick={onClose}
            className="rounded-full border border-slate-700 px-2 py-1 text-xs text-slate-300 hover:bg-slate-800"
          >
            Close
          </button>
        </div>

        <div className="mt-4 space-y-3 text-xs text-slate-300">
          <div className="grid grid-cols-2 gap-2">
            <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-3">
              <div className="text-[10px] uppercase text-slate-400">
                Current MRR
              </div>
              <div className="mt-1 text-sm font-semibold">
                {customer.currentMrr.toLocaleString()}
              </div>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-3">
              <div className="text-[10px] uppercase text-slate-400">
                Lifetime revenue
              </div>
              <div className="mt-1 text-sm font-semibold">
                {customer.lifetimeRevenue.toLocaleString()}
              </div>
            </div>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-3">
            <div className="text-[10px] uppercase text-slate-400">
              Timeline
            </div>
            <ul className="mt-2 space-y-1">
              <li>
                • First seen:{" "}
                {customer.firstSeenAt
                  ? new Date(customer.firstSeenAt).toLocaleString()
                  : "—"}
              </li>
              <li>
                • Last activity:{" "}
                {customer.lastActivityAt
                  ? new Date(customer.lastActivityAt).toLocaleString()
                  : "—"}
              </li>
              <li>• Status: {customer.status}</li>
              {customer.isHighValue && <li>• Flagged as high value</li>}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

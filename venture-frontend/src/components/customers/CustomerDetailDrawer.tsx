// src/components/customers/CustomerDetailDrawer.tsx
"use client";

import { CustomerDetail } from "@/types/metrics";

interface CustomerDetailDrawerProps {
  customer: CustomerDetail | null;
  currency: string;
}

export function CustomerDetailDrawer({ customer, currency }: CustomerDetailDrawerProps) {
  if (!customer) {
    return (
      <div className="rounded-2xl border border-dashed border-slate-800 bg-slate-900/40 p-4 text-sm text-slate-400">
        Select a customer from the table to see a 360° view.
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 text-sm text-slate-100">
      <div className="mb-3">
        <h3 className="text-base font-semibold text-slate-50">{customer.name}</h3>
        <p className="text-xs text-slate-400">{customer.email}</p>
      </div>

      <div className="grid grid-cols-2 gap-3 text-xs mb-4">
        <div className="space-y-1">
          <p className="text-slate-400">Current MRR</p>
          <p className="font-medium">
            {currency} {customer.currentMrr.toLocaleString()}
          </p>
        </div>
        <div className="space-y-1">
          <p className="text-slate-400">Lifetime revenue</p>
          <p className="font-medium">
            {currency} {customer.lifetimeRevenue.toLocaleString()}
          </p>
        </div>
        <div className="space-y-1">
          <p className="text-slate-400">First seen</p>
          <p className="font-medium">
            {new Date(customer.firstSeenAt).toLocaleDateString()}
          </p>
        </div>
        <div className="space-y-1">
          <p className="text-slate-400">Last activity</p>
          <p className="font-medium">
            {new Date(customer.lastActivityAt).toLocaleDateString()}
          </p>
        </div>
        <div className="space-y-1">
          <p className="text-slate-400">Plan</p>
          <p className="font-medium">{customer.planName}</p>
        </div>
        <div className="space-y-1">
          <p className="text-slate-400">Status</p>
          <p className="font-medium capitalize">{customer.status.replace("_", " ")}</p>
        </div>
      </div>

      <div className="mb-3">
        <p className="text-xs font-medium text-slate-300 mb-1">Segments</p>
        <div className="flex flex-wrap gap-1">
          {customer.segments.map((seg) => (
            <span
              key={seg}
              className="inline-flex items-center rounded-full border border-slate-700 bg-slate-900 px-2 py-0.5 text-[11px] text-slate-200"
            >
              {seg}
            </span>
          ))}
        </div>
      </div>

      <div className="mb-3">
        <p className="text-xs font-medium text-slate-300 mb-1">Recent pages (GA4)</p>
        <ul className="space-y-1 text-xs text-slate-300">
          {customer.recentPages.map((page) => (
            <li key={page}>• {page}</li>
          ))}
        </ul>
      </div>

      {customer.notes && (
        <div className="mt-3">
          <p className="text-xs font-medium text-slate-300 mb-1">Notes</p>
          <p className="text-xs text-slate-300">{customer.notes}</p>
        </div>
      )}
    </div>
  );
}

// src/components/kpis/KpiCard.tsx
"use client";

import clsx from "clsx";

interface KpiCardProps {
  label: string;
  value: string;
  helper?: string;
  tone?: "positive" | "negative" | "neutral";
}

export function KpiCard({ label, value, helper, tone = "neutral" }: KpiCardProps) {
  const helperColor =
    tone === "positive"
      ? "text-emerald-400"
      : tone === "negative"
      ? "text-rose-400"
      : "text-slate-400";

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 shadow-sm transition-transform duration-150 hover:-translate-y-0.5 hover:border-slate-700">
      <div className="text-xs font-medium uppercase tracking-wide text-slate-400">
        {label}
      </div>
      <div className="mt-2 text-2xl font-semibold text-slate-50">{value}</div>
      {helper && (
        <div className={clsx("mt-1 text-xs", helperColor)}>
          {helper}
        </div>
      )}
    </div>
  );
}

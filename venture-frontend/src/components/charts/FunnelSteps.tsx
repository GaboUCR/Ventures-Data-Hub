// src/components/charts/FunnelSteps.tsx
"use client";

import { FunnelStep as FunnelStepType } from "@/types/metrics";

interface FunnelStepsProps {
  steps: FunnelStepType[];
}

/**
 * Simple horizontal bars with width proportional to count.
 */
export function FunnelSteps({ steps }: FunnelStepsProps) {
  if (!steps.length) {
    return (
      <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 text-sm text-slate-400">
        No funnel data available.
      </div>
    );
  }

  const max = Math.max(...steps.map((s) => s.count)) || 1;

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 text-sm">
      <h3 className="mb-3 text-sm font-medium text-slate-100">Acquisition funnel</h3>
      <div className="space-y-3">
        {steps.map((step) => {
          const widthPercent = (step.count / max) * 100;

          return (
            <div key={step.label} className="space-y-1">
              <div className="flex items-center justify-between text-xs text-slate-300">
                <span>{step.label}</span>
                <span className="font-mono text-slate-400">{step.count.toLocaleString()}</span>
              </div>
              <div className="h-2 rounded-full bg-slate-800">
                <div
                  className="h-2 rounded-full bg-emerald-500/80"
                  style={{ width: `${widthPercent}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

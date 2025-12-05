// src/components/charts/CohortHeatmap.tsx
"use client";

import { CohortCell } from "@/types/metrics";

interface CohortHeatmapProps {
  data: CohortCell[];
}

/**
 * Simple cohort heatmap:
 * - Rows = cohorts (e.g. 2025-01)
 * - Columns = month offset (0, 1, 2...)
 * - Cell color = intensity based on retention %
 */
export function CohortHeatmap({ data }: CohortHeatmapProps) {
  if (!data.length) {
    return <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4 text-sm text-slate-400">
      No cohort data available for this period.
    </div>;
  }

  // Get distinct cohorts & months
  const cohorts = Array.from(new Set(data.map((c) => c.cohortLabel))).sort();
  const monthOffsets = Array.from(new Set(data.map((c) => c.monthOffset))).sort((a, b) => a - b);

  const lookup = new Map<string, CohortCell>();
  data.forEach((cell) => {
    lookup.set(`${cell.cohortLabel}-${cell.monthOffset}`, cell);
  });

  const formatCohortLabel = (label: string) => {
    // label "2025-01" -> "Jan 2025"
    const [year, month] = label.split("-");
    const m = parseInt(month, 10);
    const date = new Date(Number(year), m - 1, 1);
    return date.toLocaleDateString(undefined, { month: "short", year: "numeric" });
  };

  const colorForRetention = (percent: number) => {
    // Map 0–100% to a green-ish background
    const clamped = Math.max(0, Math.min(percent, 100));
    const alpha = 0.15 + (clamped / 100) * 0.5; // 0.15–0.65
    return `rgba(16, 185, 129, ${alpha})`; // Tailwind-ish emerald-500
  };

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
      <div className="mb-3 flex items-center justify-between text-xs text-slate-400">
        <span>Cohorts by signup month · retention by month since signup</span>
        <span className="flex items-center gap-2">
          <span className="flex items-center gap-1">
            <span className="h-3 w-4 rounded-sm bg-emerald-500/70" /> High
          </span>
          <span className="flex items-center gap-1">
            <span className="h-3 w-4 rounded-sm bg-emerald-500/10" /> Low
          </span>
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full border-collapse text-xs">
          <thead>
            <tr>
              <th className="px-2 py-1 text-left text-slate-400">Cohort</th>
              {monthOffsets.map((m) => (
                <th key={m} className="px-2 py-1 text-center text-slate-400">
                  M{m}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {cohorts.map((cohort) => (
              <tr key={cohort} className="border-t border-slate-800/60">
                <td className="whitespace-nowrap px-2 py-1 text-slate-300">
                  {formatCohortLabel(cohort)}
                </td>
                {monthOffsets.map((m) => {
                  const cell = lookup.get(`${cohort}-${m}`);
                  if (!cell) {
                    return (
                      <td
                        key={m}
                        className="px-2 py-1 text-center text-slate-500"
                      >
                        –
                      </td>
                    );
                  }
                  return (
                    <td
                      key={m}
                      className="px-2 py-1 text-center"
                    >
                      <div
                        className="flex items-center justify-center rounded-sm px-1 py-1 text-[11px] font-medium"
                        style={{ backgroundColor: colorForRetention(cell.retentionPercent) }}
                      >
                        {cell.retentionPercent.toFixed(0)}%
                      </div>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

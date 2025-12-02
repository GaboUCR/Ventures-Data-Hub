"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { MrrSeriesPoint } from "@/types/metrics";

interface MrrAreaChartProps {
  data: MrrSeriesPoint[];
}

export function MrrAreaChart({ data }: MrrAreaChartProps) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
      <h3 className="mb-2 text-sm font-medium text-slate-100">MRR Movements</h3>
      <ResponsiveContainer width="100%" height={260}>
        <AreaChart data={data}>
          <XAxis dataKey="date" tick={{ fontSize: 10 }} />
          <YAxis tick={{ fontSize: 10 }} />
          <Tooltip />
          <Legend />
          <Area type="monotone" dataKey="new" stackId="1" />
          <Area type="monotone" dataKey="expansion" stackId="1" />
          <Area type="monotone" dataKey="contraction" stackId="1" />
          <Area type="monotone" dataKey="churn" stackId="1" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

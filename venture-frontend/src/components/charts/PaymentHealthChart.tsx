// src/components/charts/PaymentHealthChart.tsx
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
import { PaymentHealthPoint } from "@/types/metrics";

interface PaymentHealthChartProps {
  data: PaymentHealthPoint[];
}

export function PaymentHealthChart({ data }: PaymentHealthChartProps) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
      <h3 className="mb-2 text-sm font-medium text-slate-100">
        Payment outcomes over time
      </h3>
      <ResponsiveContainer width="100%" height={260}>
        <AreaChart data={data}>
          <XAxis dataKey="date" tick={{ fontSize: 10 }} />
          <YAxis tick={{ fontSize: 10 }} />
          <Tooltip />
          <Legend />
          <Area type="monotone" dataKey="success" stackId="1" />
          <Area type="monotone" dataKey="failed" stackId="1" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

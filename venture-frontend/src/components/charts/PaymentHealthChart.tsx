// src/components/charts/PaymentHealthChart.tsx
"use client";

import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
} from "recharts";
import type { PaymentHealthPoint } from "@/types/metrics";

export function PaymentHealthChart({ data }: { data: PaymentHealthPoint[] }) {
  const chartData = data.map((d) => ({
    date: d.date, // could format with new Date(d.date).toLocaleDateString()
    success: d.success,
    failed: d.failed,
  }));

  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData}>
          <XAxis dataKey="date" tick={{ fontSize: 10 }} />
          <YAxis tick={{ fontSize: 10 }} />
          <Tooltip />
          <Legend />
          <Area
            type="monotone"
            dataKey="success"
            stackId="1"
            fillOpacity={0.6}
          />
          <Area
            type="monotone"
            dataKey="failed"
            stackId="1"
            fillOpacity={0.6}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

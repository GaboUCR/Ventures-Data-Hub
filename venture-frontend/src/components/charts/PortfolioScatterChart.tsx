// src/components/charts/PortfolioScatterChart.tsx
"use client";

import {
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
} from "recharts";
import type { PortfolioCompanyRow } from "@/types/metrics";

type Props = {
  companies: PortfolioCompanyRow[];
};

export function PortfolioScatterChart({ companies }: Props) {
  const data = companies.map((c) => ({
    x: c.growthPercent,
    y: c.nrrPercent,
    z: c.arr, // bubble size
    name: c.companyName,
    category: c.category,
  }));

  return (
    <div className="h-72">
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart>
          <XAxis
            type="number"
            dataKey="x"
            name="Growth"
            unit="%"
            tick={{ fontSize: 10 }}
          />
          <YAxis
            type="number"
            dataKey="y"
            name="NRR"
            unit="%"
            tick={{ fontSize: 10 }}
          />
          <Tooltip
            formatter={(value: any, name: any) => {
              if (name === "x") return [`${value.toFixed(1)}%`, "Growth"];
              if (name === "y") return [`${value.toFixed(1)}%`, "NRR"];
              if (name === "z") return [value.toLocaleString(), "ARR"];
              return [value, name];
            }}
            labelFormatter={(label) => `Company: ${label}`}
          />
          <Legend />
          <Scatter data={data} />
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}

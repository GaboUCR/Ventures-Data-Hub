// src/components/charts/PortfolioGrowthRetentionChart.tsx
"use client";

import {
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";
import { PortfolioCompany } from "@/types/metrics";

interface PortfolioGrowthRetentionChartProps {
  companies: PortfolioCompany[];
}

export function PortfolioGrowthRetentionChart({
  companies,
}: PortfolioGrowthRetentionChartProps) {
  const data = companies.map((c) => ({
    name: c.name,
    nrrPercent: c.nrrPercent,
    mrrGrowthRatePercent: c.mrrGrowthRatePercent,
    arr: c.arr,
    stage: c.stage,
  }));

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
      <h3 className="mb-2 text-sm font-medium text-slate-100">
        Growth vs retention
      </h3>
      <p className="mb-3 text-xs text-slate-400">
        Each dot is a company · X = NRR, Y = MRR growth, bubble ≈ ARR
      </p>
      <ResponsiveContainer width="100%" height={280}>
        <ScatterChart>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            type="number"
            dataKey="nrrPercent"
            name="NRR"
            unit="%"
            tick={{ fontSize: 10 }}
          />
          <YAxis
            type="number"
            dataKey="mrrGrowthRatePercent"
            name="MRR growth"
            unit="%"
            tick={{ fontSize: 10 }}
          />
          <Tooltip
            cursor={{ strokeDasharray: "3 3" }}
            formatter={(value: any, name: string) => {
              if (name === "NRR") return [`${value}%`, name];
              if (name === "MRR growth") return [`${value}%`, name];
              if (name === "ARR") return [`$${value.toLocaleString()}`, name];
              return [value, name];
            }}
            labelFormatter={(label: any) =>
              typeof label === "string" ? label : ""
            }
          />
          <Scatter
            name="Companies"
            data={data}
            // Let Recharts pick colors; we don't specify any
          />
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}

"use client";

import { usePortfolioMetrics } from "@/hooks/usePortfolioMetrics";
import { PortfolioTable } from "@/components/portfolio/PortfolioTable";

export default function PortfolioPage() {
  const { data, isLoading, error } = usePortfolioMetrics();

  if (isLoading) return <div className="p-6">Loading portfolio…</div>;
  if (error || !data) return <div className="p-6 text-red-400">Failed to load portfolio.</div>;

  return (
    <main className="px-3 py-6 sm:px-4 md:px-6 lg:px-8 md:py-8">
      <div className="mx-auto w-full space-y-6">
        {/* Top header bar */}
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div className="space-y-1">
            <h1 className="text-2xl font-semibold text-[#f4f4f4]">Portfolio</h1>
            <p className="text-sm text-[#a8a8a8]">
              {data.companyCount} companies · Total ARR ${data.totalArr.toLocaleString()}
            </p>
          </div>

          {/* Right controls (search still visual only for now) */}
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
            <input
              type="text"
              placeholder="Search companies"
              className="w-full rounded-md border border-[#393939] bg-[#262626] px-3 py-1.5 text-sm text-[#f4f4f4] placeholder:text-[#6f6f6f] focus:outline-none focus:ring-2 focus:ring-[#0f62fe] sm:w-64"
            />
            <button className="inline-flex items-center justify-center gap-2 rounded-md border border-[#393939] bg-[#262626] px-3 py-1.5 text-xs text-[#f4f4f4]">
              <span className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-[#393939] text-[11px]">
                6
              </span>
              Columns
            </button>
          </div>
        </div>

        {/* Data grid */}
        <PortfolioTable data={data.companies} />
      </div>
    </main>
  );
}

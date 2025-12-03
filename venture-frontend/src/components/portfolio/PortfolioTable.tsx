"use client";

import { ColumnDef } from "@tanstack/react-table";
import Link from "next/link";
import { DataTable } from "@/components/table/DataTable";
import { PortfolioCompanyRow } from "@/types/metrics";

const columns: ColumnDef<PortfolioCompanyRow>[] = [
  {
    accessorKey: "companyName",
    header: "Company",
    cell: ({ row }) => {
      const company = row.original;
      return (
        <Link
          href={`/companies/${company.companyId}/overview`}
          className="text-[#78a9ff] underline-offset-2 hover:underline"
        >
          {company.companyName}
        </Link>
      );
    },
  },
  {
    accessorKey: "arr",
    header: "ARR",
    cell: ({ row }) => {
      const value = row.original.arr;
      return <>${value.toLocaleString()}</>;
    },
  },
  {
    accessorKey: "growthRatePercent",
    header: "Growth",
    cell: ({ row }) => {
      const value = row.original.growthRatePercent;
      return <>{value.toFixed(1)}%</>;
    },
  },
  {
    accessorKey: "nrrPercent",
    header: "NRR",
    cell: ({ row }) => {
      const value = row.original.nrrPercent;
      return <>{value.toFixed(1)}%</>;
    },
  },
  {
    accessorKey: "churnRatePercent",
    header: "Churn",
    cell: ({ row }) => {
      const value = row.original.churnRatePercent;
      return <>{value.toFixed(1)}%</>;
    },
  },
  {
    accessorKey: "healthScore",
    header: "Health",
    cell: ({ row }) => {
      const value = row.original.healthScore;
      return (
        <span className="inline-flex items-center rounded-full bg-[#24a148] px-3 py-0.5 text-xs font-medium text-white">
          {value}
        </span>
      );
    },
    sortDescFirst: true,
  },
];

export function PortfolioTable({ data }: { data: PortfolioCompanyRow[] }) {
  return (
    <DataTable
      columns={columns}
      data={data}
      pageSize={10}
      fontSizePx={25}
    />
  );
}

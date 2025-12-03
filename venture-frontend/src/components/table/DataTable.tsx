"use client";

import * as React from "react";
import {
  ColumnDef,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  getPaginationRowModel,
  SortingState,
  PaginationState,
  useReactTable,
} from "@tanstack/react-table";

interface DataTableProps<TData, TValue> {
  columns: ColumnDef<TData, TValue>[];
  data: TData[];
  pageSize?: number;
  fontSizePx?: number;
}

export function DataTable<TData, TValue>({
  columns,
  data,
  pageSize = 10,
  fontSizePx = 13,
}: DataTableProps<TData, TValue>) {
  const [sorting, setSorting] = React.useState<SortingState>([]);
  const [pagination, setPagination] = React.useState<PaginationState>({
    pageIndex: 0,
    pageSize,
  });

  const table = useReactTable({
    data,
    columns,
    state: { sorting, pagination },
    onSortingChange: setSorting,
    onPaginationChange: setPagination,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
  });

  const totalRows = data.length;
  const { pageIndex } = table.getState().pagination;
  const start = pageIndex * pageSize + 1;
  const end = Math.min(start + pageSize - 1, totalRows);

  return (
    <div className="overflow-x-auto rounded-lg border border-[#393939] bg-[#262626]">
      <table className="min-w-[640px] w-full">
        <thead className="bg-[#393939] text-left text-[#c6c6c6]">
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map((header) => {
                if (header.isPlaceholder) return null;
                const sorted = header.column.getIsSorted();

                return (
                  <th key={header.id} className="px-5 py-3 font-normal">
                    <button
                      type="button"
                      onClick={header.column.getToggleSortingHandler()}
                      style={{ fontSize: `${fontSizePx}px`, lineHeight: 1.3 }}
                      className="flex items-center gap-1 text-left bg-transparent border-none p-0 text-inherit"
                    >
                      {flexRender(
                        header.column.columnDef.header,
                        header.getContext()
                      )}
                      {sorted === "asc" && <span>▲</span>}
                      {sorted === "desc" && <span>▼</span>}
                    </button>
                  </th>
                );
              })}
            </tr>
          ))}
        </thead>

        <tbody style={{ fontSize: `${fontSizePx}px` }}>
          {table.getRowModel().rows.map((row, idx) => (
            <tr
              key={row.id}
              className={`border-b border-[#393939] hover:bg-[#343434] ${
                idx === table.getRowModel().rows.length - 1 ? "border-b-0" : ""
              }`}
            >
              {row.getVisibleCells().map((cell) => (
                <td key={cell.id} className="px-5 py-3 align-middle">
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}

          {table.getRowModel().rows.length === 0 && (
            <tr>
              <td
                colSpan={columns.length}
                className="px-5 py-6 text-center text-xs text-[#a8a8a8]"
              >
                No results
              </td>
            </tr>
          )}
        </tbody>
      </table>

      {/* footer now also uses fontSizePx */}
      <div
        className="flex flex-col items-start justify-between gap-2 border-t border-[#393939] bg-[#262626] px-5 py-2 sm:flex-row sm:items-center"
        style={{ fontSize: `${fontSizePx/2}px`, color: "#a8a8a8" }}
      >
        <div>
          Items per page:{" "}
          <span className="font-medium text-[#f4f4f4]">{pageSize}</span>
        </div>
        <div className="flex items-center gap-3">
          <span>
            {totalRows === 0
              ? "0 items"
              : `${start}–${end} of ${totalRows} items`}
          </span>
          <div className="flex gap-1">
            <button
              type="button"
              onClick={() => table.previousPage()}
              disabled={!table.getCanPreviousPage()}
              className="rounded border border-[#525252] px-2 py-0.5 disabled:opacity-40"
            >
              Prev
            </button>
            <button
              type="button"
              onClick={() => table.nextPage()}
              disabled={!table.getCanNextPage()}
              className="rounded border border-[#525252] px-2 py-0.5 disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

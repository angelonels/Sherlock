"use client";

import type { DatasetColumn, DatasetQualityIssue } from "@/lib/types";
import {
  flexRender,
  getCoreRowModel,
  useReactTable,
  type ColumnDef,
} from "@tanstack/react-table";

function DataTable<TData>({
  data,
  columns,
  minWidth = "40rem",
}: {
  data: TData[];
  columns: ColumnDef<TData>[];
  minWidth?: string;
}) {
  // TanStack Table intentionally exposes mutable helpers; React Compiler skips this component.
  // eslint-disable-next-line react-hooks/incompatible-library
  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  return (
    <div className="overflow-x-auto border border-[#d9cdbf] bg-[#fffaf7]">
      <table className="w-full text-left text-sm" style={{ minWidth }}>
        <thead>
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <th key={header.id} className="border-b border-[#d9cdbf] px-3 py-2 font-semibold text-[#51473f]">
                  {header.isPlaceholder ? null : flexRender(header.column.columnDef.header, header.getContext())}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row) => (
            <tr key={row.id} className="border-b border-[#eee4d8]">
              {row.getVisibleCells().map((cell) => (
                <td key={cell.id} className="max-w-72 truncate px-3 py-2 text-[#655c52]">
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function DatasetPreviewTab({
  rows,
  onLoadNext,
  hasNextPage,
  isLoadingNext = false,
}: {
  rows: Record<string, unknown>[];
  onLoadNext?: () => void;
  hasNextPage?: boolean;
  isLoadingNext?: boolean;
}) {
  const columns = rows[0] ? Object.keys(rows[0]) : [];
  const tableColumns: ColumnDef<Record<string, unknown>>[] = columns.map((column) => ({
    accessorKey: column,
    header: column,
    cell: ({ getValue }) => String(getValue() ?? ""),
  }));
  return (
    <section>
      <DataTable data={rows} columns={tableColumns} />
      {hasNextPage ? (
        <button type="button" onClick={onLoadNext} disabled={isLoadingNext} className="m-3 border border-[#d9cdbf] px-3 py-2 text-sm font-semibold disabled:opacity-60">
          {isLoadingNext ? "Loading rows" : "Load next rows"}
        </button>
      ) : null}
    </section>
  );
}

export function DatasetSchemaTab({ columns }: { columns: DatasetColumn[] }) {
  const tableColumns: ColumnDef<DatasetColumn>[] = [
    { accessorKey: "column_name", header: "Column" },
    { accessorKey: "semantic_type", header: "Semantic type" },
    { accessorKey: "postgres_type", header: "Postgres type" },
    { accessorKey: "nullable_count", header: "Missing" },
  ];
  return (
    <DataTable data={columns} columns={tableColumns} minWidth="34rem" />
  );
}

export function DatasetQualityTab({ issues }: { issues: DatasetQualityIssue[] }) {
  const tableColumns: ColumnDef<DatasetQualityIssue>[] = [
    { accessorKey: "severity", header: "Severity" },
    { accessorKey: "title", header: "Issue" },
    { accessorKey: "description", header: "Description" },
  ];
  return (
    <section>
      {issues.length === 0 ? <p className="border border-[#d9cdbf] bg-[#fffaf7] px-3 py-3 text-sm text-[#655c52]">No quality warnings.</p> : null}
      {issues.length ? <DataTable data={issues} columns={tableColumns} minWidth="42rem" /> : null}
    </section>
  );
}

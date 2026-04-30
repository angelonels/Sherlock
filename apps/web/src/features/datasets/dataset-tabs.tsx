"use client";

import type { DatasetColumn, DatasetQualityIssue } from "@/lib/types";

export function DatasetPreviewTab({
  rows,
  onLoadNext,
  hasNextPage,
}: {
  rows: Record<string, unknown>[];
  onLoadNext?: () => void;
  hasNextPage?: boolean;
}) {
  const columns = rows[0] ? Object.keys(rows[0]) : [];
  return (
    <section className="overflow-x-auto border border-[#d9cdbf] bg-[#fffaf7]">
      <table className="w-full min-w-[40rem] text-left text-sm">
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column} className="border-b border-[#d9cdbf] px-3 py-2 font-semibold text-[#51473f]">
                {column}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index} className="border-b border-[#eee4d8]">
              {columns.map((column) => (
                <td key={column} className="max-w-72 truncate px-3 py-2 text-[#655c52]">
                  {String(row[column] ?? "")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {hasNextPage ? (
        <button type="button" onClick={onLoadNext} className="m-3 border border-[#d9cdbf] px-3 py-2 text-sm font-semibold">
          Load next rows
        </button>
      ) : null}
    </section>
  );
}

export function DatasetSchemaTab({ columns }: { columns: DatasetColumn[] }) {
  return (
    <section className="grid gap-2">
      {columns.map((column) => (
        <div key={column.id} className="border border-[#d9cdbf] bg-[#fffaf7] px-3 py-3 text-sm">
          <div className="font-semibold text-[#51473f]">{column.column_name}</div>
          <div className="mt-1 text-[#655c52]">
            {column.semantic_type} · {column.postgres_type} · {column.nullable_count} missing
          </div>
        </div>
      ))}
    </section>
  );
}

export function DatasetQualityTab({ issues }: { issues: DatasetQualityIssue[] }) {
  return (
    <section className="grid gap-2">
      {issues.length === 0 ? <p className="border border-[#d9cdbf] bg-[#fffaf7] px-3 py-3 text-sm text-[#655c52]">No quality warnings.</p> : null}
      {issues.map((issue) => (
        <div key={issue.id} className="border border-[#d9cdbf] bg-[#fffaf7] px-3 py-3 text-sm">
          <div className="font-semibold text-[#51473f]">{issue.title}</div>
          <div className="mt-1 text-[#655c52]">{issue.description}</div>
        </div>
      ))}
    </section>
  );
}

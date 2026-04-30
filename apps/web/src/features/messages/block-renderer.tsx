"use client";

import type { AssistantBlock } from "@/lib/types";

type BlockMap = Extract<AssistantBlock, { type: string }>;

export function BlockRenderer({ blocks }: { blocks: AssistantBlock[] | null | undefined }) {
  if (!blocks?.length) {
    return null;
  }
  return (
    <div className="mt-3 space-y-3">
      {blocks.map((block, index) => {
        if (block.type === "markdown") {
          const markdown = block as Extract<BlockMap, { type: "markdown" }>;
          return <p key={index} className="text-sm leading-6 text-[#51473f]">{markdown.content}</p>;
        }
        if (block.type === "plan") {
          const plan = block as Extract<BlockMap, { type: "plan" }>;
          return (
            <ol key={index} className="list-decimal space-y-1 pl-5 text-sm text-[#655c52]">
              {plan.steps.map((step) => <li key={step}>{step}</li>)}
            </ol>
          );
        }
        if (block.type === "kpi") {
          const kpi = block as Extract<BlockMap, { type: "kpi" }>;
          return (
            <div key={index} className="border border-[#d9cdbf] bg-[#fbf7f1] p-3">
              <div className="text-xs uppercase tracking-[0.14em] text-[#8f6a4e]">{kpi.label}</div>
              <div className="mt-1 text-2xl font-semibold text-[#241f1a]">{kpi.value}</div>
              {kpi.caption ? <div className="mt-1 text-xs text-[#655c52]">{kpi.caption}</div> : null}
            </div>
          );
        }
        if (block.type === "table") {
          const table = block as Extract<BlockMap, { type: "table" }>;
          return (
            <div key={index} className="overflow-x-auto border border-[#d9cdbf] bg-[#fbf7f1]">
              <table className="w-full min-w-[28rem] text-left text-sm">
                <thead>
                  <tr>{table.columns.map((column) => <th key={column} className="border-b border-[#d9cdbf] px-3 py-2">{column}</th>)}</tr>
                </thead>
                <tbody>
                  {table.rows.map((row, rowIndex) => (
                    <tr key={rowIndex}>
                      {table.columns.map((column) => <td key={column} className="border-b border-[#eee4d8] px-3 py-2">{String(row[column] ?? "")}</td>)}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          );
        }
        if (block.type === "quality_note") {
          const note = block as Extract<BlockMap, { type: "quality_note" }>;
          return <div key={index} className="border border-[#d9cdbf] bg-[#fbf7f1] p-3 text-sm"><strong>{note.title}</strong><p className="mt-1 text-[#655c52]">{note.description}</p></div>;
        }
        if (block.type === "suggestions") {
          const suggestions = block as Extract<BlockMap, { type: "suggestions" }>;
          return <div key={index} className="flex flex-wrap gap-2">{suggestions.suggestions.map((suggestion) => <span key={suggestion} className="border border-[#d9cdbf] bg-[#fbf7f1] px-2 py-1 text-xs">{suggestion}</span>)}</div>;
        }
        if (block.type === "error") {
          const error = block as Extract<BlockMap, { type: "error" }>;
          return <div key={index} className="border border-[#b84b3c] bg-[#fff2ef] p-3 text-sm text-[#7d2f26]">{error.title}: {error.message}</div>;
        }
        return <div key={index} className="border border-[#d9cdbf] bg-[#fbf7f1] p-3 text-sm text-[#655c52]">Unsupported response block.</div>;
      })}
    </div>
  );
}

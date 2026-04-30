import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { BlockRenderer } from "@/features/messages/block-renderer";

describe("BlockRenderer", () => {
  it("renders production assistant block types", () => {
    render(
      <BlockRenderer
        blocks={[
          { type: "markdown", content: "Dataset summary" },
          { type: "plan", steps: ["Inspect schema"] },
          { type: "kpi", label: "Rows", value: 42 },
          { type: "table", columns: ["name"], rows: [{ name: "Aman" }] },
          { type: "quality_note", severity: "warning", title: "Missing values", description: "Some rows have blanks." },
          { type: "suggestions", suggestions: ["Show row count"] },
          { type: "error", title: "Query failed", message: "Try a narrower question." },
        ]}
      />,
    );

    expect(screen.getByText("Dataset summary")).toBeVisible();
    expect(screen.getByText("Inspect schema")).toBeVisible();
    expect(screen.getByText("Rows")).toBeVisible();
    expect(screen.getByText("Aman")).toBeVisible();
    expect(screen.getByText("Missing values")).toBeVisible();
    expect(screen.getByText("Show row count")).toBeVisible();
    expect(screen.getByText(/Query failed/i)).toBeVisible();
  });

  it("renders unknown blocks as a safe fallback", () => {
    render(<BlockRenderer blocks={[{ type: "unknown_block", payload: [] }]} />);

    expect(screen.getByText("Unsupported response block.")).toBeVisible();
  });
});

import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { DatasetPreviewTab, DatasetQualityTab, DatasetSchemaTab } from "@/features/datasets/dataset-tabs";

describe("dataset inspector tabs", () => {
  it("renders preview rows and requests the next page", () => {
    const onLoadNext = vi.fn();
    render(
      <DatasetPreviewTab
        rows={[{ _sherlock_row_id: 1, region: "West", revenue: 100 }]}
        hasNextPage
        onLoadNext={onLoadNext}
      />,
    );

    expect(screen.getByRole("cell", { name: "West" })).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Load next rows" }));
    expect(onLoadNext).toHaveBeenCalledOnce();
  });

  it("disables pagination while the next page is loading", () => {
    render(<DatasetPreviewTab rows={[{ region: "West" }]} hasNextPage isLoadingNext />);

    expect(screen.getByRole("button", { name: "Loading rows" })).toBeDisabled();
  });

  it("renders schema and empty quality states", () => {
    const { rerender } = render(
      <DatasetSchemaTab
        columns={[
          {
            id: "column_1",
            column_index: 0,
            column_name: "revenue",
            original_column_name: "Revenue",
            postgres_type: "DOUBLE PRECISION",
            pandas_type: "float64",
            semantic_type: "currency",
            nullable_count: 1,
            nullable_ratio: 0.1,
            distinct_count: 9,
            sample_values: [100],
            warning_flags: [],
          },
        ]}
      />,
    );

    expect(screen.getByRole("cell", { name: "revenue" })).toBeVisible();
    rerender(<DatasetQualityTab issues={[]} />);
    expect(screen.getByText("No quality warnings.")).toBeVisible();
  });
});

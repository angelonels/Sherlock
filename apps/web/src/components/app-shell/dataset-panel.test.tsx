import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactElement } from "react";
import { describe, expect, it, vi } from "vitest";

import { DatasetPanel } from "@/components/app-shell/app-shell";
import type { ApiClient } from "@/lib/api-client";

function renderWithQueryClient(ui: ReactElement) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
}

describe("DatasetPanel", () => {
  it("shows loading, retries a failed query, and appends preview rows", async () => {
    const getDatasetPreview = vi
      .fn()
      .mockRejectedValueOnce(new Error("Dataset context failed."))
      .mockResolvedValueOnce({
        data: [{ _sherlock_row_id: 1, region: "West" }],
        pagination: { next_cursor: "1" },
      })
      .mockResolvedValueOnce({
        data: [{ _sherlock_row_id: 2, region: "East" }],
        pagination: { next_cursor: null },
      });
    const apiClient = {
      getDatasetPreview,
      getDatasetColumns: vi.fn(async () => ({ data: [], pagination: { next_cursor: null } })),
      getDatasetQualityIssues: vi.fn(async () => ({ data: [], pagination: { next_cursor: null } })),
    } as unknown as ApiClient;

    renderWithQueryClient(<DatasetPanel apiClient={apiClient} datasetId="dataset_123" />);

    expect(screen.getByText("Loading dataset context")).toBeVisible();
    expect(await screen.findByRole("alert")).toHaveTextContent("Dataset context failed.");
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));

    expect(await screen.findByRole("cell", { name: "West" })).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Load next rows" }));
    await waitFor(() => expect(getDatasetPreview).toHaveBeenCalledWith("dataset_123", "1"));
    expect(await screen.findByRole("cell", { name: "East" })).toBeVisible();
  });
});

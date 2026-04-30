import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { UploadSessionStep } from "@/features/upload/upload-session-step";
import type { ApiClient } from "@/lib/api-client";
import type { UploadSession } from "@/lib/types";

const routerMocks = vi.hoisted(() => ({
  push: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => routerMocks,
}));

function uploadSession(overrides: Partial<UploadSession> = {}): UploadSession {
  return {
    id: "upload_123",
    original_filename: "sales.csv",
    file_extension: "csv",
    file_size_bytes: 24,
    status: "inspected",
    sheet_names: null,
    selected_sheet_name: null,
    recommended_sheet_name: null,
    preview_rows: [{ name: "Aman", revenue: "100" }],
    detected_columns: [
      { original_name: "name", clean_name: "name", inferred_type: "text" },
      { original_name: "revenue", clean_name: "revenue", inferred_type: "text" },
    ],
    warnings: [{ code: "FORMULA_LIKE_VALUES_DETECTED", message: "Formula-like values detected.", severity: "warning" }],
    expires_at: "2026-05-03T00:00:00Z",
    ...overrides,
  };
}

function client(overrides: Partial<ApiClient> = {}): ApiClient {
  return {
    createUploadSession: vi.fn(async () => uploadSession()),
    updateUploadSessionSheet: vi.fn(async () =>
      uploadSession({
        original_filename: "orders.xlsx",
        file_extension: "xlsx",
        sheet_names: ["Orders", "Returns"],
        selected_sheet_name: "Returns",
        recommended_sheet_name: "Orders",
        preview_rows: [{ Reason: "Damaged", Count: 2 }],
        detected_columns: [
          { original_name: "Reason", clean_name: "reason", inferred_type: "text" },
          { original_name: "Count", clean_name: "count", inferred_type: "numeric" },
        ],
        warnings: [],
      }),
    ),
    deleteUploadSession: vi.fn(async () => undefined),
    ...overrides,
  } as unknown as ApiClient;
}

describe("UploadSessionStep", () => {
  it("uploads a mocked file and renders preview, detected columns, and warnings", async () => {
    const apiClient = client();
    render(<UploadSessionStep apiClient={apiClient} />);

    fireEvent.change(screen.getByLabelText(/Upload CSV or XLSX file/i), {
      target: { files: [new File(["name,revenue\nAman,100\n"], "sales.csv", { type: "text/csv" })] },
    });

    await waitFor(() => expect(apiClient.createUploadSession).toHaveBeenCalled());
    expect(await screen.findByText("sales.csv")).toBeVisible();
    expect(screen.getByText("Aman")).toBeVisible();
    expect(screen.getByText("name · text")).toBeVisible();
    expect(screen.getByText("Formula-like values detected.")).toBeVisible();
  });

  it("renders sheet selector for multi-sheet XLSX and updates preview", async () => {
    const apiClient = client({
      createUploadSession: vi.fn(async () =>
        uploadSession({
          original_filename: "orders.xlsx",
          file_extension: "xlsx",
          sheet_names: ["Orders", "Returns"],
          selected_sheet_name: null,
          recommended_sheet_name: "Orders",
        }),
      ),
    } as Partial<ApiClient>);
    render(<UploadSessionStep apiClient={apiClient} />);

    fireEvent.change(screen.getByLabelText(/Upload CSV or XLSX file/i), {
      target: { files: [new File(["xlsx"], "orders.xlsx")] },
    });

    const selector = await screen.findByLabelText("Sheet");
    fireEvent.change(selector, { target: { value: "Returns" } });

    await waitFor(() => expect(apiClient.updateUploadSessionSheet).toHaveBeenCalledWith("upload_123", "Returns"));
    expect(await screen.findByText("Damaged")).toBeVisible();
  });

  it("cancels an upload session", async () => {
    const apiClient = client();
    render(<UploadSessionStep apiClient={apiClient} />);

    fireEvent.change(screen.getByLabelText(/Upload CSV or XLSX file/i), {
      target: { files: [new File(["name,revenue\nAman,100\n"], "sales.csv")] },
    });

    fireEvent.click(await screen.findByRole("button", { name: /Cancel/i }));

    await waitFor(() => expect(apiClient.deleteUploadSession).toHaveBeenCalledWith("upload_123"));
    await waitFor(() => expect(screen.queryByText("sales.csv")).not.toBeInTheDocument());
  });
});

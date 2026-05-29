import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactElement } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { UploadSessionStep } from "@/features/upload/upload-session-step";
import type { ApiClient } from "@/lib/api-client";
import type { Dataset, DatasetColumn, DatasetQualityIssue, UploadSession } from "@/lib/types";

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

function dataset(overrides: Partial<Dataset> = {}): Dataset {
  return {
    id: "dataset_123",
    name: "Sales",
    status: "ready",
    source_file_type: "csv",
    selected_sheet_name: null,
    original_filename: "sales.csv",
    row_count: 2,
    original_row_count: 3,
    duplicate_rows_removed: 1,
    column_count: 2,
    total_missing_values: 0,
    quality_status: "good",
    quality_score: 98,
    ingestion_error: null,
    created_at: "2026-05-03T00:00:00Z",
    ...overrides,
  };
}

function client(overrides: Partial<ApiClient> = {}): ApiClient {
  return {
    createUploadSession: vi.fn(async () => uploadSession()),
    getUploadSession: vi.fn(async () => uploadSession()),
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
    createDataset: vi.fn(async () => dataset()),
    getDataset: vi.fn(async () => dataset()),
    getDatasetPreview: vi.fn(async () => ({
      data: [{ name: "Aman", revenue: 100 }],
      pagination: { next_cursor: null },
    })),
    getDatasetColumns: vi.fn(async () => ({
      data: [
        {
          id: "column_1",
          column_index: 0,
          column_name: "name",
          original_column_name: "name",
          postgres_type: "text",
          pandas_type: "object",
          semantic_type: "text",
          nullable_count: 0,
          nullable_ratio: 0,
          distinct_count: 1,
          sample_values: ["Aman"],
          warning_flags: [],
        } satisfies DatasetColumn,
      ],
      pagination: { next_cursor: null },
    })),
    getDatasetQualityIssues: vi.fn(async () => ({
      data: [
        {
          id: "issue_1",
          issue_type: "duplicate_rows_removed",
          severity: "info",
          title: "Duplicate rows removed",
          description: "1 exact duplicate row was removed.",
          affected_row_count: 1,
          affected_ratio: 0.33,
          sample_values: null,
        } satisfies DatasetQualityIssue,
      ],
      pagination: { next_cursor: null },
    })),
    createChat: vi.fn(async () => ({
      id: "chat_123",
      dataset_id: "dataset_123",
      title: "Sales",
      created_at: "2026-05-03T00:00:00Z",
      updated_at: "2026-05-03T00:00:00Z",
    })),
    ...overrides,
  } as unknown as ApiClient;
}

function renderWithQueryClient(ui: ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
}

describe("UploadSessionStep", () => {
  beforeEach(() => {
    sessionStorage.clear();
    routerMocks.push.mockClear();
  });

  it("uploads a mocked file and renders preview, detected columns, and warnings", async () => {
    const apiClient = client();
    renderWithQueryClient(<UploadSessionStep apiClient={apiClient} />);

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
    renderWithQueryClient(<UploadSessionStep apiClient={apiClient} />);

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
    renderWithQueryClient(<UploadSessionStep apiClient={apiClient} />);

    fireEvent.change(screen.getByLabelText(/Upload CSV or XLSX file/i), {
      target: { files: [new File(["name,revenue\nAman,100\n"], "sales.csv")] },
    });

    fireEvent.click(await screen.findByRole("button", { name: /Cancel/i }));

    await waitFor(() => expect(apiClient.deleteUploadSession).toHaveBeenCalledWith("upload_123"));
    await waitFor(() => expect(screen.queryByText("sales.csv")).not.toBeInTheDocument());
  });

  it("creates a dataset, reviews evidence, and starts investigation explicitly", async () => {
    const apiClient = client();
    renderWithQueryClient(<UploadSessionStep apiClient={apiClient} />);

    fireEvent.change(screen.getByLabelText(/Upload CSV or XLSX file/i), {
      target: { files: [new File(["name,revenue\nAman,100\n"], "sales.csv", { type: "text/csv" })] },
    });

    await screen.findByDisplayValue("sales");
    fireEvent.change(screen.getByLabelText("Dataset name"), { target: { value: "Sales" } });
    fireEvent.click(screen.getByRole("button", { name: /Create Dataset/i }));

    await waitFor(() =>
      expect(apiClient.createDataset).toHaveBeenCalledWith({
        upload_session_id: "upload_123",
        name: "Sales",
        selected_sheet_name: null,
      }),
    );
    expect(await screen.findByText("Dataset review")).toBeVisible();
    expect(screen.getByText(/2 rows/i)).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "quality" }));
    expect(screen.getByText("Duplicate rows removed")).toBeVisible();

    fireEvent.click(screen.getByRole("button", { name: /Start Investigation/i }));

    await waitFor(() => expect(apiClient.createChat).toHaveBeenCalledWith("dataset_123"));
    expect(routerMocks.push).toHaveBeenCalledWith("/app/chat/chat_123");
  });

  it("restores a durable upload and ready dataset after refresh", async () => {
    sessionStorage.setItem("sherlock.uploadSessionId", "upload_123");
    sessionStorage.setItem("sherlock.datasetId", "dataset_123");
    const apiClient = client();

    renderWithQueryClient(<UploadSessionStep apiClient={apiClient} />);

    await waitFor(() => expect(apiClient.getUploadSession).toHaveBeenCalledWith("upload_123"));
    await waitFor(() => expect(apiClient.getDataset).toHaveBeenCalledWith("dataset_123"));
    expect(await screen.findByText("Dataset review")).toBeVisible();
    expect(screen.getByText("sales.csv")).toBeVisible();
  });

  it("shows a recoverable inline error when starting an investigation fails", async () => {
    const apiClient = client({
      createChat: vi.fn(async () => {
        throw new Error("Investigation already exists.");
      }),
    });
    sessionStorage.setItem("sherlock.uploadSessionId", "upload_123");
    sessionStorage.setItem("sherlock.datasetId", "dataset_123");

    renderWithQueryClient(<UploadSessionStep apiClient={apiClient} />);

    fireEvent.click(await screen.findByRole("button", { name: /Start Investigation/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Investigation already exists.");
    expect(routerMocks.push).not.toHaveBeenCalled();
  });
});

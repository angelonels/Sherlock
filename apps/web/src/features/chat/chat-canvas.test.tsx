import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactElement } from "react";
import { describe, expect, it, vi } from "vitest";

import { ChatCanvas } from "@/features/chat/chat-canvas";
import type { ApiClient } from "@/lib/api-client";
import type { AnalysisRun, Message } from "@/lib/types";

const chat = {
  id: "chat_123",
  dataset_id: "dataset_123",
  title: "Sales investigation",
  created_at: "2026-06-10T00:00:00Z",
  updated_at: "2026-06-10T00:00:00Z",
};
const dataset = {
  id: "dataset_123",
  name: "Sales",
  status: "locked",
  source_file_type: "csv",
  selected_sheet_name: null,
  original_filename: "sales.csv",
  row_count: 2,
  original_row_count: 2,
  duplicate_rows_removed: 0,
  column_count: 1,
  total_missing_values: 0,
  quality_status: "good",
  quality_score: 100,
  ingestion_error: null,
  created_at: "2026-06-10T00:00:00Z",
};
const userMessage: Message = {
  id: "message_user",
  chat_session_id: "chat_123",
  message_index: 1,
  role: "user",
  content: "What is total revenue?",
  blocks: null,
  created_at: "2026-06-10T00:00:00Z",
};
const assistantMessage: Message = {
  id: "message_assistant",
  chat_session_id: "chat_123",
  message_index: 2,
  role: "assistant",
  content: "Revenue is 100.",
  blocks: [{ type: "markdown", content: "Revenue is **100**." }],
  created_at: "2026-06-10T00:00:01Z",
};

function client(overrides: Partial<ApiClient> = {}): ApiClient {
  return {
    getChat: vi.fn(async () => chat),
    getMessages: vi.fn(async () => ({ data: [], pagination: { next_cursor: null } })),
    getDataset: vi.fn(async () => dataset),
    getDatasetColumns: vi.fn(async () => ({ data: [], pagination: { next_cursor: null } })),
    getDatasetQualityIssues: vi.fn(async () => ({ data: [], pagination: { next_cursor: null } })),
    sendMessage: vi.fn(async () => ({ message: userMessage, analysis_run_id: "run_123" })),
    getAnalysisRun: vi.fn(async () => ({
      id: "run_123",
      chat_session_id: "chat_123",
      user_message_id: "message_user",
      assistant_message_id: "message_assistant",
      status: "success",
      current_stage: "completed",
      error_code: null,
      error_message: null,
      assistant_message: assistantMessage,
      created_at: "2026-06-10T00:00:00Z",
    } satisfies AnalysisRun)),
    ...overrides,
  } as unknown as ApiClient;
}

function renderWithQueryClient(ui: ReactElement) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
}

describe("ChatCanvas", () => {
  it("loads durable chat context and reports the active dataset", async () => {
    const onDatasetContext = vi.fn();
    renderWithQueryClient(<ChatCanvas apiClient={client()} chatId="chat_123" onDatasetContext={onDatasetContext} />);

    expect(await screen.findByRole("heading", { name: "Sales investigation" })).toBeVisible();
    expect(screen.getByText(/2 rows/i)).toBeVisible();
    expect(onDatasetContext).toHaveBeenCalledWith("dataset_123");
  });

  it("sends on Enter, polls, and renders the persisted assistant response", async () => {
    const apiClient = client();
    renderWithQueryClient(<ChatCanvas apiClient={apiClient} chatId="chat_123" />);
    const composer = await screen.findByPlaceholderText(/Ask about rows/i);

    fireEvent.change(composer, { target: { value: "What is total revenue?" } });
    fireEvent.keyDown(composer, { key: "Enter", shiftKey: false });

    await waitFor(() => expect(apiClient.sendMessage).toHaveBeenCalled());
    expect(await screen.findByText(/Revenue is/)).toBeVisible();
    expect(screen.queryByLabelText("Analysis status")).not.toBeInTheDocument();
  });

  it("shows a safe failed-run error and allows another question", async () => {
    const apiClient = client({
      getAnalysisRun: vi.fn(async () => ({
        id: "run_123",
        chat_session_id: "chat_123",
        user_message_id: "message_user",
        assistant_message_id: null,
        status: "failed",
        current_stage: "failed",
        error_code: "ANALYSIS_WORKFLOW_FAILED",
        error_message: "Sherlock could not complete this analysis. Try a narrower question.",
        assistant_message: null,
        created_at: "2026-06-10T00:00:00Z",
      })),
    });
    renderWithQueryClient(<ChatCanvas apiClient={apiClient} chatId="chat_123" />);
    const composer = await screen.findByPlaceholderText(/Ask about rows/i);

    fireEvent.change(composer, { target: { value: "Break it" } });
    fireEvent.keyDown(composer, { key: "Enter" });

    expect(await screen.findByRole("alert")).toHaveTextContent("Try a narrower question");
    fireEvent.change(composer, { target: { value: "Try again" } });
    expect(screen.getByRole("button", { name: "Send message" })).toBeEnabled();
  });

  it("offers a retry after chat context loading fails", async () => {
    const getChat = vi.fn().mockRejectedValueOnce(new Error("Chat could not load.")).mockResolvedValue(chat);
    const apiClient = client({ getChat });
    renderWithQueryClient(<ChatCanvas apiClient={apiClient} chatId="chat_123" />);

    expect(await screen.findByRole("alert")).toHaveTextContent("Chat could not load.");
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));

    expect(await screen.findByRole("heading", { name: "Sales investigation" })).toBeVisible();
    expect(getChat).toHaveBeenCalledTimes(2);
  });
});

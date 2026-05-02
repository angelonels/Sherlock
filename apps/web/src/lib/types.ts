export type DataEnvelope<T> = {
  data: T;
};

export type Pagination = {
  next_cursor: string | null;
};

export type ListEnvelope<T> = {
  data: T[];
  pagination: Pagination;
};

export type ErrorEnvelope = {
  error: {
    code: string;
    message: string;
    details: unknown | null;
    request_id: string | null;
  };
};

export type ChatSummary = {
  id: string;
  dataset_id: string;
  title: string;
  created_at: string;
  updated_at: string;
};

export type UploadDetectedColumn = {
  original_name: string;
  clean_name: string;
  inferred_type: string;
};

export type UploadWarning = {
  code: string;
  message: string;
  severity: "info" | "warning" | "critical" | string;
};

export type UploadSession = {
  id: string;
  original_filename: string;
  file_extension: "csv" | "xlsx";
  file_size_bytes: number;
  status: string;
  sheet_names: string[] | null;
  selected_sheet_name: string | null;
  recommended_sheet_name: string | null;
  preview_rows: Record<string, unknown>[];
  detected_columns: UploadDetectedColumn[];
  warnings: UploadWarning[];
  expires_at: string;
};

export type Dataset = {
  id: string;
  name: string;
  status: "processing" | "ready" | "locked" | "failed" | "deleted" | string;
  source_file_type: "csv" | "xlsx" | string;
  selected_sheet_name: string | null;
  original_filename: string | null;
  row_count: number;
  original_row_count: number;
  duplicate_rows_removed: number;
  column_count: number;
  total_missing_values: number;
  quality_status: string | null;
  quality_score: number | null;
  ingestion_error: string | null;
  created_at: string;
};

export type DatasetColumn = {
  id: string;
  column_index: number;
  column_name: string;
  original_column_name: string;
  postgres_type: string;
  pandas_type: string | null;
  semantic_type: string;
  nullable_count: number;
  nullable_ratio: number;
  distinct_count: number | null;
  sample_values: unknown[] | null;
};

export type DatasetQualityIssue = {
  id: string;
  issue_type: string;
  severity: string;
  title: string;
  description: string;
  affected_row_count: number | null;
  affected_ratio: number | null;
  sample_values: unknown[] | null;
};

export type Chat = ChatSummary;

export type Message = {
  id: string;
  chat_session_id: string;
  message_index: number;
  role: "user" | "assistant" | "system" | string;
  content: string | null;
  blocks: AssistantBlock[] | null;
  created_at: string;
};

export type MessageCreateResponse = {
  message: Message;
  analysis_run_id: string;
};

export type AnalysisRun = {
  id: string;
  chat_session_id: string;
  user_message_id: string;
  assistant_message_id: string | null;
  status: "queued" | "running" | "success" | "partial_success" | "failed" | string;
  current_stage: string | null;
  error_code: string | null;
  error_message: string | null;
  assistant_message: Message | null;
  created_at: string;
};

export type AssistantBlock =
  | { type: "markdown"; content: string }
  | { type: "plan"; steps: string[] }
  | { type: "kpi"; label: string; value: string | number; caption?: string | null }
  | { type: "table"; columns: string[]; rows: Record<string, unknown>[] }
  | { type: "chart"; spec: ChartSpec }
  | { type: "quality_note"; severity: string; title: string; description: string }
  | { type: "suggestions"; suggestions: string[] }
  | { type: "error"; title: string; message: string }
  | { type: string; [key: string]: unknown };

export type ChartSpec = {
  type:
    | "kpi"
    | "line"
    | "bar"
    | "horizontal_bar"
    | "stacked_bar"
    | "area"
    | "pie"
    | "donut"
    | "scatter"
    | "histogram"
    | string;
  title: string;
  x_key?: string | null;
  y_key?: string | null;
  series_key?: string | null;
  value_key?: string | null;
  label_key?: string | null;
  data: Record<string, unknown>[];
  meta?: Record<string, unknown>;
};

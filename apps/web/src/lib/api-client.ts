import { ApiClientError } from "@/lib/errors";
import type {
  AnalysisRun,
  Chat,
  ChatSummary,
  DataEnvelope,
  Dataset,
  DatasetColumn,
  DatasetQualityIssue,
  ErrorEnvelope,
  ListEnvelope,
  Message,
  MessageCreateResponse,
  UploadSession,
} from "@/lib/types";

type ApiClientOptions = {
  baseUrl?: string;
  getToken?: () => Promise<string | null> | string | null;
  fetcher?: typeof fetch;
};

type ApiRequestOptions = {
  method?: "GET" | "POST" | "PATCH" | "DELETE";
  body?: unknown;
  idempotencyKey?: string;
  headers?: HeadersInit;
};

function joinUrl(baseUrl: string, path: string): string {
  const normalizedBase = baseUrl.replace(/\/$/, "");
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${normalizedBase}${normalizedPath}`;
}

function isErrorEnvelope(value: unknown): value is ErrorEnvelope {
  return (
    typeof value === "object" &&
    value !== null &&
    "error" in value &&
    typeof (value as ErrorEnvelope).error?.code === "string"
  );
}

export class ApiClient {
  private readonly baseUrl: string;
  private readonly getToken?: ApiClientOptions["getToken"];
  private readonly fetcher: typeof fetch;

  constructor(options: ApiClientOptions = {}) {
    this.baseUrl = options.baseUrl ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";
    this.getToken = options.getToken;
    this.fetcher = options.fetcher ?? globalThis.fetch.bind(globalThis);
  }

  async request<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
    const headers = new Headers(options.headers);
    headers.set("Accept", "application/json");

    const token = this.getToken ? await this.getToken() : null;
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }

    if (options.idempotencyKey) {
      headers.set("Idempotency-Key", options.idempotencyKey);
    }

    let body: BodyInit | undefined;
    if (options.body !== undefined) {
      if (options.body instanceof FormData) {
        body = options.body;
      } else {
        headers.set("Content-Type", "application/json");
        body = JSON.stringify(options.body);
      }
    }

    let response: Response;
    try {
      response = await this.fetcher(joinUrl(this.baseUrl, path), {
        method: options.method ?? "GET",
        headers,
        body,
        cache: "no-store",
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Network request failed";
      throw new Error(`Cannot reach Sherlock API at ${this.baseUrl}. Check that the API is running and allowed for this browser origin. ${message}`);
    }

    const payload = response.status === 204 ? null : await response.json();
    if (!response.ok) {
      if (isErrorEnvelope(payload)) {
        throw new ApiClientError(response.status, payload);
      }
      throw new Error(`API request failed with status ${response.status}`);
    }

    return payload as T;
  }

  async getData<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
    const envelope = await this.request<DataEnvelope<T>>(path, options);
    return envelope.data;
  }

  async getList<T>(path: string, options: ApiRequestOptions = {}): Promise<ListEnvelope<T>> {
    return this.request<ListEnvelope<T>>(path, options);
  }

  async listChats(): Promise<ListEnvelope<ChatSummary>> {
    return this.getList<ChatSummary>("/chats");
  }

  async createUploadSession(file: File): Promise<UploadSession> {
    const formData = new FormData();
    formData.set("file", file);
    return this.getData<UploadSession>("/upload-sessions", {
      method: "POST",
      body: formData,
    });
  }

  async updateUploadSessionSheet(uploadSessionId: string, selectedSheetName: string): Promise<UploadSession> {
    return this.getData<UploadSession>(`/upload-sessions/${uploadSessionId}`, {
      method: "PATCH",
      body: { selected_sheet_name: selectedSheetName },
    });
  }

  async getUploadSession(uploadSessionId: string): Promise<UploadSession> {
    return this.getData<UploadSession>(`/upload-sessions/${uploadSessionId}`);
  }

  async deleteUploadSession(uploadSessionId: string): Promise<void> {
    await this.request<null>(`/upload-sessions/${uploadSessionId}`, {
      method: "DELETE",
    });
  }

  async createDataset(payload: { upload_session_id: string; name: string; selected_sheet_name?: string | null }): Promise<Dataset> {
    return this.getData<Dataset>("/datasets", { method: "POST", body: payload });
  }

  async getDataset(datasetId: string): Promise<Dataset> {
    return this.getData<Dataset>(`/datasets/${datasetId}`);
  }

  async getDatasetColumns(datasetId: string): Promise<ListEnvelope<DatasetColumn>> {
    return this.getList<DatasetColumn>(`/datasets/${datasetId}/columns`);
  }

  async getDatasetQualityIssues(datasetId: string): Promise<ListEnvelope<DatasetQualityIssue>> {
    return this.getList<DatasetQualityIssue>(`/datasets/${datasetId}/quality-issues`);
  }

  async getDatasetPreview(datasetId: string, cursor?: string | null): Promise<ListEnvelope<Record<string, unknown>>> {
    const suffix = cursor ? `?cursor=${encodeURIComponent(cursor)}` : "";
    return this.getList<Record<string, unknown>>(`/datasets/${datasetId}/preview${suffix}`);
  }

  async createChat(datasetId: string): Promise<Chat> {
    return this.getData<Chat>("/chats", { method: "POST", body: { dataset_id: datasetId } });
  }

  async getChat(chatId: string): Promise<Chat> {
    return this.getData<Chat>(`/chats/${chatId}`);
  }

  async getMessages(chatId: string): Promise<ListEnvelope<Message>> {
    return this.getList<Message>(`/chats/${chatId}/messages`);
  }

  async sendMessage(chatId: string, content: string, idempotencyKey: string): Promise<MessageCreateResponse> {
    return this.getData<MessageCreateResponse>(`/chats/${chatId}/messages`, {
      method: "POST",
      body: { content },
      idempotencyKey,
    });
  }

  async getAnalysisRun(analysisRunId: string): Promise<AnalysisRun> {
    return this.getData<AnalysisRun>(`/analysis-runs/${analysisRunId}`);
  }
}

export const apiClient = new ApiClient();

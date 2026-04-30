import { describe, expect, it, vi } from "vitest";

import { ApiClient } from "@/lib/api-client";
describe("ApiClient", () => {
  it("attaches Authorization header", async () => {
    const fetcher = vi.fn(async (...args: Parameters<typeof fetch>) => {
      void args;
      return Response.json({ data: { ok: true } });
    });
    const client = new ApiClient({
      baseUrl: "https://api.example.com/api/v1",
      getToken: () => "token_123",
      fetcher,
    });

    await client.getData<{ ok: boolean }>("/users/me");

    const headers = fetcher.mock.calls[0][1]?.headers as Headers;
    expect(headers.get("Authorization")).toBe("Bearer token_123");
  });

  it("attaches Idempotency-Key when provided", async () => {
    const fetcher = vi.fn(async (...args: Parameters<typeof fetch>) => {
      void args;
      return Response.json({ data: { ok: true } });
    });
    const client = new ApiClient({ baseUrl: "https://api.example.com/api/v1", fetcher });

    await client.request("/chats/chat_123/messages", {
      method: "POST",
      body: { content: "Show revenue" },
      idempotencyKey: "idem_123",
    });

    const headers = fetcher.mock.calls[0][1]?.headers as Headers;
    expect(headers.get("Idempotency-Key")).toBe("idem_123");
  });

  it("parses data envelopes", async () => {
    const fetcher = vi.fn(async (...args: Parameters<typeof fetch>) => {
      void args;
      return Response.json({ data: { status: "ok" } });
    });
    const client = new ApiClient({ baseUrl: "https://api.example.com/api/v1", fetcher });

    await expect(client.getData<{ status: string }>("/health")).resolves.toEqual({ status: "ok" });
  });

  it("throws typed errors for error envelopes", async () => {
    const fetcher = vi.fn(
      async (...args: Parameters<typeof fetch>) => {
        void args;
        return new Response(
          JSON.stringify({
            error: {
              code: "NOT_FOUND",
              message: "Dataset not found.",
              details: null,
              request_id: "req_123",
            },
          }),
          { status: 404, headers: { "Content-Type": "application/json" } },
        );
      },
    );
    const client = new ApiClient({ baseUrl: "https://api.example.com/api/v1", fetcher });

    await expect(client.getData("/datasets/dataset_123")).rejects.toMatchObject({
      code: "NOT_FOUND",
      requestId: "req_123",
      status: 404,
    });
  });

  it("posts upload sessions as multipart form data", async () => {
    const fetcher = vi.fn(async (...args: Parameters<typeof fetch>) => {
      void args;
      return Response.json({
        data: {
          id: "upload_123",
          original_filename: "sales.csv",
          file_extension: "csv",
          file_size_bytes: 12,
          status: "inspected",
          sheet_names: null,
          selected_sheet_name: null,
          recommended_sheet_name: null,
          preview_rows: [],
          detected_columns: [],
          warnings: [],
          expires_at: "2026-05-03T00:00:00Z",
        },
      });
    });
    const client = new ApiClient({ baseUrl: "https://api.example.com/api/v1", fetcher });

    await client.createUploadSession(new File(["a,b\n1,2\n"], "sales.csv", { type: "text/csv" }));

    const request = fetcher.mock.calls[0][1];
    const headers = request?.headers as Headers;
    expect(request?.method).toBe("POST");
    expect(request?.body).toBeInstanceOf(FormData);
    expect(headers.get("Content-Type")).toBeNull();
  });
});

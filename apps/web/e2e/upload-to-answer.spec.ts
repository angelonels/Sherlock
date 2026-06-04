import { expect, test } from "@playwright/test";

const apiBase = "http://127.0.0.1:8000/api/v1";

test("mocked upload-to-answer investigation flow", async ({ page }) => {
  await page.route(`${apiBase}/**`, async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname.replace("/api/v1", "");
    const method = request.method();

    if (method === "GET" && path === "/chats") {
      await route.fulfill({ json: { data: [], pagination: { next_cursor: null } } });
      return;
    }

    if (method === "POST" && path === "/upload-sessions") {
      await route.fulfill({
        status: 201,
        json: {
          data: {
            id: "upload_123",
            original_filename: "sales.csv",
            file_extension: "csv",
            file_size_bytes: 32,
            status: "inspected",
            sheet_names: null,
            selected_sheet_name: null,
            recommended_sheet_name: null,
            preview_rows: [{ region: "West", revenue: "100" }],
            detected_columns: [
              { original_name: "region", clean_name: "region", inferred_type: "text" },
              { original_name: "revenue", clean_name: "revenue", inferred_type: "numeric" },
            ],
            warnings: [],
            expires_at: "2026-05-31T00:00:00Z",
          },
        },
      });
      return;
    }

    if (method === "POST" && path === "/datasets") {
      await route.fulfill({
        status: 202,
        json: {
          data: {
            id: "dataset_123",
            name: "Sales",
            status: "processing",
            source_file_type: "csv",
            selected_sheet_name: null,
            original_filename: "sales.csv",
            row_count: 0,
            original_row_count: 0,
            duplicate_rows_removed: 0,
            column_count: 0,
            total_missing_values: 0,
            quality_status: null,
            quality_score: null,
            ingestion_error: null,
            created_at: "2026-05-31T00:00:00Z",
          },
        },
      });
      return;
    }

    if (method === "GET" && path === "/datasets/dataset_123") {
      await route.fulfill({
        json: {
          data: {
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
            quality_score: 95,
            ingestion_error: null,
            created_at: "2026-05-31T00:00:00Z",
          },
        },
      });
      return;
    }

    if (method === "GET" && path === "/datasets/dataset_123/preview") {
      await route.fulfill({
        json: { data: [{ region: "West", revenue: 100 }], pagination: { next_cursor: null } },
      });
      return;
    }

    if (method === "GET" && path === "/datasets/dataset_123/columns") {
      await route.fulfill({
        json: {
          data: [
            {
              id: "column_1",
              column_index: 0,
              column_name: "region",
              original_column_name: "region",
              postgres_type: "text",
              pandas_type: "object",
              semantic_type: "category",
              nullable_count: 0,
              nullable_ratio: 0,
              distinct_count: 1,
              sample_values: ["West"],
              warning_flags: [],
            },
            {
              id: "column_2",
              column_index: 1,
              column_name: "revenue",
              original_column_name: "revenue",
              postgres_type: "numeric",
              pandas_type: "int64",
              semantic_type: "numeric",
              nullable_count: 0,
              nullable_ratio: 0,
              distinct_count: 1,
              sample_values: [100],
              warning_flags: [],
            },
          ],
          pagination: { next_cursor: null },
        },
      });
      return;
    }

    if (method === "GET" && path === "/datasets/dataset_123/quality-issues") {
      await route.fulfill({ json: { data: [], pagination: { next_cursor: null } } });
      return;
    }

    if (method === "POST" && path === "/chats") {
      await route.fulfill({
        status: 201,
        json: {
          data: {
            id: "chat_123",
            dataset_id: "dataset_123",
            title: "Sales investigation",
            created_at: "2026-05-31T00:00:00Z",
            updated_at: "2026-05-31T00:00:00Z",
          },
        },
      });
      return;
    }

    if (method === "GET" && path === "/chats/chat_123") {
      await route.fulfill({
        json: {
          data: {
            id: "chat_123",
            dataset_id: "dataset_123",
            title: "Sales investigation",
            created_at: "2026-05-31T00:00:00Z",
            updated_at: "2026-05-31T00:00:00Z",
          },
        },
      });
      return;
    }

    if (method === "GET" && path === "/chats/chat_123/messages") {
      await route.fulfill({ json: { data: [], pagination: { next_cursor: null } } });
      return;
    }

    if (method === "POST" && path === "/chats/chat_123/messages") {
      await route.fulfill({
        status: 202,
        json: {
          data: {
            message: {
              id: "message_user_1",
              chat_session_id: "chat_123",
              message_index: 1,
              role: "user",
              content: "What is total revenue?",
              blocks: null,
              created_at: "2026-05-31T00:00:00Z",
            },
            analysis_run_id: "run_123",
          },
        },
      });
      return;
    }

    if (method === "GET" && path === "/analysis-runs/run_123") {
      await route.fulfill({
        json: {
          data: {
            id: "run_123",
            chat_session_id: "chat_123",
            user_message_id: "message_user_1",
            assistant_message_id: "message_assistant_1",
            status: "success",
            current_stage: "completed",
            error_code: null,
            error_message: null,
            assistant_message: {
              id: "message_assistant_1",
              chat_session_id: "chat_123",
              message_index: 2,
              role: "assistant",
              content: "Total revenue is 100.",
              blocks: [
                { type: "markdown", content: "Total revenue is **100**." },
                { type: "kpi", label: "Rows", value: 2, caption: "After duplicate removal" },
                { type: "table", columns: ["region", "revenue"], rows: [{ region: "West", revenue: 100 }] },
              ],
              created_at: "2026-05-31T00:00:00Z",
            },
            created_at: "2026-05-31T00:00:00Z",
          },
        },
      });
      return;
    }

    await route.fulfill({ status: 404, json: { error: { code: "NOT_FOUND", message: path } } });
  });

  await page.goto("/app/new");
  await page.getByLabel(/Upload CSV or XLSX file/i).setInputFiles({
    name: "sales.csv",
    mimeType: "text/csv",
    buffer: Buffer.from("region,revenue\nWest,100\n"),
  });

  await expect(page.getByText("sales.csv")).toBeVisible();
  await page.getByRole("button", { name: /Create Dataset/i }).click();
  await expect(page.getByText("Dataset review")).toBeVisible();
  await expect(page.getByText(/2 rows/i)).toBeVisible();

  await page.getByRole("button", { name: /Start Investigation/i }).click();
  await expect(page).toHaveURL(/\/app\/chat\/chat_123/);

  await page.getByPlaceholder(/Ask about rows/i).fill("What is total revenue?");
  await page.getByRole("button", { name: /Send message/i }).click();

  await expect(page.getByText("Total revenue is")).toBeVisible();
  await expect(page.getByText("Rows", { exact: true })).toBeVisible();
  await expect(page.getByRole("cell", { name: "West" }).first()).toBeVisible();
});

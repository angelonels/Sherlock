import { expect, type Page, test } from "@playwright/test";

const apiBase = "http://127.0.0.1:8000/api/v1";

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
  column_count: 2,
  total_missing_values: 0,
  quality_status: "good",
  quality_score: 100,
  ingestion_error: null,
  created_at: "2026-06-10T00:00:00Z",
};

async function routeAppApi(page: Page, options: { emptyChats?: boolean; failedRun?: boolean } = {}) {
  await page.route(`${apiBase}/**`, async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname.replace("/api/v1", "");
    const method = request.method();

    if (method === "GET" && path === "/chats") {
      await route.fulfill({ json: { data: options.emptyChats ? [] : [chat], pagination: { next_cursor: null } } });
      return;
    }
    if (method === "GET" && path === "/chats/chat_123") {
      await route.fulfill({ json: { data: chat } });
      return;
    }
    if (method === "GET" && path === "/chats/chat_123/messages") {
      await route.fulfill({ json: { data: [], pagination: { next_cursor: null } } });
      return;
    }
    if (method === "GET" && path === "/datasets/dataset_123") {
      await route.fulfill({ json: { data: dataset } });
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
    if (method === "GET" && path === "/datasets/dataset_123/preview") {
      await route.fulfill({
        json: { data: [{ _sherlock_row_id: 1, region: "West", revenue: 100 }], pagination: { next_cursor: null } },
      });
      return;
    }
    if (method === "POST" && path === "/chats/chat_123/messages") {
      await route.fulfill({
        status: 202,
        json: {
          data: {
            message: {
              id: "message_user",
              chat_session_id: "chat_123",
              message_index: 1,
              role: "user",
              content: "Trigger failure",
              blocks: null,
              created_at: "2026-06-10T00:00:00Z",
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
            user_message_id: "message_user",
            assistant_message_id: null,
            status: options.failedRun ? "failed" : "success",
            current_stage: options.failedRun ? "failed" : "completed",
            error_code: options.failedRun ? "ANALYSIS_WORKFLOW_FAILED" : null,
            error_message: options.failedRun
              ? "Sherlock could not complete this analysis. Try rephrasing the question or asking a narrower question."
              : null,
            assistant_message: null,
            created_at: "2026-06-10T00:00:00Z",
          },
        },
      });
      return;
    }

    await route.fulfill({ status: 404, json: { error: { code: "NOT_FOUND", message: path } } });
  });
}

test("first-time app shows the upload-focused empty state", async ({ page }) => {
  await routeAppApi(page, { emptyChats: true });
  await page.goto("/app");

  await expect(page.getByRole("heading", { name: "Start with a CSV or XLSX file" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Upload dataset" })).toHaveAttribute("href", "/app/new");
});

test("reopens an investigation and controls desktop sidebar and inspector", async ({ page }) => {
  await routeAppApi(page);
  await page.goto("/app");

  await page.getByLabel("Investigation hub").getByRole("link", { name: "Sales investigation" }).click();
  await expect(page).toHaveURL(/\/app\/chat\/chat_123/);
  await expect(page.getByRole("heading", { name: "Sales investigation" })).toBeVisible();

  await page.getByRole("button", { name: "Close chat sidebar" }).click();
  await page.getByRole("button", { name: "Close dataset panel" }).click();
  await expect(page.getByRole("button", { name: "Open chat sidebar" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Open dataset panel" })).toBeVisible();
  await page.getByRole("button", { name: "Open chat sidebar" }).click();
  await page.getByRole("button", { name: "Open dataset panel" }).click();
  await expect(page.getByRole("complementary", { name: "Chat sidebar" })).toBeVisible();
  await expect(page.getByLabel("Dataset panel", { exact: true })).toBeVisible();
});

test("failed analysis is user-safe and leaves the composer recoverable", async ({ page }) => {
  await routeAppApi(page, { failedRun: true });
  await page.goto("/app/chat/chat_123");

  const composer = page.getByPlaceholder(/Ask about rows/i);
  await composer.fill("Trigger failure");
  await page.getByRole("button", { name: "Send message" }).click();

  await expect(page.getByRole("alert").filter({ hasText: "Sherlock could not complete" })).toContainText("Try rephrasing");
  await expect(page.getByText(/SELECT secret|\/tmp\/secret/)).toHaveCount(0);
  await composer.fill("Try a narrower question");
  await expect(page.getByRole("button", { name: "Send message" })).toBeEnabled();
});

test("opens and closes sidebar and inspector drawers on mobile", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await routeAppApi(page);
  await page.goto("/app/chat/chat_123");

  await page.getByRole("button", { name: "Open chat sidebar" }).click();
  const chatDrawer = page.getByRole("dialog", { name: "Investigations" });
  await expect(chatDrawer).toBeVisible();
  await chatDrawer.getByRole("button", { name: "Close chat sidebar" }).click();
  await expect(chatDrawer).toHaveCount(0);

  await page.getByRole("button", { name: "Open dataset panel" }).click();
  const datasetDrawer = page.getByRole("dialog", { name: "Dataset inspector" });
  await expect(datasetDrawer).toBeVisible();
  await datasetDrawer.getByRole("button", { name: "Close dataset panel" }).click();
  await expect(datasetDrawer).toHaveCount(0);
});

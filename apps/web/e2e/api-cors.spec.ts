import { expect, test } from "@playwright/test";

test("upload API is reachable from the local browser origin", async ({ page }) => {
  await page.goto("/");

  const result = await page.evaluate(async () => {
    const formData = new FormData();
    formData.set("file", new File(["region,revenue\nWest,100\nEast,200\n"], "cors-check.csv", { type: "text/csv" }));

    try {
      const response = await fetch("http://127.0.0.1:8000/api/v1/upload-sessions", {
        method: "POST",
        headers: { Authorization: "Bearer invalid-local-cors-check" },
        body: formData,
      });
      return { reachedApi: true, status: response.status };
    } catch (error) {
      return {
        reachedApi: false,
        message: error instanceof Error ? error.message : "Unknown browser fetch failure",
      };
    }
  });

  expect(result).toEqual({ reachedApi: true, status: 401 });
});

import { expect, test } from "@playwright/test";

test("logged-out landing page renders with auth CTAs", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: /investigate spreadsheets with evidence/i })).toBeVisible();
  await expect(page.getByLabel("Main navigation").getByRole("link", { name: /open app/i })).toBeVisible();
  await expect(page.getByRole("link", { name: /start an investigation/i })).toBeVisible();
});

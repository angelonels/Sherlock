import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  expect: {
    timeout: 10_000,
  },
  fullyParallel: true,
  use: {
    baseURL: "http://127.0.0.1:3100",
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: [
    {
      command:
        "cd ../api && FRONTEND_ORIGIN=http://127.0.0.1:3100 uv run uvicorn app.main:app --host 127.0.0.1 --port 8000",
      url: "http://127.0.0.1:8000/api/v1/health",
      reuseExistingServer: true,
      timeout: 30_000,
    },
    {
      command:
        "ulimit -n 8192 && NEXT_PUBLIC_AUTH_BYPASS=true NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY= NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1 pnpm build && NEXT_PUBLIC_AUTH_BYPASS=true NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY= NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1 pnpm start --hostname 127.0.0.1 --port 3100",
      url: "http://127.0.0.1:3100",
      reuseExistingServer: true,
      timeout: 120_000,
    },
  ],
});

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const protect = vi.fn();
const clerkHandler = vi.fn(async () => new Response("clerk"));
const nextResponse = new Response("next");

vi.mock("@clerk/nextjs/server", () => ({
  clerkMiddleware:
    (callback: (auth: { protect: typeof protect }, request: { nextUrl: { pathname: string } }) => Promise<void>) =>
    async (request: { nextUrl: { pathname: string } }) => {
      await callback({ protect }, request);
      return clerkHandler();
    },
  createRouteMatcher:
    () =>
    (request: { nextUrl: { pathname: string } }) =>
      request.nextUrl.pathname.startsWith("/app"),
}));

vi.mock("next/server", () => ({
  NextResponse: {
    next: vi.fn(() => nextResponse),
  },
}));

import proxy from "@/proxy";

describe("Clerk proxy", () => {
  const originalEnv = process.env;

  beforeEach(() => {
    process.env = { ...originalEnv };
    delete process.env.NEXT_PUBLIC_AUTH_BYPASS;
    delete process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;
    protect.mockReset();
    clerkHandler.mockClear();
  });

  afterEach(() => {
    process.env = originalEnv;
  });

  it("leaves missing-Clerk handling to the fail-closed client gate", async () => {
    const response = await proxy(
      { nextUrl: { pathname: "/app" } } as never,
      {} as never,
    );

    expect(response).toBe(nextResponse);
    expect(protect).not.toHaveBeenCalled();
  });

  it("allows the explicit automated-test bypass", async () => {
    process.env.NEXT_PUBLIC_AUTH_BYPASS = "true";
    process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY = "pk_test_mock";

    const response = await proxy(
      { nextUrl: { pathname: "/app" } } as never,
      {} as never,
    );

    expect(response).toBe(nextResponse);
    expect(protect).not.toHaveBeenCalled();
  });

  it("protects app routes when Clerk is configured", async () => {
    process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY = "pk_test_mock";

    await proxy({ nextUrl: { pathname: "/app/chat/chat_123" } } as never, {} as never);

    expect(protect).toHaveBeenCalledOnce();
  });

  it("does not require authentication for public routes", async () => {
    process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY = "pk_test_mock";

    await proxy({ nextUrl: { pathname: "/" } } as never, {} as never);

    expect(protect).not.toHaveBeenCalled();
    expect(clerkHandler).toHaveBeenCalledOnce();
  });
});

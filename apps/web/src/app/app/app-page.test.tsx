import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";

vi.mock("@/features/auth/server", () => ({
  getServerAuthState: async () => ({ isSignedIn: true, userId: "user_123" }),
}));

vi.mock("@/features/auth/protected-app-route", () => ({
  ProtectedAppRoute: ({ children }: { children: ReactNode }) => <>{children}</>,
}));

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    getToken: async () => "clerk_token_123",
  }),
}));

vi.mock("next/navigation", () => ({
  redirect: vi.fn(),
}));

import AppPage from "@/app/app/page";

describe("/app route", () => {
  it("renders for an authenticated user", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => Response.json({ data: [], pagination: { next_cursor: null } })),
    );

    render(await AppPage());

    expect(screen.getByRole("heading", { name: /Investigation desk/i })).toBeVisible();
  });
});

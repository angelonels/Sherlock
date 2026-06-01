import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";

vi.mock("@/features/auth/protected-app-route", () => ({
  ProtectedAppRoute: ({ children }: { children: ReactNode }) => <>{children}</>,
}));

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    getToken: async () => "clerk_token_123",
  }),
  useClerk: () => ({
    signOut: async () => undefined,
  }),
}));

vi.mock("next/navigation", () => ({
  redirect: vi.fn(),
}));

import AppPage from "@/app/app/page";

describe("/app route", () => {
  it("renders for an authenticated user", async () => {
    vi.stubEnv("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY", "pk_test_fake");
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => Response.json({ data: [], pagination: { next_cursor: null } })),
    );

    const queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });
    render(<QueryClientProvider client={queryClient}>{await AppPage()}</QueryClientProvider>);

    expect(screen.getByRole("heading", { name: /Investigation desk/i })).toBeVisible();
  });
});

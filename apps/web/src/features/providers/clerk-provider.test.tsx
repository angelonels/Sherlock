import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { SherlockClerkProvider } from "@/features/providers/clerk-provider";

vi.mock("@clerk/nextjs", () => ({
  ClerkProvider: ({
    children,
    signInUrl,
    signUpUrl,
    signInFallbackRedirectUrl,
    signUpFallbackRedirectUrl,
    signInForceRedirectUrl,
    signUpForceRedirectUrl,
  }: {
    children: ReactNode;
    signInUrl: string;
    signUpUrl: string;
    signInFallbackRedirectUrl: string;
    signUpFallbackRedirectUrl: string;
    signInForceRedirectUrl: string;
    signUpForceRedirectUrl: string;
  }) => (
    <div
      data-testid="clerk-provider"
      data-sign-in-fallback-redirect-url={signInFallbackRedirectUrl}
      data-sign-in-force-redirect-url={signInForceRedirectUrl}
      data-sign-in-url={signInUrl}
      data-sign-up-fallback-redirect-url={signUpFallbackRedirectUrl}
      data-sign-up-force-redirect-url={signUpForceRedirectUrl}
      data-sign-up-url={signUpUrl}
    >
      {children}
    </div>
  ),
}));

describe("SherlockClerkProvider", () => {
  const originalEnv = process.env;

  beforeEach(() => {
    process.env = { ...originalEnv };
  });

  afterEach(() => {
    process.env = originalEnv;
  });

  it("renders children without ClerkProvider when local Clerk keys are absent", () => {
    delete process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;

    render(
      <SherlockClerkProvider>
        <p>Landing remains available</p>
      </SherlockClerkProvider>,
    );

    expect(screen.getByText("Landing remains available")).toBeVisible();
    expect(screen.queryByTestId("clerk-provider")).not.toBeInTheDocument();
  });

  it("passes local sign-in and sign-up redirect envs to ClerkProvider", () => {
    process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY = "pk_test_mock";

    render(
      <SherlockClerkProvider>
        <p>App routes</p>
      </SherlockClerkProvider>,
    );

    const provider = screen.getByTestId("clerk-provider");
    expect(provider).toHaveAttribute("data-sign-in-url", "/sign-in");
    expect(provider).toHaveAttribute("data-sign-up-url", "/sign-up");
    expect(provider).toHaveAttribute("data-sign-in-fallback-redirect-url", "/app");
    expect(provider).toHaveAttribute("data-sign-up-fallback-redirect-url", "/app");
    expect(provider).toHaveAttribute("data-sign-in-force-redirect-url", "/app");
    expect(provider).toHaveAttribute("data-sign-up-force-redirect-url", "/app");
  });
});

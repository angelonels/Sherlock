import { render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { RequireAuth } from "@/features/auth/auth-gate";

let authState: { isLoaded?: boolean; isSignedIn?: boolean } = {
  isLoaded: true,
  isSignedIn: true,
};

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => authState,
}));

describe("RequireAuth", () => {
  const originalEnv = process.env;

  beforeEach(() => {
    process.env = { ...originalEnv };
    delete process.env.NEXT_PUBLIC_AUTH_BYPASS;
    delete process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;
    authState = { isLoaded: true, isSignedIn: true };
  });

  afterEach(() => {
    process.env = originalEnv;
  });

  it("fails closed when Clerk is not configured", () => {
    render(
      <RequireAuth>
        <p>Private investigation</p>
      </RequireAuth>,
    );

    expect(screen.getByRole("alert")).toHaveTextContent("Authentication is unavailable");
    expect(screen.queryByText("Private investigation")).not.toBeInTheDocument();
  });

  it("allows the explicit test bypass", () => {
    process.env.NEXT_PUBLIC_AUTH_BYPASS = "true";

    render(
      <RequireAuth>
        <p>Private investigation</p>
      </RequireAuth>,
    );

    expect(screen.getByText("Private investigation")).toBeVisible();
  });

  it("renders authenticated children through Clerk", () => {
    process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY = "pk_test_mock";

    render(
      <RequireAuth>
        <p>Private investigation</p>
      </RequireAuth>,
    );

    expect(screen.getByText("Private investigation")).toBeVisible();
  });

  it("fails closed while Clerk session state is indeterminate", () => {
    process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY = "pk_test_mock";
    authState = {};

    render(
      <RequireAuth>
        <p>Private investigation</p>
      </RequireAuth>,
    );

    expect(screen.getByText("Checking session")).toBeVisible();
    expect(screen.queryByText("Private investigation")).not.toBeInTheDocument();
  });

  it("fails closed for a signed-out Clerk session", () => {
    process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY = "pk_test_mock";
    authState = { isLoaded: true, isSignedIn: false };

    render(
      <RequireAuth>
        <p>Private investigation</p>
      </RequireAuth>,
    );

    expect(screen.getByText("Checking session")).toBeVisible();
    expect(screen.queryByText("Private investigation")).not.toBeInTheDocument();
  });
});

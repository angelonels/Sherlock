import { render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import SignInPage from "@/app/sign-in/[[...sign-in]]/page";
import SignUpPage from "@/app/sign-up/[[...sign-up]]/page";

vi.mock("@clerk/nextjs", () => ({
  SignIn: (props: {
    path: string;
    signUpUrl: string;
    fallbackRedirectUrl: string;
    forceRedirectUrl: string;
    signUpFallbackRedirectUrl: string;
    signUpForceRedirectUrl: string;
    oauthFlow: string;
  }) => (
    <section
      aria-label="Clerk sign-in flow"
      data-fallback-redirect-url={props.fallbackRedirectUrl}
      data-force-redirect-url={props.forceRedirectUrl}
      data-oauth-flow={props.oauthFlow}
      data-path={props.path}
      data-sign-up-fallback-redirect-url={props.signUpFallbackRedirectUrl}
      data-sign-up-force-redirect-url={props.signUpForceRedirectUrl}
      data-sign-up-url={props.signUpUrl}
    >
      Clerk SignIn
    </section>
  ),
  SignUp: (props: {
    path: string;
    signInUrl: string;
    fallbackRedirectUrl: string;
    forceRedirectUrl: string;
    signInFallbackRedirectUrl: string;
    signInForceRedirectUrl: string;
    oauthFlow: string;
  }) => (
    <section
      aria-label="Clerk sign-up flow"
      data-fallback-redirect-url={props.fallbackRedirectUrl}
      data-force-redirect-url={props.forceRedirectUrl}
      data-oauth-flow={props.oauthFlow}
      data-path={props.path}
      data-sign-in-fallback-redirect-url={props.signInFallbackRedirectUrl}
      data-sign-in-force-redirect-url={props.signInForceRedirectUrl}
      data-sign-in-url={props.signInUrl}
    >
      Clerk SignUp
    </section>
  ),
}));

describe("auth routes", () => {
  const originalEnv = process.env;

  beforeEach(() => {
    process.env = { ...originalEnv };
  });

  afterEach(() => {
    process.env = originalEnv;
  });

  it("renders the sign-in route", () => {
    delete process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;
    render(<SignInPage />);

    expect(screen.getByRole("heading", { name: /Open Sherlock/i })).toBeVisible();
  });

  it("renders the sign-up route", () => {
    delete process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;
    render(<SignUpPage />);

    expect(screen.getByRole("heading", { name: /Start with Sherlock/i })).toBeVisible();
  });

  it("renders Clerk SignIn with the local auth methods enabled by Clerk", () => {
    process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY = "pk_test_mock";

    render(<SignInPage />);

    const flow = screen.getByLabelText("Clerk sign-in flow");
    expect(flow).toHaveAttribute("data-path", "/sign-in");
    expect(flow).toHaveAttribute("data-sign-up-url", "/sign-up");
    expect(flow).toHaveAttribute("data-fallback-redirect-url", "/app");
    expect(flow).toHaveAttribute("data-force-redirect-url", "/app");
    expect(flow).toHaveAttribute("data-oauth-flow", "redirect");
  });

  it("renders Clerk SignUp with the local auth methods enabled by Clerk", () => {
    process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY = "pk_test_mock";

    render(<SignUpPage />);

    const flow = screen.getByLabelText("Clerk sign-up flow");
    expect(flow).toHaveAttribute("data-path", "/sign-up");
    expect(flow).toHaveAttribute("data-sign-in-url", "/sign-in");
    expect(flow).toHaveAttribute("data-fallback-redirect-url", "/app");
    expect(flow).toHaveAttribute("data-force-redirect-url", "/app");
    expect(flow).toHaveAttribute("data-oauth-flow", "redirect");
  });
});

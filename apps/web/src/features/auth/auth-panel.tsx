"use client";

import { SignIn, SignUp } from "@clerk/nextjs";
import Link from "next/link";

type AuthPanelProps = {
  mode: "sign-in" | "sign-up";
};

export function AuthPanel({ mode }: AuthPanelProps) {
  const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;
  const isSignIn = mode === "sign-in";
  const signInUrl = process.env.NEXT_PUBLIC_CLERK_SIGN_IN_URL ?? "/sign-in";
  const signUpUrl = process.env.NEXT_PUBLIC_CLERK_SIGN_UP_URL ?? "/sign-up";
  const signInFallbackRedirectUrl =
    process.env.NEXT_PUBLIC_CLERK_SIGN_IN_FALLBACK_REDIRECT_URL ?? "/app";
  const signUpFallbackRedirectUrl =
    process.env.NEXT_PUBLIC_CLERK_SIGN_UP_FALLBACK_REDIRECT_URL ?? "/app";
  const signInForceRedirectUrl =
    process.env.NEXT_PUBLIC_CLERK_SIGN_IN_FORCE_REDIRECT_URL ?? "/app";
  const signUpForceRedirectUrl =
    process.env.NEXT_PUBLIC_CLERK_SIGN_UP_FORCE_REDIRECT_URL ?? "/app";

  if (!publishableKey) {
    return (
      <div className="w-full max-w-md border border-[#d9cdbf] bg-[#fffaf7] p-8 shadow-[0_30px_70px_-48px_rgba(70,47,30,0.75)]">
        <p className="font-mono text-xs uppercase tracking-[0.18em] text-[#8f6a4e]">
          {isSignIn ? "Sign in" : "Sign up"}
        </p>
        <h1 className="mt-4 text-3xl font-semibold tracking-[-0.055em] text-[#241f1a]">
          {isSignIn ? "Open Sherlock" : "Start with Sherlock"}
        </h1>
        <p className="mt-4 text-sm leading-6 text-[#655c52]">
          Clerk is ready to connect. Add your Clerk environment keys to enable the hosted
          authentication flow locally.
        </p>
        <Link
          href={isSignIn ? "/sign-up" : "/sign-in"}
          className="mt-8 inline-flex h-11 items-center justify-center border border-[#241f1a] bg-[#241f1a] px-4 text-sm font-semibold text-[#fffaf7] transition-colors hover:bg-[#3b332d] focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-[#b56b32]/25"
        >
          {isSignIn ? "Create an account" : "I already have an account"}
        </Link>
      </div>
    );
  }

  return isSignIn ? (
    <SignIn
      routing="path"
      path={signInUrl}
      signUpUrl={signUpUrl}
      fallbackRedirectUrl={signInFallbackRedirectUrl}
      forceRedirectUrl={signInForceRedirectUrl}
      signUpFallbackRedirectUrl={signUpFallbackRedirectUrl}
      signUpForceRedirectUrl={signUpForceRedirectUrl}
      oauthFlow="redirect"
    />
  ) : (
    <SignUp
      routing="path"
      path={signUpUrl}
      signInUrl={signInUrl}
      fallbackRedirectUrl={signUpFallbackRedirectUrl}
      forceRedirectUrl={signUpForceRedirectUrl}
      signInFallbackRedirectUrl={signInFallbackRedirectUrl}
      signInForceRedirectUrl={signInForceRedirectUrl}
      oauthFlow="redirect"
    />
  );
}

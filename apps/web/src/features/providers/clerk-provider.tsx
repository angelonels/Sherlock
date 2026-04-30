"use client";

import { ClerkProvider } from "@clerk/nextjs";
import type { ReactNode } from "react";

type SherlockClerkProviderProps = {
  children: ReactNode;
};

export function SherlockClerkProvider({ children }: SherlockClerkProviderProps) {
  const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;
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
    return <>{children}</>;
  }

  return (
    <ClerkProvider
      publishableKey={publishableKey}
      signInUrl={signInUrl}
      signUpUrl={signUpUrl}
      signInFallbackRedirectUrl={signInFallbackRedirectUrl}
      signUpFallbackRedirectUrl={signUpFallbackRedirectUrl}
      signInForceRedirectUrl={signInForceRedirectUrl}
      signUpForceRedirectUrl={signUpForceRedirectUrl}
    >
      {children}
    </ClerkProvider>
  );
}

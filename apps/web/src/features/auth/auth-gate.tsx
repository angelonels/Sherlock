"use client";

import { SherlockThinkingState } from "@/components/ai/sherlock-ai";
import { isAuthBypassEnabled, isClerkConfigured } from "@/features/auth/auth-config";
import { useAuth } from "@clerk/nextjs";
import type { ReactNode } from "react";
import { useEffect } from "react";

type AuthGateProps = {
  children: ReactNode;
};

function replaceRoute(path: string) {
  if (typeof window === "undefined" || window.location.pathname === path) {
    return;
  }
  window.location.replace(path);
}

export function RequireAuth({ children }: AuthGateProps) {
  if (isAuthBypassEnabled()) {
    return <>{children}</>;
  }
  if (!isClerkConfigured()) {
    return <AuthConfigurationError />;
  }

  return <RequireClerkAuth>{children}</RequireClerkAuth>;
}

function AuthConfigurationError() {
  return (
    <main className="grid min-h-dvh place-items-center bg-[#f7f3ec] px-6 text-[#241f1a]">
      <div className="max-w-lg border border-[#b84b3c] bg-[#fff2ef] p-5" role="alert">
        <h1 className="text-lg font-semibold">Authentication is unavailable</h1>
        <p className="mt-2 text-sm text-[#7d2f26]">
          Sherlock requires Clerk authentication. Contact the deployment administrator.
        </p>
      </div>
    </main>
  );
}

function RequireClerkAuth({ children }: AuthGateProps) {
  const { isLoaded, isSignedIn } = useAuth();
  const sessionLoaded = isLoaded === true;
  const signedIn = isSignedIn === true;

  useEffect(() => {
    if (sessionLoaded && !signedIn) {
      replaceRoute("/");
    }
  }, [sessionLoaded, signedIn]);

  if (!sessionLoaded || !signedIn) {
    return (
      <main className="grid min-h-dvh place-items-center bg-[#f7f3ec] text-[#241f1a]">
        <SherlockThinkingState className="flex items-center gap-2" label="Checking session" />
      </main>
    );
  }

  return <>{children}</>;
}

export function RedirectIfAuthenticated() {
  if (isAuthBypassEnabled() || !isClerkConfigured()) {
    return null;
  }

  return <RedirectIfClerkAuthenticated />;
}

function RedirectIfClerkAuthenticated() {
  const { isLoaded, isSignedIn } = useAuth();

  useEffect(() => {
    if (isLoaded === true && isSignedIn === true) {
      replaceRoute("/app");
    }
  }, [isLoaded, isSignedIn]);

  return null;
}

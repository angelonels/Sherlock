import { describe, expect, it } from "vitest";

import { resolveAppRoute, resolveLandingRoute } from "@/features/auth/auth-routing";

describe("auth route resolution", () => {
  it("redirects logged-out app visitors to the landing page", () => {
    expect(resolveAppRoute({ isSignedIn: false })).toBe("/");
  });

  it("allows logged-in app visitors to stay on the app route", () => {
    expect(resolveAppRoute({ isSignedIn: true })).toBeNull();
  });

  it("redirects logged-in landing visitors to the app route", () => {
    expect(resolveLandingRoute({ isSignedIn: true })).toBe("/app");
  });

  it("allows logged-out landing visitors to see the landing page", () => {
    expect(resolveLandingRoute({ isSignedIn: false })).toBeNull();
  });
});


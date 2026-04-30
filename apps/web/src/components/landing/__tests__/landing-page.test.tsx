import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { LandingPage } from "@/components/landing/landing-page";

describe("LandingPage", () => {
  it("renders for logged-out visitors with a visible primary CTA", () => {
    render(<LandingPage />);

    expect(
      screen.getByRole("heading", { name: /Investigate spreadsheets with evidence/i }),
    ).toBeVisible();
    expect(screen.getAllByRole("link", { name: /Start an investigation/i })[0]).toHaveAttribute(
      "href",
      "/sign-up",
    );
  });
});


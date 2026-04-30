import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { AppShell, AuthenticatedAppShell } from "@/components/app-shell/app-shell";

const authMocks = vi.hoisted(() => ({
  getToken: vi.fn(async () => "clerk_token_123"),
}));

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    getToken: authMocks.getToken,
  }),
}));

function mockChatsResponse(chats: unknown[] = []) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () =>
      Response.json({
        data: chats,
        pagination: { next_cursor: null },
      }),
    ),
  );
}

describe("AppShell", () => {
  it("renders the central chat area", async () => {
    mockChatsResponse();

    render(<AppShell />);

    expect(screen.getByRole("heading", { name: /Central chat canvas/i })).toBeVisible();
    await waitFor(() => expect(screen.getByText(/No previous chats yet/i)).toBeVisible());
  });

  it("links New Investigation to /app/new", () => {
    mockChatsResponse();

    render(<AppShell />);

    expect(screen.getByRole("link", { name: /New Investigation/i })).toHaveAttribute("href", "/app/new");
  });

  it("closes and reopens the right dataset panel", async () => {
    mockChatsResponse();

    render(<AppShell />);

    expect(screen.getByLabelText("Dataset panel")).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: /Close dataset panel/i }));
    expect(screen.queryByLabelText("Dataset panel")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Open dataset panel/i }));
    expect(screen.getByLabelText("Dataset panel")).toBeVisible();
  });

  it("shows the previous chats empty state when the API returns no chats", async () => {
    mockChatsResponse();

    render(<AppShell />);

    await waitFor(() => expect(screen.getByText(/No previous chats yet/i)).toBeVisible());
  });

  it("uses Clerk getToken when the authenticated shell loads protected APIs", async () => {
    const fetcher = vi.fn(
      async (...args: Parameters<typeof fetch>) => {
        void args;
        return Response.json({
          data: [],
          pagination: { next_cursor: null },
        });
      },
    );
    vi.stubGlobal("fetch", fetcher);

    render(<AuthenticatedAppShell />);

    await waitFor(() => expect(authMocks.getToken).toHaveBeenCalled());
    const headers = fetcher.mock.calls[0][1]?.headers as Headers;
    expect(headers.get("Authorization")).toBe("Bearer clerk_token_123");
  });
});

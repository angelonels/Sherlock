import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactElement } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AppShell, AuthenticatedAppShell } from "@/components/app-shell/app-shell";

const authMocks = vi.hoisted(() => ({
  getToken: vi.fn(async () => "clerk_token_123"),
  signOut: vi.fn(async () => undefined),
}));

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    getToken: authMocks.getToken,
  }),
  useClerk: () => ({
    signOut: authMocks.signOut,
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

function renderWithQueryClient(ui: ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
}

describe("AppShell", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    Object.defineProperty(window, "innerWidth", { configurable: true, value: 1280 });
  });

  it("renders the central chat area", async () => {
    mockChatsResponse();

    renderWithQueryClient(<AppShell />);

    expect(screen.getByRole("heading", { name: /Investigation desk/i })).toBeVisible();
    await waitFor(() => expect(screen.getByText(/No previous chats yet/i)).toBeVisible());
  });

  it("links New Investigation to /app/new", () => {
    mockChatsResponse();

    renderWithQueryClient(<AppShell />);

    expect(screen.getAllByRole("link", { name: /New Investigation/i })).toEqual(
      expect.arrayContaining([expect.objectContaining({ href: expect.stringContaining("/app/new") })]),
    );
  });

  it("filters recent investigations from the sidebar search", async () => {
    mockChatsResponse([
      { id: "chat_sales", dataset_id: "dataset_1", title: "Sales review", created_at: "", updated_at: "" },
      { id: "chat_costs", dataset_id: "dataset_2", title: "Cost review", created_at: "", updated_at: "" },
    ]);

    renderWithQueryClient(<AppShell />);
    await screen.findAllByText("Sales review");

    fireEvent.change(screen.getByPlaceholderText("Search investigations"), { target: { value: "cost" } });

    const sidebar = screen.getByLabelText("Recent investigations");
    expect(within(sidebar).queryByText("Sales review")).not.toBeInTheDocument();
    expect(within(sidebar).getByText("Cost review")).toBeVisible();
  });

  it("opens mobile sidebar and dataset drawers", async () => {
    Object.defineProperty(window, "innerWidth", { configurable: true, value: 390 });
    mockChatsResponse();

    renderWithQueryClient(<AppShell />);

    fireEvent.click(screen.getByRole("button", { name: /Open chat sidebar/i }));
    const mobileSidebar = screen.getByLabelText("Mobile chat sidebar");
    expect(mobileSidebar).toBeVisible();
    fireEvent.click(within(mobileSidebar).getByRole("button", { name: /Close chat sidebar/i }));
    expect(screen.queryByLabelText("Mobile chat sidebar")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /Open dataset panel/i }));
    expect(screen.getByLabelText("Mobile dataset panel")).toBeVisible();
  });

  it("closes and reopens the right dataset panel", async () => {
    mockChatsResponse();

    renderWithQueryClient(<AppShell />);

    expect(screen.getByLabelText("Dataset panel")).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: /Close dataset panel/i }));
    expect(screen.queryByLabelText("Dataset panel")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Open dataset panel/i }));
    expect(screen.getByLabelText("Dataset panel")).toBeVisible();
  });

  it("closes and reopens the left chat sidebar", async () => {
    mockChatsResponse();

    renderWithQueryClient(<AppShell />);

    expect(screen.getByLabelText("Chat sidebar")).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: /Close chat sidebar/i }));
    expect(screen.queryByLabelText("Chat sidebar")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Open chat sidebar/i }));
    expect(screen.getByLabelText("Chat sidebar")).toBeVisible();
  });

  it("shows the previous chats empty state when the API returns no chats", async () => {
    mockChatsResponse();

    renderWithQueryClient(<AppShell />);

    await waitFor(() => expect(screen.getByText(/No previous chats yet/i)).toBeVisible());
  });

  it("signs out from the chat sidebar", async () => {
    vi.stubEnv("NEXT_PUBLIC_AUTH_BYPASS", "false");
    vi.stubEnv("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY", "pk_test_fake");
    mockChatsResponse();

    renderWithQueryClient(<AuthenticatedAppShell />);

    fireEvent.click(screen.getByRole("button", { name: /Log out/i }));

    await waitFor(() => expect(authMocks.signOut).toHaveBeenCalledWith({ redirectUrl: "/" }));
  });

  it("uses Clerk getToken when the authenticated shell loads protected APIs", async () => {
    vi.stubEnv("NEXT_PUBLIC_AUTH_BYPASS", "false");
    vi.stubEnv("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY", "pk_test_fake");
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

    renderWithQueryClient(<AuthenticatedAppShell />);

    await waitFor(() => expect(authMocks.getToken).toHaveBeenCalled());
    const headers = fetcher.mock.calls[0][1]?.headers as Headers;
    expect(headers.get("Authorization")).toBe("Bearer clerk_token_123");
  });
});

"use client";

import { SherlockConversation, SherlockMessage } from "@/components/ai/sherlock-ai";
import { isAuthBypassEnabled, isClerkConfigured } from "@/features/auth/auth-config";
import { DatasetPreviewTab, DatasetQualityTab, DatasetSchemaTab } from "@/features/datasets/dataset-tabs";
import { ChatCanvas } from "@/features/chat/chat-canvas";
import { UploadSessionStep } from "@/features/upload/upload-session-step";
import { ApiClient } from "@/lib/api-client";
import type { ChatSummary } from "@/lib/types";
import { Sheet, SheetContent, SheetDescription, SheetTitle } from "@/components/ui/sheet";
import { useAuth, useClerk } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";
import {
  FileSpreadsheet,
  LogOut,
  Menu,
  MessageSquareText,
  PanelLeftOpen,
  PanelRight,
  PanelRightOpen,
  Plus,
  RefreshCw,
  Search,
  UserRound,
  X,
} from "lucide-react";
import Link from "next/link";
import { useMemo, useState, type PointerEvent } from "react";

type AppShellProps = {
  activeView?: "home" | "new" | "chat";
  chatId?: string;
  getToken?: () => Promise<string | null> | string | null;
  onSignOut?: () => void;
};

type SidebarContentProps = {
  chats: ChatSummary[];
  isLoadingChats: boolean;
  onSignOut: () => void;
  onClose?: () => void;
};

type DatasetPanelProps = {
  apiClient: ApiClient;
  datasetId: string | null;
  onClose?: () => void;
};

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

function SidebarContent({ chats, isLoadingChats, onSignOut, onClose }: SidebarContentProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const filteredChats = chats.filter((chat) =>
    chat.title.toLocaleLowerCase().includes(searchQuery.trim().toLocaleLowerCase()),
  );

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between gap-3">
        <Link href="/app" className="flex items-center gap-3" onClick={onClose}>
          <span className="grid size-9 place-items-center border border-[#241f1a] bg-[#241f1a] text-[#fffaf7] shadow-[3px_3px_0_#d2c3b3]">
            <FileSpreadsheet size={18} />
          </span>
          <span className="text-lg font-semibold tracking-[-0.03em]">Sherlock</span>
        </Link>
        {onClose ? (
          <button
            type="button"
            onClick={onClose}
            className="inline-flex size-9 items-center justify-center border border-[#d9cdbf] bg-[#fffaf7] text-[#51473f]"
            aria-label="Close chat sidebar"
          >
            <X size={17} />
          </button>
        ) : null}
      </div>

      <Link
        href="/app/new"
        onClick={onClose}
        className="mt-8 inline-flex h-11 w-full items-center justify-center gap-2 border border-[#241f1a] bg-[#241f1a] px-3 text-sm font-semibold text-[#fffaf7] transition-colors hover:bg-[#3b332d] focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-[#b56b32]/25"
      >
        <Plus size={17} />
        New Investigation
      </Link>

      <section className="mt-8 min-h-0 flex-1" aria-label="Recent investigations">
        <div className="flex items-center gap-2 text-sm font-semibold text-[#51473f]">
          <MessageSquareText size={16} />
          Recent investigations
        </div>
        <label className="relative mt-3 block">
          <span className="sr-only">Search investigations</span>
          <Search className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[#8b7d70]" size={15} />
          <input
            type="search"
            value={searchQuery}
            onChange={(event) => setSearchQuery(event.target.value)}
            placeholder="Search investigations"
            className="h-10 w-full border border-[#d9cdbf] bg-[#fffaf7] pl-9 pr-3 text-sm outline-none focus:border-[#241f1a]"
          />
        </label>
        <div className="mt-3 space-y-2 overflow-y-auto pb-4">
          {isLoadingChats ? (
            <p className="border border-[#d9cdbf] bg-[#fffaf7]/70 px-3 py-3 text-sm text-[#655c52]">Loading chats</p>
          ) : chats.length === 0 ? (
            <p className="border border-[#d9cdbf] bg-[#fffaf7]/70 px-3 py-3 text-sm text-[#655c52]">
              No previous chats yet.
            </p>
          ) : filteredChats.length === 0 ? (
            <p className="border border-[#d9cdbf] bg-[#fffaf7]/70 px-3 py-3 text-sm text-[#655c52]">
              No investigations match this search.
            </p>
          ) : (
            filteredChats.map((chat) => (
              <Link
                key={chat.id}
                href={`/app/chat/${chat.id}`}
                onClick={onClose}
                className="block border border-[#d9cdbf] bg-[#fffaf7]/70 px-3 py-3 text-sm font-medium text-[#51473f]"
              >
                {chat.title}
              </Link>
            ))
          )}
        </div>
      </section>

      <div className="mt-4 border-t border-[#d9cdbf] pt-4">
        <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase text-[#8b7d70]">
          <UserRound size={15} />
          Account
        </div>
        <button
          type="button"
          onClick={onSignOut}
          className="inline-flex h-11 w-full items-center justify-center gap-2 border border-[#d9cdbf] bg-[#fffaf7] px-3 text-sm font-semibold text-[#51473f] transition-colors hover:border-[#241f1a] hover:text-[#241f1a] focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-[#b56b32]/25"
        >
          <LogOut size={16} />
          Log out
        </button>
      </div>
    </div>
  );
}

export function DatasetPanel({ apiClient, datasetId, onClose }: DatasetPanelProps) {
  const [activeTab, setActiveTab] = useState<"preview" | "schema" | "quality">("preview");
  const [previewAppend, setPreviewAppend] = useState<{
    datasetId: string | null;
    rows: Record<string, unknown>[];
    cursor: string | null;
  }>({ datasetId: null, rows: [], cursor: null });
  const [isLoadingNext, setIsLoadingNext] = useState(false);
  const [nextPageError, setNextPageError] = useState<string | null>(null);
  const panelQuery = useQuery({
    queryKey: ["dataset-panel", datasetId],
    enabled: Boolean(datasetId),
    retry: false,
    queryFn: async () => {
      if (!datasetId) {
        throw new Error("Dataset is not selected.");
      }
      const [preview, schema, quality] = await Promise.all([
        apiClient.getDatasetPreview(datasetId),
        apiClient.getDatasetColumns(datasetId),
        apiClient.getDatasetQualityIssues(datasetId),
      ]);
      return { preview, schema, quality };
    },
  });

  const basePreviewRows = panelQuery.data?.preview.data ?? [];
  const basePreviewCursor = panelQuery.data?.preview.pagination.next_cursor ?? null;
  const appendedRows = previewAppend.datasetId === datasetId ? previewAppend.rows : [];
  const previewRows = [...basePreviewRows, ...appendedRows];
  const previewCursor = previewAppend.datasetId === datasetId ? previewAppend.cursor : basePreviewCursor;

  async function loadNextPreviewRows() {
    if (!datasetId || !previewCursor) {
      return;
    }
    setIsLoadingNext(true);
    setNextPageError(null);
    try {
      const next = await apiClient.getDatasetPreview(datasetId, previewCursor);
      setPreviewAppend((current) => ({
        datasetId,
        rows: current.datasetId === datasetId ? [...current.rows, ...next.data] : next.data,
        cursor: next.pagination.next_cursor,
      }));
    } catch (error) {
      setNextPageError(error instanceof Error ? error.message : "Could not load more preview rows.");
    } finally {
      setIsLoadingNext(false);
    }
  }

  return (
    <div className="flex h-full min-h-0 flex-col" aria-label="Dataset panel">
      <div className="flex items-center justify-between gap-3">
        <p className="font-mono text-xs uppercase tracking-[0.18em] text-[#8f6a4e]">Dataset</p>
        {onClose ? (
          <button
            type="button"
            onClick={onClose}
            className="inline-flex size-9 items-center justify-center border border-[#d9cdbf] bg-[#fffaf7] text-[#51473f]"
            aria-label="Close dataset panel"
          >
            <X size={17} />
          </button>
        ) : null}
      </div>

      <div className="mt-4 grid grid-cols-3 gap-1">
        {(["preview", "schema", "quality"] as const).map((tab) => (
          <button
            key={tab}
            type="button"
            onClick={() => setActiveTab(tab)}
            className={[
              "h-10 border px-2 text-xs font-semibold capitalize",
              activeTab === tab
                ? "border-[#241f1a] bg-[#241f1a] text-[#fffaf7]"
                : "border-[#d9cdbf] bg-[#fffaf7]/70 text-[#51473f]",
            ].join(" ")}
          >
            {tab}
          </button>
        ))}
      </div>

      <div className="mt-4 min-h-0 flex-1 overflow-y-auto">
        {!datasetId ? (
          <p className="border border-[#d9cdbf] bg-[#fffaf7]/70 px-3 py-3 text-sm text-[#655c52]">
            Open a dataset-backed investigation to inspect preview rows, schema, and quality notes.
          </p>
        ) : panelQuery.isLoading ? (
          <p className="border border-[#d9cdbf] bg-[#fffaf7]/70 px-3 py-3 text-sm text-[#655c52]">
            Loading dataset context
          </p>
        ) : panelQuery.error ? (
          <div className="border border-[#b84b3c] bg-[#fff2ef] px-3 py-3 text-sm text-[#7d2f26]" role="alert">
            <p>{panelQuery.error instanceof Error ? panelQuery.error.message : "Dataset panel failed to load."}</p>
            <button
              type="button"
              onClick={() => void panelQuery.refetch()}
              className="mt-3 inline-flex h-9 items-center gap-2 border border-[#b84b3c] bg-[#fffaf7] px-3 font-semibold"
            >
              <RefreshCw size={14} />
              Retry
            </button>
          </div>
        ) : activeTab === "preview" ? (
          <>
            <DatasetPreviewTab
              rows={previewRows}
              hasNextPage={Boolean(previewCursor)}
              isLoadingNext={isLoadingNext}
              onLoadNext={() => void loadNextPreviewRows()}
            />
            {nextPageError ? <p className="mt-3 text-sm text-[#7d2f26]" role="alert">{nextPageError}</p> : null}
          </>
        ) : activeTab === "schema" ? (
          <DatasetSchemaTab columns={panelQuery.data?.schema.data ?? []} />
        ) : (
          <DatasetQualityTab issues={panelQuery.data?.quality.data ?? []} />
        )}
      </div>
    </div>
  );
}

export function AuthenticatedAppShell(props: Omit<AppShellProps, "getToken">) {
  if (isAuthBypassEnabled()) {
    return <AppShell {...props} getToken={() => null} />;
  }
  if (!isClerkConfigured()) {
    return null;
  }

  return <ClerkAuthenticatedAppShell {...props} />;
}

function ClerkAuthenticatedAppShell(props: Omit<AppShellProps, "getToken">) {
  const { getToken } = useAuth();
  const { signOut } = useClerk();
  return <AppShell {...props} getToken={getToken} onSignOut={() => void signOut({ redirectUrl: "/" })} />;
}

export function AppShell({ activeView = "home", chatId, getToken, onSignOut }: AppShellProps) {
  const [isChatSidebarOpen, setIsChatSidebarOpen] = useState(true);
  const [isDatasetPanelOpen, setIsDatasetPanelOpen] = useState(true);
  const [isMobileChatDrawerOpen, setIsMobileChatDrawerOpen] = useState(false);
  const [isMobileDatasetDrawerOpen, setIsMobileDatasetDrawerOpen] = useState(false);
  const [chatSidebarWidth, setChatSidebarWidth] = useState(288);
  const [datasetPanelWidth, setDatasetPanelWidth] = useState(360);
  const [activeDatasetId, setActiveDatasetId] = useState<string | null>(null);
  const apiClient = useMemo(() => new ApiClient({ getToken }), [getToken]);
  const {
    data: chatsResponse,
    isLoading: isLoadingChats,
    refetch: refreshChats,
  } = useQuery({
    queryKey: ["chats"],
    queryFn: () => apiClient.listChats(),
    retry: false,
  });
  const chats: ChatSummary[] = chatsResponse?.data ?? [];
  const handleSignOut = onSignOut ?? (() => window.location.assign("/"));

  function startPanelResize(side: "chat" | "dataset", event: PointerEvent<HTMLDivElement>) {
    event.preventDefault();
    const startX = event.clientX;
    const startWidth = side === "chat" ? chatSidebarWidth : datasetPanelWidth;

    function handlePointerMove(moveEvent: globalThis.PointerEvent) {
      if (side === "chat") {
        setChatSidebarWidth(clamp(startWidth + moveEvent.clientX - startX, 232, 440));
      } else {
        setDatasetPanelWidth(clamp(startWidth - (moveEvent.clientX - startX), 280, 560));
      }
    }

    function stopPanelResize() {
      window.removeEventListener("pointermove", handlePointerMove);
      window.removeEventListener("pointerup", stopPanelResize);
    }

    window.addEventListener("pointermove", handlePointerMove);
    window.addEventListener("pointerup", stopPanelResize, { once: true });
  }

  function isDesktopViewport() {
    return typeof window !== "undefined" ? window.innerWidth >= 1024 : true;
  }

  const showDesktopToolbar = !isChatSidebarOpen || !isDatasetPanelOpen;

  return (
    <main className="min-h-dvh bg-[#f7f3ec] text-[#241f1a]">
      <div className="flex min-h-dvh">
        {isChatSidebarOpen ? (
          <>
            <aside
              className="hidden shrink-0 border-r border-[#ddd2c4] bg-[#efe6da] p-5 lg:block"
              style={{ width: chatSidebarWidth }}
              aria-label="Chat sidebar"
            >
              <SidebarContent
                chats={chats}
                isLoadingChats={isLoadingChats}
                onSignOut={handleSignOut}
                onClose={() => setIsChatSidebarOpen(false)}
              />
            </aside>
            <div
              className="hidden w-1 cursor-col-resize bg-transparent transition-colors hover:bg-[#b8aa9a] lg:block"
              role="separator"
              aria-label="Resize chat sidebar"
              onPointerDown={(event) => startPanelResize("chat", event)}
            />
          </>
        ) : null}

        <SherlockConversation className="flex min-h-dvh min-w-0 flex-1 flex-col bg-[#fbf7f1]">
          <header
            className={[
              "flex items-center justify-between gap-3 border-b border-[#ddd2c4] px-4 py-3 sm:px-5",
              showDesktopToolbar ? "lg:flex" : "lg:hidden",
            ].join(" ")}
          >
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => {
                  setIsChatSidebarOpen(true);
                  if (!isDesktopViewport()) {
                    setIsMobileChatDrawerOpen(true);
                  }
                }}
                className="inline-flex size-10 items-center justify-center border border-[#d9cdbf] bg-[#fffaf7] text-[#51473f]"
                aria-label="Open chat sidebar"
              >
                {isChatSidebarOpen ? <Menu size={18} /> : <PanelLeftOpen size={18} />}
              </button>
              <Link href="/app" className="text-base font-semibold tracking-[-0.03em] lg:hidden">
                Sherlock
              </Link>
            </div>
            <button
              type="button"
              onClick={() => {
                setIsDatasetPanelOpen(true);
                if (!isDesktopViewport()) {
                  setIsMobileDatasetDrawerOpen(true);
                }
              }}
              className="inline-flex size-10 items-center justify-center border border-[#d9cdbf] bg-[#fffaf7] text-[#51473f]"
              aria-label="Open dataset panel"
            >
              {isDatasetPanelOpen ? <PanelRight size={18} /> : <PanelRightOpen size={18} />}
            </button>
          </header>

          <div className={activeView === "new" || activeView === "chat" ? "min-h-0 flex-1 px-4 sm:px-5" : "grid flex-1 place-items-center px-4 py-8 sm:px-5"}>
            {activeView === "new" ? (
              <UploadSessionStep apiClient={apiClient} onDatasetReady={setActiveDatasetId} />
            ) : activeView === "chat" && chatId ? (
              <ChatCanvas
                apiClient={apiClient}
                chatId={chatId}
                onDatasetContext={setActiveDatasetId}
                onChatUpdated={() => void refreshChats()}
              />
            ) : (
              <section className="w-full max-w-4xl py-8" aria-label="Investigation hub">
                <div className="flex flex-col gap-4 border-b border-[#d9cdbf] pb-6 sm:flex-row sm:items-end sm:justify-between">
                  <div>
                    <p className="font-mono text-xs uppercase text-[#8f6a4e]">Workspace</p>
                    <h1 className="mt-2 text-2xl font-semibold">Investigation desk</h1>
                    <p className="mt-2 text-sm text-[#655c52]">Upload a spreadsheet or reopen an evidence-backed investigation.</p>
                  </div>
                  <Link href="/app/new" className="inline-flex h-11 items-center justify-center gap-2 border border-[#241f1a] bg-[#241f1a] px-4 text-sm font-semibold text-[#fffaf7]">
                    <Plus size={16} />
                    New Investigation
                  </Link>
                </div>
                {chats.length === 0 ? (
                  <SherlockMessage className="mt-6 border border-[#d9cdbf] bg-[#fffaf7] p-5">
                    <FileSpreadsheet size={20} />
                    <h2 className="mt-4 text-lg font-semibold">Start with a CSV or XLSX file</h2>
                    <p className="mt-2 max-w-xl text-sm leading-6 text-[#655c52]">
                      Sherlock will inspect the upload, surface quality issues, and let you review the dataset before opening a chat.
                    </p>
                    <Link href="/app/new" className="mt-5 inline-flex h-10 items-center gap-2 border border-[#241f1a] px-3 text-sm font-semibold">
                      Upload dataset
                      <PanelRightOpen size={15} />
                    </Link>
                  </SherlockMessage>
                ) : (
                  <div className="mt-6">
                    <h2 className="text-sm font-semibold text-[#51473f]">Recent investigations</h2>
                    <div className="mt-3 divide-y divide-[#eee4d8] border border-[#d9cdbf] bg-[#fffaf7]">
                      {chats.slice(0, 6).map((chat) => (
                        <Link key={chat.id} href={`/app/chat/${chat.id}`} className="flex items-center justify-between gap-4 px-4 py-3 text-sm font-medium">
                          <span className="truncate">{chat.title}</span>
                          <PanelRightOpen className="shrink-0 text-[#8b7d70]" size={15} />
                        </Link>
                      ))}
                    </div>
                  </div>
                )}
              </section>
            )}
          </div>
        </SherlockConversation>

        {isDatasetPanelOpen ? (
          <>
            <div
              className="hidden w-1 cursor-col-resize bg-transparent transition-colors hover:bg-[#b8aa9a] lg:block"
              role="separator"
              aria-label="Resize dataset panel"
              onPointerDown={(event) => startPanelResize("dataset", event)}
            />
            <aside
              className="hidden shrink-0 border-l border-[#ddd2c4] bg-[#efe6da] p-5 lg:block"
              style={{ width: datasetPanelWidth }}
            >
              <DatasetPanel apiClient={apiClient} datasetId={activeDatasetId} onClose={() => setIsDatasetPanelOpen(false)} />
            </aside>
          </>
        ) : null}
      </div>

      <Sheet open={isMobileChatDrawerOpen} onOpenChange={setIsMobileChatDrawerOpen}>
        <SheetContent
          side="left"
          showCloseButton={false}
          className="w-[min(22rem,88vw)] border-r border-[#ddd2c4] bg-[#efe6da] p-5 lg:hidden"
          aria-label="Mobile chat sidebar"
        >
          <SheetTitle className="sr-only">Investigations</SheetTitle>
          <SheetDescription className="sr-only">Recent investigations and account controls.</SheetDescription>
          <div className="h-full">
            <SidebarContent
              chats={chats}
              isLoadingChats={isLoadingChats}
              onSignOut={handleSignOut}
              onClose={() => setIsMobileChatDrawerOpen(false)}
            />
          </div>
        </SheetContent>
      </Sheet>

      <Sheet open={isMobileDatasetDrawerOpen} onOpenChange={setIsMobileDatasetDrawerOpen}>
        <SheetContent
          side="right"
          showCloseButton={false}
          className="w-[min(24rem,90vw)] border-l border-[#ddd2c4] bg-[#efe6da] p-5 lg:hidden"
          aria-label="Mobile dataset panel"
        >
          <SheetTitle className="sr-only">Dataset inspector</SheetTitle>
          <SheetDescription className="sr-only">Preview, schema, and quality details for the active dataset.</SheetDescription>
          <div className="h-full">
            <DatasetPanel
              apiClient={apiClient}
              datasetId={activeDatasetId}
              onClose={() => setIsMobileDatasetDrawerOpen(false)}
            />
          </div>
        </SheetContent>
      </Sheet>
    </main>
  );
}

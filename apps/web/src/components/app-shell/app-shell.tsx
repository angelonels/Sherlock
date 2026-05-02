"use client";

import { SherlockConversation, SherlockMessage, SherlockThinkingState } from "@/components/ai/sherlock-ai";
import { DatasetPreviewTab, DatasetQualityTab, DatasetSchemaTab } from "@/features/datasets/dataset-tabs";
import { ChatCanvas } from "@/features/chat/chat-canvas";
import { UploadSessionStep } from "@/features/upload/upload-session-step";
import { ApiClient } from "@/lib/api-client";
import type { ChatSummary, DatasetColumn, DatasetQualityIssue } from "@/lib/types";
import { useAuth } from "@clerk/nextjs";
import {
  FileSpreadsheet,
  Menu,
  MessageSquareText,
  PanelLeftOpen,
  PanelRight,
  PanelRightOpen,
  Plus,
  X,
} from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useMemo, useState, type PointerEvent } from "react";

type AppShellProps = {
  activeView?: "home" | "new" | "chat";
  chatId?: string;
  getToken?: () => Promise<string | null> | string | null;
};

type SidebarContentProps = {
  chats: ChatSummary[];
  isLoadingChats: boolean;
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

function SidebarContent({ chats, isLoadingChats, onClose }: SidebarContentProps) {
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

      <section className="mt-8 min-h-0 flex-1" aria-label="Previous chats">
        <div className="flex items-center gap-2 text-sm font-semibold text-[#51473f]">
          <MessageSquareText size={16} />
          Previous chats
        </div>
        <div className="mt-3 space-y-2 overflow-y-auto pb-4">
          {isLoadingChats ? (
            <p className="border border-[#d9cdbf] bg-[#fffaf7]/70 px-3 py-3 text-sm text-[#655c52]">Loading chats</p>
          ) : chats.length === 0 ? (
            <p className="border border-[#d9cdbf] bg-[#fffaf7]/70 px-3 py-3 text-sm text-[#655c52]">
              No previous chats yet.
            </p>
          ) : (
            chats.map((chat) => (
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
    </div>
  );
}

function DatasetPanel({ apiClient, datasetId, onClose }: DatasetPanelProps) {
  const [activeTab, setActiveTab] = useState<"preview" | "schema" | "quality">("preview");
  const [previewRows, setPreviewRows] = useState<Record<string, unknown>[]>([]);
  const [previewCursor, setPreviewCursor] = useState<string | null>(null);
  const [columns, setColumns] = useState<DatasetColumn[]>([]);
  const [issues, setIssues] = useState<DatasetQualityIssue[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    async function loadDatasetPanel() {
      if (!datasetId) {
        setPreviewRows([]);
        setPreviewCursor(null);
        setColumns([]);
        setIssues([]);
        return;
      }

      setIsLoading(true);
      setError(null);
      try {
        const [preview, schema, quality] = await Promise.all([
          apiClient.getDatasetPreview(datasetId),
          apiClient.getDatasetColumns(datasetId),
          apiClient.getDatasetQualityIssues(datasetId),
        ]);
        if (!mounted) {
          return;
        }
        setPreviewRows(preview.data);
        setPreviewCursor(preview.pagination.next_cursor);
        setColumns(schema.data);
        setIssues(quality.data);
      } catch (panelError) {
        if (mounted) {
          setError(panelError instanceof Error ? panelError.message : "Dataset panel failed to load.");
        }
      } finally {
        if (mounted) {
          setIsLoading(false);
        }
      }
    }

    void loadDatasetPanel();

    return () => {
      mounted = false;
    };
  }, [apiClient, datasetId]);

  async function loadNextPreviewRows() {
    if (!datasetId || !previewCursor) {
      return;
    }
    const next = await apiClient.getDatasetPreview(datasetId, previewCursor);
    setPreviewRows((rows) => [...rows, ...next.data]);
    setPreviewCursor(next.pagination.next_cursor);
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
        ) : isLoading ? (
          <p className="border border-[#d9cdbf] bg-[#fffaf7]/70 px-3 py-3 text-sm text-[#655c52]">
            Loading dataset context
          </p>
        ) : error ? (
          <p className="border border-[#b84b3c] bg-[#fff2ef] px-3 py-3 text-sm text-[#7d2f26]" role="alert">
            {error}
          </p>
        ) : activeTab === "preview" ? (
          <DatasetPreviewTab
            rows={previewRows}
            hasNextPage={Boolean(previewCursor)}
            onLoadNext={() => void loadNextPreviewRows()}
          />
        ) : activeTab === "schema" ? (
          <DatasetSchemaTab columns={columns} />
        ) : (
          <DatasetQualityTab issues={issues} />
        )}
      </div>
    </div>
  );
}

export function AuthenticatedAppShell(props: Omit<AppShellProps, "getToken">) {
  const { getToken } = useAuth();

  return <AppShell {...props} getToken={getToken} />;
}

export function AppShell({ activeView = "home", chatId, getToken }: AppShellProps) {
  const [isChatSidebarOpen, setIsChatSidebarOpen] = useState(true);
  const [isDatasetPanelOpen, setIsDatasetPanelOpen] = useState(true);
  const [isMobileChatDrawerOpen, setIsMobileChatDrawerOpen] = useState(false);
  const [isMobileDatasetDrawerOpen, setIsMobileDatasetDrawerOpen] = useState(false);
  const [chatSidebarWidth, setChatSidebarWidth] = useState(288);
  const [datasetPanelWidth, setDatasetPanelWidth] = useState(360);
  const [activeDatasetId, setActiveDatasetId] = useState<string | null>(null);
  const [chats, setChats] = useState<ChatSummary[]>([]);
  const [isLoadingChats, setIsLoadingChats] = useState(true);
  const apiClient = useMemo(() => new ApiClient({ getToken }), [getToken]);

  const refreshChats = useCallback(async () => {
    setIsLoadingChats(true);
    try {
      const response = await apiClient.listChats();
      setChats(response.data);
    } catch {
      setChats([]);
    } finally {
      setIsLoadingChats(false);
    }
  }, [apiClient]);

  useEffect(() => {
    queueMicrotask(() => {
      void refreshChats();
    });
  }, [refreshChats]);

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
              <SidebarContent chats={chats} isLoadingChats={isLoadingChats} onClose={() => setIsChatSidebarOpen(false)} />
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
              <SherlockMessage className="w-full max-w-2xl border border-[#d9cdbf] bg-[#fffaf7] p-5">
                <h1 className="text-2xl font-semibold tracking-[-0.05em]">Investigation desk</h1>
                <p className="mt-3 text-sm leading-6 text-[#655c52]">
                  Start a new investigation or reopen a previous chat from the sidebar.
                </p>
                <SherlockThinkingState className="mt-5 flex items-center gap-2" />
              </SherlockMessage>
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

      {isMobileChatDrawerOpen ? (
        <div className="fixed inset-0 z-40 bg-[#241f1a]/35 lg:hidden" onClick={() => setIsMobileChatDrawerOpen(false)}>
          <aside
            className="h-full w-[min(22rem,88vw)] border-r border-[#ddd2c4] bg-[#efe6da] p-5"
            onClick={(event) => event.stopPropagation()}
            aria-label="Mobile chat sidebar"
          >
            <SidebarContent
              chats={chats}
              isLoadingChats={isLoadingChats}
              onClose={() => setIsMobileChatDrawerOpen(false)}
            />
          </aside>
        </div>
      ) : null}

      {isMobileDatasetDrawerOpen ? (
        <div className="fixed inset-0 z-40 bg-[#241f1a]/35 lg:hidden" onClick={() => setIsMobileDatasetDrawerOpen(false)}>
          <aside
            className="ml-auto h-full w-[min(24rem,90vw)] border-l border-[#ddd2c4] bg-[#efe6da] p-5"
            onClick={(event) => event.stopPropagation()}
          >
            <DatasetPanel
              apiClient={apiClient}
              datasetId={activeDatasetId}
              onClose={() => setIsMobileDatasetDrawerOpen(false)}
            />
          </aside>
        </div>
      ) : null}
    </main>
  );
}

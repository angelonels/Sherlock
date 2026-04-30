"use client";

import {
  SherlockConversation,
  SherlockMessage,
  SherlockPromptComposer,
  SherlockSuggestions,
  SherlockThinkingState,
} from "@/components/ai/sherlock-ai";
import { useAuth } from "@clerk/nextjs";
import { ChatCanvas } from "@/features/chat/chat-canvas";
import { UploadSessionStep } from "@/features/upload/upload-session-step";
import { ApiClient } from "@/lib/api-client";
import type { ChatSummary } from "@/lib/types";
import { FileSpreadsheet, MessageSquareText, PanelRight, Plus, X } from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

type AppShellProps = {
  activeView?: "home" | "new" | "chat";
  chatId?: string;
  getToken?: () => Promise<string | null> | string | null;
};

export function AuthenticatedAppShell(props: Omit<AppShellProps, "getToken">) {
  const { getToken } = useAuth();

  return <AppShell {...props} getToken={getToken} />;
}

export function AppShell({ activeView = "home", chatId, getToken }: AppShellProps) {
  const [isDatasetPanelOpen, setIsDatasetPanelOpen] = useState(true);
  const [chats, setChats] = useState<ChatSummary[]>([]);
  const [isLoadingChats, setIsLoadingChats] = useState(true);
  const apiClient = useMemo(() => new ApiClient({ getToken }), [getToken]);

  useEffect(() => {
    let isMounted = true;

    apiClient
      .listChats()
      .then((response) => {
        if (isMounted) {
          setChats(response.data);
        }
      })
      .catch(() => {
        if (isMounted) {
          setChats([]);
        }
      })
      .finally(() => {
        if (isMounted) {
          setIsLoadingChats(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [apiClient]);

  const title =
    activeView === "new" ? "New investigation" : activeView === "chat" ? "Open investigation" : "Investigation desk";

  return (
    <main className="min-h-dvh bg-[#f7f3ec] text-[#241f1a]">
      <div
        className={[
          "grid min-h-dvh",
          isDatasetPanelOpen
            ? "lg:grid-cols-[17rem_minmax(0,1fr)_20rem]"
            : "lg:grid-cols-[17rem_minmax(0,1fr)]",
        ].join(" ")}
      >
        <aside className="border-b border-[#ddd2c4] bg-[#efe6da] p-4 sm:p-5 lg:border-b-0 lg:border-r">
          <Link href="/app" className="flex items-center gap-3">
            <span className="grid size-9 place-items-center border border-[#241f1a] bg-[#241f1a] text-[#fffaf7] shadow-[3px_3px_0_#d2c3b3]">
              <FileSpreadsheet size={18} />
            </span>
            <span className="text-lg font-semibold tracking-[-0.03em]">Sherlock</span>
          </Link>

          <Link
            href="/app/new"
            className="mt-8 inline-flex h-11 w-full items-center justify-center gap-2 border border-[#241f1a] bg-[#241f1a] px-3 text-sm font-semibold text-[#fffaf7] transition-colors hover:bg-[#3b332d] focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-[#b56b32]/25"
          >
            <Plus size={17} />
            New Investigation
          </Link>

          <section className="mt-8" aria-label="Previous chats">
            <div className="flex items-center gap-2 text-sm font-semibold text-[#51473f]">
              <MessageSquareText size={16} />
              Previous chats
            </div>
            <div className="mt-3 space-y-2">
              {isLoadingChats ? (
                <p className="border border-[#d9cdbf] bg-[#fffaf7]/70 px-3 py-3 text-sm text-[#655c52]">
                  Loading chats
                </p>
              ) : chats.length === 0 ? (
                <p className="border border-[#d9cdbf] bg-[#fffaf7]/70 px-3 py-3 text-sm text-[#655c52]">
                  No previous chats yet.
                </p>
              ) : (
                chats.map((chat) => (
                  <Link
                    key={chat.id}
                    href={`/app/chat/${chat.id}`}
                    className="block border border-[#d9cdbf] bg-[#fffaf7]/70 px-3 py-3 text-sm font-medium text-[#51473f]"
                  >
                    {chat.title}
                  </Link>
                ))
              )}
            </div>
          </section>
        </aside>

        <SherlockConversation className="flex min-h-[34rem] min-w-0 flex-col border-b border-[#ddd2c4] bg-[#fbf7f1] p-4 sm:p-5 lg:border-b-0">
          <header className="flex items-start justify-between gap-4 border-b border-[#ddd2c4] pb-4">
            <div>
              <p className="font-mono text-xs uppercase tracking-[0.18em] text-[#8f6a4e]">
                App shell
              </p>
              <h1 className="mt-2 text-2xl font-semibold tracking-[-0.05em]">{title}</h1>
              {chatId ? <p className="mt-1 text-sm text-[#655c52]">Chat ID: {chatId}</p> : null}
            </div>
            {!isDatasetPanelOpen ? (
              <button
                type="button"
                onClick={() => setIsDatasetPanelOpen(true)}
                className="inline-flex size-10 items-center justify-center border border-[#d9cdbf] bg-[#fffaf7] text-[#51473f]"
                aria-label="Open dataset panel"
              >
                <PanelRight size={18} />
              </button>
            ) : null}
          </header>

          <div className={activeView === "new" || activeView === "chat" ? "flex-1" : "grid flex-1 place-items-center py-8"}>
            {activeView === "new" ? (
              <UploadSessionStep apiClient={apiClient} />
            ) : activeView === "chat" && chatId ? (
              <ChatCanvas apiClient={apiClient} chatId={chatId} />
            ) : (
            <SherlockMessage className="w-full max-w-2xl border border-[#d9cdbf] bg-[#fffaf7] p-5">
              <h2 className="text-2xl font-semibold tracking-[-0.05em]">Central chat canvas</h2>
              <p className="mt-3 text-sm leading-6 text-[#655c52]">
                Upload, chat persistence, and analysis blocks will attach to this canvas in the next phases.
              </p>
              <SherlockThinkingState className="mt-5 flex items-center gap-2" />
              <SherlockSuggestions
                className="mt-5 grid gap-2 sm:grid-cols-2"
                suggestions={["Summarize this dataset", "Show revenue by month"]}
              />
            </SherlockMessage>
            )}
          </div>

          <SherlockPromptComposer className="border-t border-[#ddd2c4] pt-4" />
        </SherlockConversation>

        {isDatasetPanelOpen ? (
          <aside className="bg-[#efe6da] p-4 sm:p-5 lg:border-l lg:border-[#ddd2c4]" aria-label="Dataset panel">
            <div className="flex items-center justify-between gap-3">
              <p className="font-mono text-xs uppercase tracking-[0.18em] text-[#8f6a4e]">
                Dataset
              </p>
              <button
                type="button"
                onClick={() => setIsDatasetPanelOpen(false)}
                className="inline-flex size-9 items-center justify-center border border-[#d9cdbf] bg-[#fffaf7] text-[#51473f]"
                aria-label="Close dataset panel"
              >
                <X size={17} />
              </button>
            </div>
            <div className="mt-4 space-y-3">
              {["Preview", "Schema", "Quality"].map((tab) => (
                <div
                  key={tab}
                  className="h-11 border border-[#d9cdbf] bg-[#fffaf7]/70 px-3 py-3 text-sm font-medium text-[#51473f]"
                >
                  {tab}
                </div>
              ))}
            </div>
          </aside>
        ) : null}
      </div>
    </main>
  );
}

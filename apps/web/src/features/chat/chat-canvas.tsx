"use client";

import {
  Conversation,
  ConversationContent,
  ConversationScrollButton,
} from "@/components/ai-elements/conversation";
import { Message as AIMessage, MessageContent } from "@/components/ai-elements/message";
import { SherlockPromptComposer, SherlockThinkingState } from "@/components/ai/sherlock-ai";
import { BlockRenderer } from "@/features/messages/block-renderer";
import type { ApiClient } from "@/lib/api-client";
import type { Message } from "@/lib/types";
import { useQuery } from "@tanstack/react-query";
import { Loader2, RefreshCw, Send } from "lucide-react";
import { FormEvent, KeyboardEvent, useEffect, useMemo, useState } from "react";

type ChatCanvasProps = {
  apiClient: ApiClient;
  chatId: string;
  onDatasetContext?: (datasetId: string) => void;
  onChatUpdated?: () => void;
};

export function ChatCanvas({ apiClient, chatId, onDatasetContext, onChatUpdated }: ChatCanvasProps) {
  const [transientMessages, setTransientMessages] = useState<Message[]>([]);
  const [prompt, setPrompt] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [statusTone, setStatusTone] = useState<"progress" | "error">("progress");
  const contextQuery = useQuery({
    queryKey: ["chat-canvas", chatId],
    retry: false,
    queryFn: async () => {
      const loadedChat = await apiClient.getChat(chatId);
      const [loadedMessages, loadedDataset, loadedColumns, loadedIssues] = await Promise.all([
        apiClient.getMessages(chatId),
        apiClient.getDataset(loadedChat.dataset_id),
        apiClient.getDatasetColumns(loadedChat.dataset_id),
        apiClient.getDatasetQualityIssues(loadedChat.dataset_id),
      ]);
      return {
        chat: loadedChat,
        dataset: loadedDataset,
        columns: loadedColumns.data,
        issues: loadedIssues.data,
        messages: loadedMessages.data,
      };
    },
  });
  const chat = contextQuery.data?.chat ?? null;
  const dataset = contextQuery.data?.dataset ?? null;
  const columns = contextQuery.data?.columns ?? [];
  const issues = contextQuery.data?.issues ?? [];
  const messages = useMemo(() => {
    const persisted = contextQuery.data?.messages ?? [];
    const persistedIds = new Set(persisted.map((message) => message.id));
    return [...persisted, ...transientMessages.filter((message) => !persistedIds.has(message.id))].sort(
      (a, b) => a.message_index - b.message_index,
    );
  }, [contextQuery.data?.messages, transientMessages]);
  const loadError = contextQuery.error instanceof Error ? contextQuery.error.message : null;

  useEffect(() => {
    if (chat?.dataset_id) {
      onDatasetContext?.(chat.dataset_id);
    }
  }, [chat?.dataset_id, onDatasetContext]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const content = prompt.trim();
    if (!content || isSending) {
      return;
    }
    setPrompt("");
    setIsSending(true);
    setStatus(null);
    setStatusTone("progress");
    const optimistic: Message = {
      id: `optimistic-${crypto.randomUUID()}`,
      chat_session_id: chatId,
      message_index: messages.length + 1,
      role: "user",
      content,
      blocks: null,
      created_at: new Date().toISOString(),
    };
    setTransientMessages((current) => [...current, optimistic]);
    const idempotencyKey = crypto.randomUUID();
    try {
      const response = await apiClient.sendMessage(chatId, content, idempotencyKey);
      setTransientMessages((current) => current.map((message) => (message.id === optimistic.id ? response.message : message)));
      await pollAnalysisRun(response.analysis_run_id);
      await contextQuery.refetch();
      onChatUpdated?.();
    } catch (sendError) {
      setStatusTone("error");
      setStatus(sendError instanceof Error ? sendError.message : "Message failed");
    } finally {
      setIsSending(false);
    }
  }

  async function pollAnalysisRun(analysisRunId: string) {
    setStatusTone("progress");
    setStatus("queued");
    for (let index = 0; index < 120; index += 1) {
      const run = await apiClient.getAnalysisRun(analysisRunId);
      setStatus(run.current_stage ?? run.status);
      if ((run.status === "success" || run.status === "partial_success") && run.assistant_message) {
        setTransientMessages((current) => [...current.filter((message) => message.id !== run.assistant_message?.id), run.assistant_message as Message]);
        setStatus(null);
        return;
      }
      if (run.status === "success" || run.status === "partial_success") {
        await contextQuery.refetch();
        setStatus(null);
        return;
      }
      if (run.status === "failed") {
        setStatusTone("error");
        if (run.assistant_message) {
          setTransientMessages((current) => [...current.filter((message) => message.id !== run.assistant_message?.id), run.assistant_message as Message]);
          setStatus(null);
        } else {
          setStatus(run.error_message ?? "Analysis failed");
        }
        return;
      }
      if (index % 4 === 3) {
        await contextQuery.refetch();
      }
      await new Promise((resolve) => setTimeout(resolve, 500));
    }
    await contextQuery.refetch();
    setStatusTone("error");
    setStatus("Analysis is taking longer than expected. Refresh the investigation to check its latest state.");
  }

  function handlePromptKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault();
      event.currentTarget.form?.requestSubmit();
    }
  }

  return (
    <section className="mx-auto flex h-full min-h-[34rem] w-full max-w-5xl flex-col">
      <div className="sticky top-0 z-10 border-b border-[#ddd2c4] bg-[#fbf7f1]/95 py-4 backdrop-blur">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h1 className="text-xl font-semibold tracking-[-0.04em] sm:text-2xl">{chat?.title ?? "Investigation"}</h1>
          {status ? (
            <span
              className={[
                "border px-2 py-1 text-xs font-semibold",
                statusTone === "error"
                  ? "border-[#b84b3c] bg-[#fff2ef] text-[#7d2f26]"
                  : "border-[#d9cdbf] bg-[#fffaf7] text-[#655c52]",
              ].join(" ")}
              aria-label="Analysis status"
            >
              {status}
            </span>
          ) : null}
        </div>
        <p className="mt-1 text-sm text-[#655c52]">
          {dataset ? `${dataset.name} · ${dataset.row_count} rows · ${columns.length} columns · ${issues.length} quality notes` : "Loading dataset context"}
        </p>
      </div>

      <Conversation className="min-h-0">
        <ConversationContent className="gap-4 px-0 py-5 pr-1">
          {loadError ? (
            <div className="rounded-[8px] border border-[#b84b3c] bg-[#fff2ef] p-4 text-sm text-[#7d2f26]" role="alert">
              <p>{loadError}</p>
              <button
                type="button"
                onClick={() => void contextQuery.refetch()}
                className="mt-3 inline-flex h-9 items-center gap-2 border border-[#b84b3c] bg-[#fffaf7] px-3 font-semibold"
              >
                <RefreshCw size={14} />
                Retry
              </button>
            </div>
          ) : null}
          {messages.length === 0 ? <p className="border border-[#d9cdbf] bg-[#fffaf7] p-4 text-sm text-[#655c52]">Ask your first question about this dataset.</p> : null}
          {messages.map((message) => (
            <AIMessage key={message.id} from={message.role === "user" ? "user" : "assistant"}>
              <MessageContent
                className={[
                  "max-w-3xl border p-4 opacity-100 shadow-[0_1px_0_rgba(36,31,26,0.04)] transition-all duration-200 motion-safe:animate-in motion-safe:fade-in motion-safe:slide-in-from-bottom-2",
                  message.role === "user"
                    ? "border-[#241f1a] bg-[#241f1a] text-[#fffaf7]"
                    : "border-[#d9cdbf] bg-[#fffaf7] text-[#241f1a]",
                ].join(" ")}
              >
                {message.role === "assistant" && message.blocks?.length ? null : (
                  <p className="text-sm leading-6">{message.content}</p>
                )}
                {message.role === "assistant" ? <BlockRenderer blocks={message.blocks} /> : null}
              </MessageContent>
            </AIMessage>
          ))}
          {status && statusTone === "progress" ? (
            <SherlockThinkingState
              className="flex items-center gap-2 rounded-sm border border-[#d9cdbf] bg-[#fffaf7]/80 px-3 py-2 text-sm motion-safe:animate-in motion-safe:fade-in"
              label={status}
            />
          ) : status ? (
            <p className="border border-[#b84b3c] bg-[#fff2ef] px-3 py-2 text-sm text-[#7d2f26]" role="alert">
              {status}
            </p>
          ) : null}
        </ConversationContent>
        <ConversationScrollButton />
      </Conversation>

      <SherlockPromptComposer onSubmit={(event) => void handleSubmit(event)} className="sticky bottom-0 border-t border-[#ddd2c4] bg-[#fbf7f1]/95 py-4 backdrop-blur">
        <label className="sr-only" htmlFor="chat-prompt">Ask Sherlock</label>
        <div className="flex items-end gap-2 rounded-[8px] border border-[#d9cdbf] bg-[#fffaf7] p-2 shadow-[0_8px_30px_rgba(36,31,26,0.07)] transition-shadow focus-within:border-[#241f1a] focus-within:shadow-[0_12px_36px_rgba(36,31,26,0.10)]">
          <textarea
            id="chat-prompt"
            value={prompt}
            onChange={(event) => setPrompt(event.target.value)}
            onKeyDown={handlePromptKeyDown}
            placeholder="Ask about rows, columns, quality, trends, or totals"
            className="max-h-40 min-h-12 flex-1 resize-none bg-transparent px-2 py-2 text-sm outline-none placeholder:text-[#9a8d80]"
          />
          <button type="submit" disabled={isSending || !prompt.trim()} className="inline-flex size-10 shrink-0 items-center justify-center rounded-[8px] border border-[#241f1a] bg-[#241f1a] text-[#fffaf7] transition-colors hover:bg-[#3b332d] disabled:opacity-60" aria-label="Send message">
            {isSending ? <Loader2 className="animate-spin" size={17} /> : <Send size={17} />}
          </button>
        </div>
      </SherlockPromptComposer>
    </section>
  );
}

"use client";

import { BlockRenderer } from "@/features/messages/block-renderer";
import type { ApiClient } from "@/lib/api-client";
import type { Chat, Dataset, DatasetColumn, DatasetQualityIssue, Message } from "@/lib/types";
import { Loader2, Send } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";

type ChatCanvasProps = {
  apiClient: ApiClient;
  chatId: string;
  onDatasetContext?: (datasetId: string) => void;
  onChatUpdated?: () => void;
};

export function ChatCanvas({ apiClient, chatId, onDatasetContext, onChatUpdated }: ChatCanvasProps) {
  const [chat, setChat] = useState<Chat | null>(null);
  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [columns, setColumns] = useState<DatasetColumn[]>([]);
  const [issues, setIssues] = useState<DatasetQualityIssue[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [prompt, setPrompt] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [status, setStatus] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    async function load() {
      const loadedChat = await apiClient.getChat(chatId);
      const [loadedMessages, loadedDataset, loadedColumns, loadedIssues] = await Promise.all([
        apiClient.getMessages(chatId),
        apiClient.getDataset(loadedChat.dataset_id),
        apiClient.getDatasetColumns(loadedChat.dataset_id),
        apiClient.getDatasetQualityIssues(loadedChat.dataset_id),
      ]);
      if (!mounted) return;
      setChat(loadedChat);
      setMessages(loadedMessages.data);
      setDataset(loadedDataset);
      setColumns(loadedColumns.data);
      setIssues(loadedIssues.data);
      onDatasetContext?.(loadedChat.dataset_id);
    }
    void load();
    return () => {
      mounted = false;
    };
  }, [apiClient, chatId, onDatasetContext]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const content = prompt.trim();
    if (!content || isSending) {
      return;
    }
    setPrompt("");
    setIsSending(true);
    const optimistic: Message = {
      id: `optimistic-${crypto.randomUUID()}`,
      chat_session_id: chatId,
      message_index: messages.length + 1,
      role: "user",
      content,
      blocks: null,
      created_at: new Date().toISOString(),
    };
    setMessages((current) => [...current, optimistic]);
    const idempotencyKey = crypto.randomUUID();
    try {
      const response = await apiClient.sendMessage(chatId, content, idempotencyKey);
      setMessages((current) => current.map((message) => (message.id === optimistic.id ? response.message : message)));
      await pollAnalysisRun(response.analysis_run_id);
      onChatUpdated?.();
    } catch (sendError) {
      setStatus(sendError instanceof Error ? sendError.message : "Message failed");
    } finally {
      setIsSending(false);
    }
  }

  async function pollAnalysisRun(analysisRunId: string) {
    setStatus("queued");
    for (let index = 0; index < 120; index += 1) {
      const run = await apiClient.getAnalysisRun(analysisRunId);
      setStatus(run.current_stage ?? run.status);
      if ((run.status === "success" || run.status === "partial_success") && run.assistant_message) {
        setMessages((current) => [...current.filter((message) => message.id !== run.assistant_message?.id), run.assistant_message as Message].sort((a, b) => a.message_index - b.message_index));
        setStatus(null);
        return;
      }
      if (run.status === "success" || run.status === "partial_success") {
        const loadedMessages = await apiClient.getMessages(chatId);
        setMessages(loadedMessages.data);
        setStatus(null);
        return;
      }
      if (run.status === "failed") {
        setStatus(run.error_message ?? "Analysis failed");
        return;
      }
      if (index % 4 === 3) {
        const loadedMessages = await apiClient.getMessages(chatId);
        setMessages((current) => {
          const persistedIds = new Set(loadedMessages.data.map((message) => message.id));
          const optimisticMessages = current.filter((message) => message.id.startsWith("optimistic-") && !persistedIds.has(message.id));
          return [...loadedMessages.data, ...optimisticMessages].sort((a, b) => a.message_index - b.message_index);
        });
      }
      await new Promise((resolve) => setTimeout(resolve, 500));
    }
    const loadedMessages = await apiClient.getMessages(chatId);
    setMessages(loadedMessages.data);
    setStatus(null);
  }

  return (
    <div className="flex h-full min-h-[34rem] flex-col">
      <div className="border-b border-[#ddd2c4] pb-4">
        <p className="font-mono text-xs uppercase tracking-[0.18em] text-[#8f6a4e]">Chat</p>
        <h2 className="mt-2 text-2xl font-semibold tracking-[-0.05em]">{chat?.title ?? "Investigation"}</h2>
        <p className="mt-1 text-sm text-[#655c52]">
          {dataset ? `${dataset.name} · ${dataset.row_count} rows · ${columns.length} columns · ${issues.length} quality notes` : "Loading dataset context"}
        </p>
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto py-5">
        {messages.length === 0 ? <p className="border border-[#d9cdbf] bg-[#fffaf7] p-4 text-sm text-[#655c52]">Ask your first question about this dataset.</p> : null}
        {messages.map((message) => (
          <article
            key={message.id}
            className={[
              "max-w-3xl border p-4",
              message.role === "user" ? "ml-auto border-[#241f1a] bg-[#241f1a] text-[#fffaf7]" : "border-[#d9cdbf] bg-[#fffaf7] text-[#241f1a]",
            ].join(" ")}
          >
            {message.role === "assistant" && message.blocks?.length ? null : (
              <p className="text-sm leading-6">{message.content}</p>
            )}
            {message.role === "assistant" ? <BlockRenderer blocks={message.blocks} /> : null}
          </article>
        ))}
        {status ? (
          <div className="flex items-center gap-2 text-sm text-[#655c52]">
            <Loader2 className="animate-spin" size={16} />
            {status}
          </div>
        ) : null}
      </div>

      <form onSubmit={(event) => void handleSubmit(event)} className="border-t border-[#ddd2c4] pt-4">
        <label className="sr-only" htmlFor="chat-prompt">Ask Sherlock</label>
        <div className="flex gap-2">
          <textarea
            id="chat-prompt"
            value={prompt}
            onChange={(event) => setPrompt(event.target.value)}
            placeholder="Ask about rows, columns, quality, trends, or totals"
            className="min-h-20 flex-1 resize-none border border-[#d9cdbf] bg-[#fffaf7] px-3 py-3 text-sm"
          />
          <button type="submit" disabled={isSending || !prompt.trim()} className="inline-flex w-12 items-center justify-center border border-[#241f1a] bg-[#241f1a] text-[#fffaf7] disabled:opacity-60" aria-label="Send message">
            {isSending ? <Loader2 className="animate-spin" size={17} /> : <Send size={17} />}
          </button>
        </div>
      </form>
    </div>
  );
}

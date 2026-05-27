"use client";

import type { FormEventHandler, ReactNode } from "react";

type WrapperProps = {
  children: ReactNode;
  className?: string;
};

export function SherlockConversation({ children, className = "" }: WrapperProps) {
  return <section className={className}>{children}</section>;
}

export function SherlockMessage({ children, className = "" }: WrapperProps) {
  return <article className={className}>{children}</article>;
}

type PromptComposerProps = {
  children?: ReactNode;
  className?: string;
  onSubmit?: FormEventHandler<HTMLFormElement>;
};

export function SherlockPromptComposer({ children, className = "", onSubmit }: PromptComposerProps) {
  return (
    <form className={className} aria-label="Prompt composer" onSubmit={onSubmit}>
      {children ?? (
        <>
          <label className="sr-only" htmlFor="sherlock-prompt">
            Ask Sherlock
          </label>
          <textarea
            id="sherlock-prompt"
            rows={2}
            disabled
            placeholder="Ask a question after uploading a dataset"
            className="min-h-20 w-full resize-none border border-[#d9cdbf] bg-[#fffaf7] px-3 py-3 text-sm text-[#241f1a] placeholder:text-[#8b7d70] disabled:cursor-not-allowed disabled:opacity-80"
          />
        </>
      )}
    </form>
  );
}

export function SherlockThinkingState({ className = "", label = "Ready for an investigation" }: { className?: string; label?: string }) {
  return (
    <div className={className} aria-label="Thinking state">
      <span className="inline-flex size-2 rounded-full bg-[#9d5728] motion-safe:animate-pulse" />
      <span className="text-sm text-[#655c52]">{label}</span>
    </div>
  );
}

export function SherlockSuggestions({ suggestions, className = "" }: { suggestions: string[]; className?: string }) {
  return (
    <div className={className} aria-label="Suggestions">
      {suggestions.map((suggestion) => (
        <button
          key={suggestion}
          type="button"
          disabled
          className="border border-[#d9cdbf] bg-[#fffaf7] px-3 py-2 text-left text-sm text-[#51473f] disabled:cursor-not-allowed"
        >
          {suggestion}
        </button>
      ))}
    </div>
  );
}

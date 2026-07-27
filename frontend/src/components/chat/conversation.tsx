"use client";

import { SendHorizontal } from "lucide-react";
import { useActionState, useOptimistic, useRef } from "react";
import { useFormStatus } from "react-dom";

import { askQuestion, type ChatActionState } from "@/app/(app)/chat/actions";
import { LogoMark } from "@/components/brand/logo";
import { Button } from "@/components/ui/button";
import type { ChatMessageRecord } from "@/lib/services";
import { cn } from "@/lib/utils";

const SUGGESTIONS = [
  "What should I learn next?",
  "Am I ready to apply for a senior role?",
  "What's the weakest part of my CV?",
];

function Bubble({
  role,
  children,
  muted = false,
}: {
  role: "user" | "assistant";
  children: React.ReactNode;
  muted?: boolean;
}) {
  return (
    <div className={cn("flex gap-3", role === "user" && "flex-row-reverse")}>
      {role === "assistant" && (
        <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-primary/12">
          <LogoMark className="h-4 w-4 text-primary" />
        </span>
      )}
      <div className={cn("max-w-[80%]", muted && "opacity-60")}>{children}</div>
    </div>
  );
}

/** Three dots while the model composes. Cheaper to read than a spinner. */
function Thinking() {
  const { pending } = useFormStatus();
  if (!pending) return null;

  return (
    <Bubble role="assistant">
      <div
        role="status"
        className="flex items-center gap-1 rounded-2xl bg-muted px-4 py-3"
      >
        <span className="sr-only">Thinking</span>
        {[0, 150, 300].map((delay) => (
          <span
            key={delay}
            aria-hidden
            className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground/60"
            style={{ animationDelay: `${delay}ms` }}
          />
        ))}
      </div>
    </Bubble>
  );
}

function Send() {
  const { pending } = useFormStatus();
  return (
    <Button
      type="submit"
      size="icon"
      className="h-10 w-10"
      aria-label="Send"
      disabled={pending}
      aria-busy={pending}
    >
      <SendHorizontal className="h-4 w-4" />
    </Button>
  );
}

/**
 * Transcript and composer in one client component.
 *
 * Client-side so the question can appear the instant it is sent: a grounded
 * answer is a retrieval plus a model call, and a message that vanishes for
 * several seconds reads as a dropped one.
 */
export function Conversation({
  messages,
  disabled,
}: {
  messages: ChatMessageRecord[];
  disabled: boolean;
}) {
  const [state, action] = useActionState<ChatActionState, FormData>(
    askQuestion,
    {},
  );
  const [shown, addOptimistic] = useOptimistic(
    messages,
    (current, content: string): ChatMessageRecord[] => [
      ...current,
      {
        id: `pending-${current.length}`,
        role: "user",
        content,
        sources: null,
        created_at: new Date().toISOString(),
      },
    ],
  );
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <div className="flex h-[560px] flex-col rounded-2xl border bg-card">
      <div className="flex-1 space-y-4 overflow-y-auto p-6">
        {shown.length === 0 ? (
          <p className="pt-16 text-center text-sm text-muted-foreground">
            Ask the first question.
          </p>
        ) : (
          shown.map((m) => (
            <Bubble
              key={m.id}
              role={m.role}
              muted={m.id.startsWith("pending-")}
            >
              {/* Model output rendered as plain text, never as HTML or
                  markdown. Nothing the model returns can become markup. */}
              <div
                className={cn(
                  "whitespace-pre-wrap rounded-2xl px-4 py-2.5 text-sm",
                  m.role === "assistant"
                    ? "bg-muted"
                    : "bg-primary text-primary-foreground",
                )}
              >
                {m.content}
              </div>
              {m.role === "assistant" && m.sources && m.sources.length > 0 ? (
                <p className="mt-1 px-1 font-mono text-[10px] text-muted-foreground">
                  from: {[...new Set(m.sources.map((s) => s.kind))].join(", ")}
                </p>
              ) : null}
            </Bubble>
          ))
        )}
        <Thinking />
      </div>

      <form
        action={(formData) => {
          const message = String(formData.get("message") ?? "").trim();
          if (message) addOptimistic(message);
          // Clear now rather than in an effect: the sent text is already on
          // screen as the optimistic bubble.
          if (inputRef.current) inputRef.current.value = "";
          return action(formData);
        }}
        className="border-t p-4"
      >
        <div className="mb-3 flex flex-wrap gap-2">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              type="button"
              disabled={disabled}
              onClick={() => {
                if (inputRef.current) inputRef.current.value = s;
              }}
              className="rounded-full border px-3 py-1 text-xs text-muted-foreground transition-colors hover:border-primary/50 hover:text-foreground disabled:opacity-50"
            >
              {s}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <input
            ref={inputRef}
            name="message"
            disabled={disabled}
            placeholder={
              disabled
                ? "Analyze your CV first so there's something to talk about"
                : "Ask anything about your career…"
            }
            className="h-10 flex-1 rounded-lg border bg-background px-3 text-sm outline-none placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/30 disabled:opacity-60"
          />
          <Send />
        </div>

        {state.error ? (
          <p role="alert" className="mt-2 text-xs text-destructive">
            {state.error}
          </p>
        ) : null}
      </form>
    </div>
  );
}

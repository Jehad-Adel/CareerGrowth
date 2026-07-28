"use client";

import { Loader2, SendHorizontal, Trash2 } from "lucide-react";
import { useActionState, useOptimistic, useRef, useTransition } from "react";
import { useFormStatus } from "react-dom";

import {
  askQuestion,
  clearChat,
  type ChatActionState,
} from "@/app/(app)/chat/actions";
import { LogoMark } from "@/components/brand/logo";
import { Button } from "@/components/ui/button";
import { DictateButton } from "@/components/ui/dictate-button";
import type { ChatMessageRecord, ChatSource } from "@/lib/services";
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
      {/* `min-w-0` lets the bubble shrink below its longest word, which is what
          keeps a pasted URL from widening the whole transcript. */}
      <div className={cn("min-w-0 max-w-[85%] sm:max-w-[80%]", muted && "opacity-60")}>
        {children}
      </div>
    </div>
  );
}

function names(sources: ChatSource[]): string[] {
  return [...new Set(sources.map((s) => s.label ?? s.kind))];
}

/**
 * Where an answer came from.
 *
 * The two corpora are listed separately because they mean different things:
 * the person's own documents are evidence about them, CareerFarm's guidance
 * is not. Collapsing both into one "from:" list would let general advice read
 * as something their CV said.
 */
function Attribution({ sources }: { sources: ChatSource[] }) {
  // Sources without an origin predate guidance attribution, and everything
  // stored back then came from the person's own documents.
  const documents = names(sources.filter((s) => s.origin !== "guide"));
  const guides = names(sources.filter((s) => s.origin === "guide"));

  if (documents.length === 0 && guides.length === 0) return null;

  return (
    <p className="mt-1 px-1 font-mono text-[10px] text-muted-foreground">
      {documents.length > 0 && <>from: {documents.join(", ")}</>}
      {documents.length > 0 && guides.length > 0 && " · "}
      {guides.length > 0 && <>guidance: {guides.join(", ")}</>}
    </p>
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
      className="h-11 w-11 shrink-0 rounded-xl"
      aria-label="Send"
      disabled={pending}
      aria-busy={pending}
    >
      {pending ? (
        <Loader2 className="h-4 w-4 animate-spin" />
      ) : (
        <SendHorizontal className="h-4 w-4" />
      )}
    </Button>
  );
}

function ClearChatButton() {
  const [isPending, startTransition] = useTransition();

  return (
    <Button
      variant="ghost"
      size="sm"
      className="min-h-9 px-3 text-xs text-muted-foreground hover:text-destructive focus-visible:ring-2 focus-visible:ring-destructive focus-visible:ring-offset-1"
      aria-label="Clear chat history"
      disabled={isPending}
      onClick={() => {
        startTransition(async () => {
          await clearChat();
        });
      }}
    >
      <Trash2 className="me-1.5 h-3.5 w-3.5" />
      {isPending ? "Clearing..." : "Clear history"}
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
        id: `pending-${Date.now()}`,
        role: "user",
        content,
        sources: null,
        created_at: new Date().toISOString(),
      },
    ],
  );
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    // A fixed 560px box is taller than a phone's viewport minus the topbar and
    // page header, so the composer sat below the fold and the transcript could
    // not be reached without scrolling the page under a sticky header. `dvh`
    // rather than `vh` — `vh` measures the viewport with the URL bar hidden.
    <div className="flex h-[calc(100dvh-13rem)] min-h-[26rem] flex-col rounded-2xl border bg-card sm:h-[560px]">
      {messages.length > 0 ? (
        <div className="flex justify-end border-b px-4 py-2 bg-muted/20">
          <ClearChatButton />
        </div>
      ) : null}
      <div className="scroll-area flex-1 space-y-4 overflow-y-auto p-4 sm:p-6">
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
                  "whitespace-pre-wrap break-words rounded-2xl px-3.5 py-2.5 text-sm sm:px-4",
                  m.role === "assistant"
                    ? "bg-muted"
                    : "bg-primary text-primary-foreground",
                )}
              >
                {m.content}
              </div>
              {m.role === "assistant" && m.sources && m.sources.length > 0 ? (
                <Attribution sources={m.sources} />
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
        className="border-t p-3 sm:p-4"
      >
        {/* One scrolling row on a phone rather than three wrapped lines: inside
            a viewport-height panel, wrapped chips ate the transcript. They go
            back to wrapping once there is room. */}
        <div className="scroll-area -mx-1 mb-2.5 flex gap-2 overflow-x-auto px-1 pb-1 sm:mx-0 sm:mb-3 sm:flex-wrap sm:overflow-visible sm:px-0 sm:pb-0">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              type="button"
              disabled={disabled}
              onClick={() => {
                if (inputRef.current) inputRef.current.value = s;
              }}
              className="inline-flex min-h-9 shrink-0 items-center whitespace-nowrap rounded-full border px-3.5 py-1.5 text-xs text-muted-foreground transition-all hover:border-primary/60 hover:bg-primary/5 hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1 disabled:opacity-50 sm:whitespace-normal"
            >
              {s}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-1.5 sm:gap-2">
          <input
            ref={inputRef}
            name="message"
            disabled={disabled}
            // `enterkeyhint` so the phone keyboard's action key says Send, and
            // the autocomplete/spellcheck settings a chat box wants.
            enterKeyHint="send"
            autoComplete="off"
            aria-label="Ask a question about your career"
            placeholder={
              disabled
                ? "Analyze your CV first so there's something to talk about"
                : "Ask anything about your career…"
            }
            // 16px on mobile deliberately: iOS zooms the whole page in when a
            // focused input's text is smaller than that, and never zooms back
            // out. `sm:text-sm` restores the intended size on desktop.
            className="h-11 min-w-0 flex-1 rounded-xl border bg-background px-3.5 text-base outline-none placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/30 disabled:opacity-60 sm:text-sm"
          />
          {/* Writes straight into the uncontrolled input, the same way the
              suggestion chips above already do. Never submits on its own —
              the user reads what was heard, then presses send. */}
          <DictateButton inputRef={inputRef} disabled={disabled} />
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

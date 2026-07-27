"use client";

import { SendHorizontal } from "lucide-react";
import { useActionState, useEffect, useRef } from "react";
import { useFormStatus } from "react-dom";

import { askQuestion, type ChatActionState } from "@/app/(app)/chat/actions";
import { Button } from "@/components/ui/button";

const SUGGESTIONS = [
  "What should I learn next?",
  "Am I ready to apply for a senior role?",
  "What's the weakest part of my CV?",
];

function Send() {
  const { pending } = useFormStatus();
  return (
    <Button
      type="submit"
      size="icon"
      className="h-10 w-10"
      aria-label="Send"
      disabled={pending}
    >
      <SendHorizontal className="h-4 w-4" />
    </Button>
  );
}

export function ChatInput({ disabled }: { disabled: boolean }) {
  const [state, action] = useActionState<ChatActionState, FormData>(
    askQuestion,
    {},
  );
  const formRef = useRef<HTMLFormElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Clear the box once a question actually went through.
  useEffect(() => {
    if (state.ok) formRef.current?.reset();
  }, [state]);

  return (
    <form ref={formRef} action={action} className="border-t p-4">
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
  );
}

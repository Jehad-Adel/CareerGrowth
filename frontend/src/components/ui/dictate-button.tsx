"use client";

import { Mic, Square } from "lucide-react";
import type { RefObject } from "react";

import { Button } from "@/components/ui/button";
import { useDictation } from "@/lib/use-dictation";

/**
 * Mic button for an existing uncontrolled input.
 *
 * The counterpart to `DictateField`: that one owns its textarea, this one
 * writes into a field somebody else owns, via the ref they already hold. The
 * chat input is uncontrolled and its suggestion chips already work this way,
 * so matching them avoids converting the form to controlled state for one
 * button.
 *
 * Like `DictateField`, it never submits — recognition mishears, and every send
 * costs an AI call.
 */
export function DictateButton({
  inputRef,
  disabled = false,
}: {
  inputRef: RefObject<HTMLInputElement | null>;
  disabled?: boolean;
}) {
  const dictation = useDictation((phrase) => {
    const input = inputRef.current;
    if (!input || !phrase) return;
    const current = input.value.trim();
    input.value = current ? `${current} ${phrase}` : phrase;
  });

  if (!dictation.supported) return null;

  return (
    <Button
      type="button"
      variant={dictation.listening ? "default" : "ghost"}
      size="icon"
      disabled={disabled}
      onClick={dictation.toggle}
      aria-pressed={dictation.listening}
      aria-label={dictation.listening ? "Stop dictating" : "Dictate your question"}
      title={
        dictation.error ??
        (dictation.listening ? "Stop dictating" : "Dictate your question")
      }
      className="shrink-0"
    >
      {dictation.listening ? (
        <Square className="h-4 w-4" />
      ) : (
        <Mic className="h-4 w-4" />
      )}
      <span className="sr-only" aria-live="polite">
        {dictation.listening ? `Listening. ${dictation.interim}` : ""}
      </span>
    </Button>
  );
}

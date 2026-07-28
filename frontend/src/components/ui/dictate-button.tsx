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
    // React tracks the last value it wrote to an input and swallows an `input`
    // event that reports the same one. Clearing that tracker first makes the
    // dispatch below behave like real typing, so anything listening (and the
    // browser's own scroll-to-caret) reacts to dictated text too.
    const tracker = (
      input as unknown as {
        _valueTracker?: { setValue: (v: string) => void };
      }
    )._valueTracker;
    tracker?.setValue("");
    input.dispatchEvent(new Event("input", { bubbles: true }));
    input.scrollLeft = input.scrollWidth;
  });

  if (!dictation.supported) return null;

  return (
    <div className="relative shrink-0">
      {/* Live feedback anchored to the button. Without it the only sign that
          recognition is running is the icon swap, and a mic that is listening
          but has not heard anything yet looks identical to a broken one. */}
      {dictation.listening || dictation.error ? (
        <div
          className="absolute bottom-full end-0 mb-2 max-w-[min(18rem,60vw)] rounded-lg border bg-popover px-2.5 py-1.5 text-xs shadow-md"
          role={dictation.error ? "alert" : undefined}
        >
          {dictation.error ? (
            <span className="text-destructive">{dictation.error}</span>
          ) : (
            <span className="line-clamp-2 text-muted-foreground">
              <span className="me-1.5 inline-block h-2 w-2 animate-pulse rounded-full bg-destructive align-middle" />
              {dictation.interim || "Listening…"}
            </span>
          )}
        </div>
      ) : null}

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
        className="h-11 w-11 rounded-xl"
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
    </div>
  );
}

"use client";

import { Mic, Square } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useDictation } from "@/lib/use-dictation";
import { cn } from "@/lib/utils";

/**
 * A textarea you can talk into.
 *
 * The dictated text lands in the field and is **never auto-submitted**. Speech
 * recognition mishears names and technical terms constantly, and every submit
 * here spends an AI quota call — so the transcript is a draft the user reads
 * and corrects, not a command. That single decision is what makes this a UX
 * improvement rather than a new way to waste a generation.
 *
 * Controlled, so dictation can append to what is already typed. To clear it
 * after a successful submit, give it a `key` that changes then — React's own
 * answer for resetting component state, and it avoids an effect that would
 * also fire on a failed submit and delete what the user just dictated.
 */
export function DictateField({
  name,
  rows = 6,
  placeholder,
  ariaLabel,
}: {
  name: string;
  rows?: number;
  placeholder?: string;
  ariaLabel?: string;
}) {
  const [value, setValue] = useState("");

  const dictation = useDictation((phrase) => {
    if (!phrase) return;
    setValue((current) =>
      current ? `${current.trimEnd()} ${phrase}` : phrase,
    );
  });

  return (
    <div className="space-y-2">
      <div className="relative">
        <Textarea
          name={name}
          rows={rows}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder={placeholder}
          aria-label={ariaLabel}
          className={cn(dictation.supported && "pr-12")}
        />

        {dictation.supported ? (
          <Button
            type="button"
            variant={dictation.listening ? "default" : "ghost"}
            size="icon"
            onClick={dictation.toggle}
            aria-pressed={dictation.listening}
            aria-label={dictation.listening ? "Stop dictating" : "Dictate your answer"}
            title={
              dictation.listening
                ? "Stop dictating"
                : "Dictate — your browser transcribes it, and you can edit before sending"
            }
            className="absolute right-2 top-2"
          >
            {dictation.listening ? (
              <Square className="h-4 w-4" />
            ) : (
              <Mic className="h-4 w-4" />
            )}
          </Button>
        ) : null}
      </div>

      {/* aria-live so a screen reader hears that recording started, and hears
          the words as they are recognised. */}
      <p aria-live="polite" className="min-h-4 px-1 text-xs text-muted-foreground">
        {dictation.error ? (
          <span role="alert" className="text-destructive">
            {dictation.error}
          </span>
        ) : dictation.listening ? (
          <>
            <span className="mr-1.5 inline-block h-2 w-2 animate-pulse rounded-full bg-destructive align-middle" />
            Listening… {dictation.interim}
          </>
        ) : null}
      </p>
    </div>
  );
}

"use client";

import { DICTATION_LANGUAGES } from "@/lib/use-dictation-language";
import { cn } from "@/lib/utils";

/**
 * Language picker for dictation.
 *
 * A native `<select>` on purpose: it is one control, it is keyboard and screen
 * reader complete for free, and on a phone it opens the OS picker — a custom
 * listbox here would be more code and worse.
 */
export function DictationLanguage({
  value,
  onChange,
  className,
}: {
  value: string;
  onChange: (next: string) => void;
  className?: string;
}) {
  return (
    <label className={cn("inline-flex items-center gap-1.5", className)}>
      <span className="sr-only">Dictation language</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        title="Language the microphone listens for"
        className="h-8 rounded-lg border bg-background px-1.5 text-xs text-muted-foreground outline-none focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/40"
      >
        {DICTATION_LANGUAGES.map((l) => (
          <option key={l.value} value={l.value}>
            {l.label}
          </option>
        ))}
      </select>
    </label>
  );
}

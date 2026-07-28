"use client";

import { useCallback, useSyncExternalStore } from "react";

/**
 * The language dictation should recognise, remembered across sessions.
 *
 * Kept out of the dictation hook itself so the mic button and the answer
 * textarea share one preference: someone who dictates their interview answers
 * in Arabic does not want to re-pick it in the chat composer.
 */
const KEY = "cf-dictation-lang";

export const DICTATION_LANGUAGES = [
  { value: "en-US", label: "English (US)" },
  { value: "en-GB", label: "English (UK)" },
  { value: "ar-EG", label: "العربية (مصر)" },
  { value: "ar-SA", label: "العربية (فصحى)" },
  { value: "fr-FR", label: "Français" },
  { value: "es-ES", label: "Español" },
  { value: "de-DE", label: "Deutsch" },
] as const;

/** The closest offered tag to the browser's own language, else English. */
function fallback(): string {
  if (typeof navigator === "undefined") return "en-US";
  const preferred = navigator.language;
  const exact = DICTATION_LANGUAGES.find((l) => l.value === preferred);
  if (exact) return exact.value;
  const base = preferred?.split("-")[0];
  const sameBase = DICTATION_LANGUAGES.find((l) => l.value.startsWith(`${base}-`));
  return sameBase?.value ?? "en-US";
}

/**
 * localStorage as an external store, rather than state seeded in an effect.
 * The effect version renders the default, then immediately sets state — a
 * cascading render React 19's lint rejects — and it does not keep two mounted
 * pickers (the chat button and an answer field) in step. `useSyncExternalStore`
 * gives the server a stable snapshot and swaps in the stored value at
 * hydration, which is the case that would otherwise be a mismatch.
 */
const listeners = new Set<() => void>();

function subscribe(onChange: () => void) {
  listeners.add(onChange);
  // `storage` only fires in *other* tabs; same-tab updates go through the
  // manual notify in `choose`.
  window.addEventListener("storage", onChange);
  return () => {
    listeners.delete(onChange);
    window.removeEventListener("storage", onChange);
  };
}

function getSnapshot(): string {
  return window.localStorage.getItem(KEY) ?? fallback();
}

const getServerSnapshot = () => "en-US";

export function useDictationLanguage(): [string, (next: string) => void] {
  const lang = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);

  const choose = useCallback((next: string) => {
    window.localStorage.setItem(KEY, next);
    for (const notify of listeners) notify();
  }, []);

  return [lang, choose];
}

import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * One date format for the whole app.
 *
 * `toLocaleDateString()` with no arguments reads whatever locale the *runtime*
 * has. In a Server Component that is the container's — `en-US` on Railway —
 * so every visitor got ambiguous `M/D/YYYY` regardless of where they are. In a
 * Client Component it is the server's during SSR and the browser's after
 * hydration, which is a mismatch React warns about. Pinning the locale, the
 * fields, and the time zone makes the output identical everywhere.
 */
const DATE_FORMAT = new Intl.DateTimeFormat("en-GB", {
  day: "numeric",
  month: "short",
  year: "numeric",
  timeZone: "UTC",
})

/** e.g. "7 Mar 2026". Returns "" for a missing or unparseable value. */
export function formatDate(value: string | number | Date | null | undefined): string {
  if (value === null || value === undefined || value === "") return ""
  const date = value instanceof Date ? value : new Date(value)
  return Number.isNaN(date.getTime()) ? "" : DATE_FORMAT.format(date)
}

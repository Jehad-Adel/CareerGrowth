"use client";

import { AlertCircle, Trash2 } from "lucide-react";
import { useActionState } from "react";

import {
  addApplication,
  deleteApplication,
  moveApplication,
  type ApplicationActionState,
} from "@/app/(app)/applications/actions";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PendingFieldset, SubmitButton } from "@/components/ui/submit-button";
import type {
  ApplicationBoard,
  ApplicationRecord,
  ApplicationStatus,
} from "@/lib/services";

const LABELS: Record<ApplicationStatus, string> = {
  saved: "Saved",
  applied: "Applied",
  interviewing: "Interviewing",
  offer: "Offer",
  rejected: "Rejected",
};

const ACCENT: Record<ApplicationStatus, string> = {
  saved: "bg-muted text-muted-foreground",
  applied: "bg-primary/12 text-primary",
  interviewing: "bg-[var(--harvest)]/15 text-[var(--harvest)]",
  offer: "bg-primary/20 text-primary",
  rejected: "bg-destructive/12 text-destructive",
};

/** Whole days since a date, or null when there is nothing to count from. */
function daysSince(iso: string | null): number | null {
  if (!iso) return null;
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return null;
  return Math.floor((Date.now() - then) / 86_400_000);
}

function Card({
  application,
  statuses,
}: {
  application: ApplicationRecord;
  statuses: ApplicationStatus[];
}) {
  const waiting = daysSince(application.applied_at);

  return (
    <li className="flex flex-col gap-3 rounded-xl border bg-card p-4 transition-shadow hover:shadow-sm">
      <div className="space-y-1 min-w-0">
        <p className="text-sm font-semibold leading-snug break-words">{application.role}</p>
        <p className="text-xs text-muted-foreground break-words">{application.company}</p>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
        {waiting !== null && !["offer", "rejected"].includes(application.status) ? (
          <span className="rounded-md bg-muted/70 px-2 py-0.5 font-mono text-[11px] text-muted-foreground">
            {waiting === 0 ? "Applied today" : `${waiting}d waiting`}
          </span>
        ) : (
          <span />
        )}

        {application.url ? (
          <a
            href={application.url}
            target="_blank"
            rel="noopener noreferrer"
            className="font-medium text-primary underline-offset-4 hover:underline focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-1 rounded-sm"
          >
            Posting ↗
          </a>
        ) : null}
      </div>

      <div className="flex items-center gap-2 border-t border-border/50 pt-2.5">
        <form action={moveApplication} className="flex-1 min-w-0">
          <input type="hidden" name="id" value={application.id} />
          <label className="sr-only" htmlFor={`move-${application.id}`}>
            Move {application.role} to another stage
          </label>
          <select
            id={`move-${application.id}`}
            name="status"
            defaultValue={application.status}
            onChange={(e) => e.currentTarget.form?.requestSubmit()}
            className="w-full rounded-lg border bg-background px-2.5 py-1.5 text-xs outline-none transition-colors focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1"
          >
            {statuses.map((s) => (
              <option key={s} value={s}>
                {LABELS[s]}
              </option>
            ))}
          </select>
        </form>

        <form action={deleteApplication}>
          <input type="hidden" name="id" value={application.id} />
          <button
            type="submit"
            aria-label={`Delete ${application.role} at ${application.company}`}
            className="min-h-[36px] min-w-[36px] flex items-center justify-center rounded-lg p-2 text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive focus-visible:ring-2 focus-visible:ring-destructive focus-visible:outline-none"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </form>
      </div>
    </li>
  );
}

export function ApplicationsBoard({ board }: { board: ApplicationBoard }) {
  const [state, action] = useActionState<ApplicationActionState, FormData>(
    addApplication,
    {},
  );

  return (
    <div className="space-y-6">
      <section className="rounded-2xl border bg-card p-6">
        {/* Keyed on submittedAt so the inputs clear once a row is saved, and
            keep their text when validation rejects it. */}
        <form key={state.submittedAt ?? "new"} action={action} className="space-y-4">
          <PendingFieldset>
            <div className="grid gap-4 sm:grid-cols-3">
              <div className="space-y-1.5">
                <Label htmlFor="company" className="text-sm font-medium">Company</Label>
                <Input id="company" name="company" maxLength={200} placeholder="Acme Corp" required aria-required="true" />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="role" className="text-sm font-medium">Role</Label>
                <Input id="role" name="role" maxLength={200} placeholder="Senior Frontend Engineer" required aria-required="true" />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="url" className="text-sm font-medium">Posting link (optional)</Label>
                <Input id="url" name="url" type="url" maxLength={500} placeholder="https://..." />
              </div>
            </div>
          </PendingFieldset>

          <div className="flex flex-wrap items-center gap-3 pt-1">
            <SubmitButton idle="Track this" busy="Saving…" />
            {state.error ? (
              <div role="alert" className="flex items-center gap-2 rounded-lg bg-destructive/10 px-3.5 py-2 text-xs text-destructive">
                <AlertCircle className="h-3.5 w-3.5 shrink-0" />
                <span>{state.error}</span>
              </div>
            ) : null}
          </div>
        </form>
      </section>

      <div className="grid gap-5 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-5">
        {board.statuses.map((status) => {
          const column = board.applications.filter((a) => a.status === status);
          return (
            <section key={status} className="space-y-2.5 min-w-0">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-medium">{LABELS[status]}</h2>
                <span
                  className={`rounded-full px-2 py-0.5 text-xs ${ACCENT[status]}`}
                >
                  {board.counts[status] ?? 0}
                </span>
              </div>

              {column.length === 0 ? (
                <p className="rounded-xl border border-dashed p-3 text-xs text-muted-foreground">
                  Nothing here.
                </p>
              ) : (
                <ul className="space-y-2.5">
                  {column.map((application) => (
                    <Card
                      key={application.id}
                      application={application}
                      statuses={board.statuses}
                    />
                  ))}
                </ul>
              )}
            </section>
          );
        })}
      </div>
    </div>
  );
}

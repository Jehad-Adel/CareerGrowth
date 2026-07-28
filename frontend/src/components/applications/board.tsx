"use client";

import { Trash2 } from "lucide-react";
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
    <li className="rounded-xl border bg-card p-3">
      <p className="text-sm font-medium">{application.role}</p>
      <p className="text-xs text-muted-foreground">{application.company}</p>

      {waiting !== null && !["offer", "rejected"].includes(application.status) ? (
        // The number people actually want: how long they have been waiting.
        <p className="mt-1 text-xs text-muted-foreground">
          {waiting === 0 ? "Applied today" : `${waiting}d since applying`}
        </p>
      ) : null}

      {application.url ? (
        <a
          href={application.url}
          target="_blank"
          // noreferrer alongside noopener: the target must learn nothing about
          // where the click came from.
          rel="noopener noreferrer"
          className="mt-1 inline-block text-xs text-primary underline underline-offset-2"
        >
          Posting
        </a>
      ) : null}

      <div className="mt-2.5 flex items-center gap-2">
        <form action={moveApplication} className="flex-1">
          <input type="hidden" name="id" value={application.id} />
          <label className="sr-only" htmlFor={`move-${application.id}`}>
            Move {application.role} to another stage
          </label>
          <select
            id={`move-${application.id}`}
            name="status"
            defaultValue={application.status}
            // A select rather than drag-and-drop: it works on a phone, works
            // with a keyboard, needs no library, and cannot drop a card into
            // nowhere.
            onChange={(e) => e.currentTarget.form?.requestSubmit()}
            className="w-full rounded-lg border bg-background px-2 py-1 text-xs outline-none focus-visible:border-ring"
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
            className="rounded-lg p-1.5 text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive"
          >
            <Trash2 className="h-3.5 w-3.5" />
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
      <section className="rounded-2xl border bg-card p-5">
        {/* Keyed on submittedAt so the inputs clear once a row is saved, and
            keep their text when validation rejects it. */}
        <form key={state.submittedAt ?? "new"} action={action} className="space-y-3">
          <PendingFieldset>
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="space-y-1.5">
                <Label htmlFor="company">Company</Label>
                <Input id="company" name="company" maxLength={200} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="role">Role</Label>
                <Input id="role" name="role" maxLength={200} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="url">Posting link (optional)</Label>
                <Input id="url" name="url" type="url" maxLength={500} />
              </div>
            </div>
          </PendingFieldset>

          <div className="flex items-center gap-3">
            <SubmitButton idle="Track this" busy="Saving…" size="sm" />
            {state.error ? (
              <p role="alert" className="text-xs text-destructive">
                {state.error}
              </p>
            ) : null}
          </div>
        </form>
      </section>

      <div className="grid gap-4 md:grid-cols-3 xl:grid-cols-5">
        {board.statuses.map((status) => {
          const column = board.applications.filter((a) => a.status === status);
          return (
            <section key={status} className="space-y-2.5">
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

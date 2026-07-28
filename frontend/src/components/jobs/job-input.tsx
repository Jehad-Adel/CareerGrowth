"use client";

import { AlertCircle } from "lucide-react";
import { useActionState } from "react";

import type { JobActionState } from "@/app/(app)/jobs/actions";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PendingFieldset, SubmitButton } from "@/components/ui/submit-button";
import { Textarea } from "@/components/ui/textarea";

export function JobInput({
  action,
  label,
  hint,
  disabled = false,
}: {
  action: (prev: JobActionState, formData: FormData) => Promise<JobActionState>;
  label: string;
  hint: string;
  disabled?: boolean;
}) {
  const [state, formAction] = useActionState<JobActionState, FormData>(action, {});

  return (
    <form action={formAction} className="space-y-4">
      <PendingFieldset>
        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="job_title" className="text-sm font-medium">Role title (optional)</Label>
            <Input
              id="job_title"
              name="job_title"
              placeholder="Senior Backend Engineer"
              maxLength={200}
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="job_description" className="text-sm font-medium">Job description</Label>
            <Textarea
              id="job_description"
              name="job_description"
              rows={10}
              required
              aria-required="true"
              placeholder="Paste the full posting here…"
              aria-describedby="jd-hint"
            />
            <p id="jd-hint" className="text-xs text-muted-foreground">
              {hint}
            </p>
          </div>
        </div>
      </PendingFieldset>

      <SubmitButton
        idle={label}
        busy="Reading the job…"
        disabled={disabled}
        className="w-full"
      />

      {state.error ? (
        <div role="alert" className="flex items-start gap-2.5 rounded-lg bg-destructive/10 px-3.5 py-2.5 text-xs text-destructive">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-destructive" />
          <span>{state.error}</span>
        </div>
      ) : null}
    </form>
  );
}

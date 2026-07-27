"use client";

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
        <div className="space-y-1.5">
          <Label htmlFor="job_title">Role title (optional)</Label>
          <Input
            id="job_title"
            name="job_title"
            placeholder="Senior Backend Engineer"
            maxLength={200}
          />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="job_description">Job description</Label>
          <Textarea
            id="job_description"
            name="job_description"
            rows={10}
            placeholder="Paste the full posting here…"
            aria-describedby="jd-hint"
          />
          <p id="jd-hint" className="text-xs text-muted-foreground">
            {hint}
          </p>
        </div>
      </PendingFieldset>

      <SubmitButton
        idle={label}
        busy="Reading the job…"
        disabled={disabled}
        className="w-full"
      />

      {state.error ? (
        <p role="alert" className="text-xs text-destructive">
          {state.error}
        </p>
      ) : null}
    </form>
  );
}

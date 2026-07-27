"use client";

import { useActionState } from "react";
import { useFormStatus } from "react-dom";

import type { JobActionState } from "@/app/(app)/jobs/actions";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

function Submit({ label, disabled }: { label: string; disabled: boolean }) {
  const { pending } = useFormStatus();
  return (
    <Button type="submit" disabled={pending || disabled} className="w-full">
      {pending ? "Reading the job…" : label}
    </Button>
  );
}

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

      <Submit label={label} disabled={disabled} />

      {state.error ? (
        <p role="alert" className="text-xs text-destructive">
          {state.error}
        </p>
      ) : null}
    </form>
  );
}

"use client";

import { AlertCircle, Check } from "lucide-react";
import { useActionState } from "react";

import {
  completeStep,
  generateRoadmap,
  type RoadmapActionState,
} from "@/app/(app)/roadmap/actions";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PendingFieldset, SubmitButton } from "@/components/ui/submit-button";

export function GenerateRoadmap({ targetRole }: { targetRole: string | null }) {
  const [state, action] = useActionState<RoadmapActionState, FormData>(
    generateRoadmap,
    {},
  );

  return (
    <form action={action} className="flex flex-col gap-3 sm:flex-row sm:items-end">
      <PendingFieldset>
        <div className="flex-1 space-y-1.5">
          <Label htmlFor="target_role" className="text-sm font-medium">Target role</Label>
          <Input
            key={targetRole ?? ""}
            id="target_role"
            name="target_role"
            defaultValue={targetRole ?? ""}
            placeholder="Staff Engineer"
            maxLength={200}
            required
            aria-required="true"
          />
        </div>
      </PendingFieldset>
      <SubmitButton idle="Build my roadmap" busy="Planning…" />
      {state.error ? (
        <div role="alert" className="flex items-start gap-2.5 rounded-lg bg-destructive/10 px-3.5 py-2.5 text-xs text-destructive sm:self-center">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-destructive" />
          <span>{state.error}</span>
        </div>
      ) : null}
    </form>
  );
}

export function CompleteStep({
  stepId,
  done,
}: {
  stepId: string;
  done: boolean;
}) {
  const [state, action] = useActionState<RoadmapActionState, FormData>(
    completeStep,
    {},
  );

  if (done) {
    return (
      <span className="inline-flex items-center gap-1.5 text-xs text-primary">
        <Check className="h-3.5 w-3.5" />
        Done
      </span>
    );
  }

  return (
    <form action={action}>
      <input type="hidden" name="step_id" value={stepId} />
      <SubmitButton idle="Mark done" busy="Saving…" />
      {state.error ? (
        <p role="alert" className="mt-1 flex items-center gap-1.5 text-xs text-destructive">
          <AlertCircle className="h-3.5 w-3.5 shrink-0" />
          <span>{state.error}</span>
        </p>
      ) : null}
    </form>
  );
}

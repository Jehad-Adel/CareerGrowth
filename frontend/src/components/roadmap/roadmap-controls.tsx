"use client";

import { Check } from "lucide-react";
import { useActionState } from "react";
import { useFormStatus } from "react-dom";

import {
  completeStep,
  generateRoadmap,
  type RoadmapActionState,
} from "@/app/(app)/roadmap/actions";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

function Pending({ idle, busy }: { idle: string; busy: string }) {
  const { pending } = useFormStatus();
  return (
    <Button type="submit" disabled={pending}>
      {pending ? busy : idle}
    </Button>
  );
}

export function GenerateRoadmap({ targetRole }: { targetRole: string | null }) {
  const [state, action] = useActionState<RoadmapActionState, FormData>(
    generateRoadmap,
    {},
  );

  return (
    <form action={action} className="flex flex-col gap-3 sm:flex-row sm:items-end">
      <div className="flex-1 space-y-1.5">
        <Label htmlFor="target_role">Target role</Label>
        <Input
          id="target_role"
          name="target_role"
          defaultValue={targetRole ?? ""}
          placeholder="Staff Engineer"
          maxLength={200}
        />
      </div>
      <Pending idle="Build my roadmap" busy="Planning…" />
      {state.error ? (
        <p role="alert" className="text-xs text-destructive sm:self-center">
          {state.error}
        </p>
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
      <Pending idle="Mark done" busy="Saving…" />
      {state.error ? (
        <p role="alert" className="mt-1 text-xs text-destructive">
          {state.error}
        </p>
      ) : null}
    </form>
  );
}

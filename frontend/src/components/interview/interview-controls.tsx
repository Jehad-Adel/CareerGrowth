"use client";

import { useActionState } from "react";

import {
  startInterview,
  submitAnswer,
  type InterviewActionState,
} from "@/app/(app)/interview/actions";
import { DictateField } from "@/components/ui/dictate-field";
import { Label } from "@/components/ui/label";
import { PendingFieldset, SubmitButton } from "@/components/ui/submit-button";
import { Textarea } from "@/components/ui/textarea";
import type { InterviewLevel } from "@/lib/services";

const LEVELS: { value: InterviewLevel; label: string; blurb: string }[] = [
  {
    value: "friendly_hr",
    label: "Friendly HR",
    blurb: "Supportive and calm. Builds confidence.",
  },
  {
    value: "technical_lead",
    label: "Technical lead",
    blurb: "Direct. Challenges shallow answers with follow-ups.",
  },
  {
    value: "stress_interview",
    label: "Stress interview",
    blurb: "High pressure. Scenario-based, fast-paced.",
  },
];

export function StartInterview() {
  const [state, action] = useActionState<InterviewActionState, FormData>(
    startInterview,
    {},
  );

  return (
    <form action={action} className="space-y-5">
      <PendingFieldset>
        <div className="space-y-5">
          <fieldset className="space-y-2">
            <legend className="mb-2 text-sm font-medium">Interviewer</legend>
            {LEVELS.map((level, i) => (
              <label
                key={level.value}
                className="flex cursor-pointer items-start gap-3 rounded-xl border p-3 transition-colors hover:border-primary/50 has-[:checked]:border-primary has-[:checked]:bg-primary/5 has-[:disabled]:cursor-progress"
              >
                <input
                  type="radio"
                  name="level"
                  value={level.value}
                  defaultChecked={i === 0}
                  className="mt-1"
                />
                <span>
                  <span className="block text-sm font-medium">{level.label}</span>
                  <span className="block text-xs text-muted-foreground">
                    {level.blurb}
                  </span>
                </span>
              </label>
            ))}
          </fieldset>

          <div className="space-y-1.5">
            <Label htmlFor="job_description" className="text-sm font-medium">Job description</Label>
            <Textarea
              id="job_description"
              name="job_description"
              rows={8}
              placeholder="Paste the role you're interviewing for…"
            />
          </div>
        </div>
      </PendingFieldset>

      <SubmitButton idle="Start interview" busy="Setting up…" />

      {state.error ? (
        <div role="alert" className="flex items-center gap-2 rounded-lg bg-destructive/10 px-3 py-2 text-xs text-destructive">
          {state.error}
        </div>
      ) : null}
    </form>
  );
}

export function AnswerQuestion({ sessionId }: { sessionId: string }) {
  const [state, action] = useActionState<InterviewActionState, FormData>(
    submitAnswer,
    {},
  );

  return (
    <form action={action} className="space-y-3">
      <input type="hidden" name="session_id" value={sessionId} />
      <PendingFieldset>
        {/* Remounted on each accepted answer, which clears it. Keyed on
            `submittedAt` rather than `ok`, so a validation error does not
            throw away what the user just dictated. */}
        <DictateField
          key={state.submittedAt ?? "first"}
          name="answer"
          rows={6}
          placeholder="Answer out loud — tap the mic and speak, or type here…"
          ariaLabel="Your answer"
        />
      </PendingFieldset>
      <div className="flex items-center gap-3">
        <SubmitButton idle="Submit answer" busy="Thinking…" />
        {state.error ? (
          <div role="alert" className="flex items-center gap-2 rounded-lg bg-destructive/10 px-3 py-1.5 text-xs text-destructive">
            {state.error}
          </div>
        ) : null}
      </div>
    </form>
  );
}

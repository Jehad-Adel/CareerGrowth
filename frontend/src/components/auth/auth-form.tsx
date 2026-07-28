"use client";

import { useActionState } from "react";
import { useFormStatus } from "react-dom";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { AuthState } from "@/lib/validation/auth";

type Field = {
  name: string;
  label: string;
  type?: string;
  placeholder?: string;
  autoComplete?: string;
};

function SubmitButton({ label }: { label: string }) {
  const { pending } = useFormStatus();
  return (
    <Button type="submit" className="w-full" disabled={pending}>
      {pending ? "Working…" : label}
    </Button>
  );
}

function formatInitialError(err?: string) {
  if (!err) return undefined;
  if (err === "invalid_code") {
    return "That confirmation link is expired or invalid. Please try logging in or sign up again.";
  }
  if (err === "missing_code") {
    return "Could not confirm your email address. Please try logging in.";
  }
  return err;
}

export function AuthForm({
  action,
  fields,
  submitLabel,
  next,
  initialNotice,
  initialError,
}: {
  action: (prev: AuthState, formData: FormData) => Promise<AuthState>;
  fields: Field[];
  submitLabel: string;
  next?: string;
  initialNotice?: string;
  initialError?: string;
}) {
  const [state, formAction] = useActionState<AuthState, FormData>(action, {});
  const notice = state.notice || initialNotice;
  const formError = state.formError || formatInitialError(initialError);

  return (
    <form action={formAction} className="mt-6 space-y-4" noValidate>
      {next ? <input type="hidden" name="next" value={next} /> : null}

      {notice ? (
        <p
          role="status"
          className="rounded-lg border border-primary/30 bg-primary/8 px-3 py-2 text-sm text-foreground"
        >
          {notice}
        </p>
      ) : null}

      {formError ? (
        <p
          role="alert"
          className="rounded-lg border border-destructive/40 bg-destructive/8 px-3 py-2 text-sm text-destructive"
        >
          {formError}
        </p>
      ) : null}

      {fields.map((field) => {
        const error = state.fieldErrors?.[field.name];
        const errorId = `${field.name}-error`;
        return (
          <div key={field.name} className="space-y-1.5">
            <Label htmlFor={field.name}>{field.label}</Label>
            <Input
              id={field.name}
              name={field.name}
              type={field.type ?? "text"}
              placeholder={field.placeholder}
              autoComplete={field.autoComplete}
              aria-invalid={error ? true : undefined}
              aria-describedby={error ? errorId : undefined}
            />
            {error ? (
              <p id={errorId} role="alert" className="text-xs text-destructive">
                {error}
              </p>
            ) : null}
          </div>
        );
      })}

      <SubmitButton label={submitLabel} />
    </form>
  );
}

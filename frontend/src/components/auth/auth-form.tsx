"use client";

import { AlertCircle, CheckCircle2, Loader2 } from "lucide-react";
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
    <Button
      type="submit"
      className="w-full h-10 font-medium"
      disabled={pending}
      aria-busy={pending}
    >
      {pending ? (
        <>
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          Working…
        </>
      ) : (
        label
      )}
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
  if (err === "access_denied") {
    return "Access was denied. Please check your account and try again.";
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
        <div
          role="status"
          className="flex items-start gap-2.5 rounded-lg border border-primary/30 bg-primary/8 px-3.5 py-2.5 text-sm text-foreground"
        >
          <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
          <span>{notice}</span>
        </div>
      ) : null}

      {formError ? (
        <div
          role="alert"
          className="flex items-start gap-2.5 rounded-lg border border-destructive/40 bg-destructive/8 px-3.5 py-2.5 text-sm text-destructive"
        >
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-destructive" />
          <span>{formError}</span>
        </div>
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
              required
              aria-invalid={error ? true : undefined}
              aria-describedby={error ? errorId : undefined}
            />
            {error ? (
              <p id={errorId} role="alert" className="flex items-center gap-1.5 text-xs text-destructive">
                <AlertCircle className="h-3 w-3 shrink-0" />
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

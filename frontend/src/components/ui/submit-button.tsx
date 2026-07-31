"use client";

import { Loader2 } from "lucide-react";
import { useFormStatus } from "react-dom";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

/**
 * Submit button wired to the enclosing form's pending state.
 *
 * `useFormStatus` only reports for a form *above* the component reading it, so
 * this must stay a child of the `<form>` — never the element rendering it.
 */
export function SubmitButton({
  idle,
  busy,
  disabled = false,
  className,
  variant,
  size,
}: {
  idle: string;
  busy: string;
  disabled?: boolean;
  className?: string;
  variant?: React.ComponentProps<typeof Button>["variant"];
  size?: React.ComponentProps<typeof Button>["size"];
}) {
  const { pending } = useFormStatus();

  return (
    <Button
      type="submit"
      variant={variant}
      size={size}
      className={className}
      disabled={pending || disabled}
      aria-busy={pending}
    >
      {pending ? (
        <>
          <Loader2 className="animate-spin" />
          {busy}
        </>
      ) : (
        idle
      )}
    </Button>
  );
}

/**
 * Freezes its inputs while the form is submitting. `display: contents` keeps
 * the fieldset out of the layout — it exists only to carry `disabled` down to
 * every control inside, so nobody edits or resubmits a request in flight.
 *
 * Space the enclosing form with `flex flex-col gap-*`, not `space-y-*`.
 * `display: contents` removes this element from the box tree, so:
 *   - any margin a parent `space-y-*` puts on it is discarded, which leaves
 *     the submit button flush against the last field, and
 *   - the fields inside are grandchildren of the form, which
 *     `.space-y-4 > :not(:last-child)` never matches, so they collapse too.
 * A flex container hoists these children into its own layout, so `gap`
 * spaces the fields and the button uniformly. An inner `space-y-*` wrapper
 * (as in `jobs/job-input.tsx`) fixes the fields but not the button.
 */
export function PendingFieldset({
  className,
  children,
}: {
  className?: string;
  children: React.ReactNode;
}) {
  const { pending } = useFormStatus();
  return (
    <fieldset
      disabled={pending}
      className={cn("contents", pending && "cursor-progress", className)}
    >
      {children}
    </fieldset>
  );
}

import { z } from "zod";

export const signInSchema = z.object({
  email: z.string().trim().min(1, "Email is required").email("Enter a valid email"),
  password: z.string().min(1, "Password is required"),
});

export const signUpSchema = z.object({
  name: z
    .string()
    .trim()
    .min(1, "Name is required")
    .max(200, "That name is too long"),
  email: z.string().trim().min(1, "Email is required").email("Enter a valid email"),
  password: z
    .string()
    .min(8, "Use at least 8 characters")
    .max(72, "Passwords are capped at 72 characters"),
});

export type SignInInput = z.infer<typeof signInSchema>;
export type SignUpInput = z.infer<typeof signUpSchema>;

/** Shape returned by every auth server action to `useActionState`. */
export type AuthState = {
  /** Per-field messages, keyed by field name. */
  fieldErrors?: Record<string, string>;
  /** A message about the submission as a whole. */
  formError?: string;
  /** Non-error outcome, e.g. "check your email to confirm". */
  notice?: string;
};

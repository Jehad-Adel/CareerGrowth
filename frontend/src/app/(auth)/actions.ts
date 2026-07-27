"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { createClient } from "@/lib/supabase/server";
import {
  type AuthState,
  signInSchema,
  signUpSchema,
} from "@/lib/validation/auth";

/**
 * One message for every credential failure.
 *
 * Distinguishing "no such account" from "wrong password" is a user-enumeration
 * oracle: it lets anyone check whether an address has an account here. Keep
 * this single constant as the only thing either path returns.
 */
const CREDENTIALS_REJECTED = "That email and password combination is not valid.";

/** Only allow same-origin relative paths, so `next` cannot become an open redirect. */
function safeNext(next: FormDataEntryValue | null): string {
  if (typeof next !== "string") return "/dashboard";
  if (!next.startsWith("/") || next.startsWith("//")) return "/dashboard";
  return next;
}

function fieldErrorsFrom(error: { issues: { path: PropertyKey[]; message: string }[] }) {
  const fieldErrors: Record<string, string> = {};
  for (const issue of error.issues) {
    const key = String(issue.path[0] ?? "");
    if (key && !fieldErrors[key]) fieldErrors[key] = issue.message;
  }
  return fieldErrors;
}

export async function signIn(
  _prev: AuthState,
  formData: FormData,
): Promise<AuthState> {
  const parsed = signInSchema.safeParse({
    email: formData.get("email"),
    password: formData.get("password"),
  });
  if (!parsed.success) {
    return { fieldErrors: fieldErrorsFrom(parsed.error) };
  }

  const supabase = await createClient();
  const { error } = await supabase.auth.signInWithPassword(parsed.data);

  if (error) {
    // Never surface error.message: it differentiates unconfirmed accounts,
    // wrong passwords, and rate limiting.
    return { formError: CREDENTIALS_REJECTED };
  }

  revalidatePath("/", "layout");
  redirect(safeNext(formData.get("next")));
}

export async function signUp(
  _prev: AuthState,
  formData: FormData,
): Promise<AuthState> {
  const parsed = signUpSchema.safeParse({
    name: formData.get("name"),
    email: formData.get("email"),
    password: formData.get("password"),
  });
  if (!parsed.success) {
    return { fieldErrors: fieldErrorsFrom(parsed.error) };
  }

  const supabase = await createClient();
  const { data, error } = await supabase.auth.signUp({
    email: parsed.data.email,
    password: parsed.data.password,
    options: { data: { full_name: parsed.data.name } },
  });

  if (error) {
    return { formError: "Could not create that account. Try again." };
  }

  // This project has email confirmation enabled (mailer_autoconfirm is off),
  // so signUp returns a user with no session. Say so plainly instead of
  // redirecting to an app the user cannot actually enter yet.
  if (!data.session) {
    return {
      notice:
        "Check your email to confirm your account, then log in to start growing.",
    };
  }

  revalidatePath("/", "layout");
  redirect("/dashboard");
}

export async function signOut() {
  const supabase = await createClient();
  await supabase.auth.signOut();
  revalidatePath("/", "layout");
  redirect("/login");
}

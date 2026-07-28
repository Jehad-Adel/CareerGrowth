"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { createClient } from "@/lib/supabase/server";
import {
  type AuthState,
  signInSchema,
  signUpSchema,
} from "@/lib/validation/auth";

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
    const msg = error.message.toLowerCase();
    if (
      msg.includes("confirm") ||
      msg.includes("not confirmed") ||
      error.status === 400 && msg.includes("email")
    ) {
      return {
        formError:
          "Your email address has not been confirmed yet. Please check your inbox for the confirmation link before logging in.",
      };
    }
    if (
      msg.includes("rate limit") ||
      msg.includes("too many") ||
      error.status === 429
    ) {
      return {
        formError:
          "Too many login attempts. Please wait a few minutes and try again.",
      };
    }
    if (
      msg.includes("invalid login") ||
      msg.includes("invalid credentials") ||
      msg.includes("invalid_grant") ||
      msg.includes("not found")
    ) {
      return {
        formError:
          "Invalid email or password. Please check your credentials and try again.",
      };
    }
    return {
      formError:
        error.message ||
        "Could not log in. Please check your credentials and try again.",
    };
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
  // Ensure no stale session exists before creating a new account
  await supabase.auth.signOut();

  const { data, error } = await supabase.auth.signUp({
    email: parsed.data.email,
    password: parsed.data.password,
    options: { data: { full_name: parsed.data.name } },
  });

  if (error) {
    const msg = error.message.toLowerCase();
    if (
      msg.includes("already registered") ||
      msg.includes("already exists") ||
      msg.includes("user already registered") ||
      error.status === 422 && msg.includes("registered")
    ) {
      return {
        formError:
          "An account with this email address already exists. Please log in instead.",
      };
    }
    if (
      msg.includes("rate limit") ||
      msg.includes("too many") ||
      error.status === 429
    ) {
      return {
        formError:
          "Too many signup attempts. Please wait a few minutes before trying again.",
      };
    }
    if (
      msg.includes("password") && (msg.includes("least") || msg.includes("short") || msg.includes("character"))
    ) {
      return {
        formError: "Your password must be at least 8 characters long.",
      };
    }
    return {
      formError:
        error.message || "Could not create that account. Please try again.",
    };
  }

  // When email enumeration protection is enabled in Supabase, calling signUp on an
  // already registered email returns a user with empty identities and no error.
  if (data.user && data.user.identities && data.user.identities.length === 0) {
    return {
      formError:
        "An account with this email address already exists. Please log in instead.",
    };
  }

  // This project has email confirmation enabled (mailer_autoconfirm is off),
  // so signUp returns a user with no session.
  // Never redirect to dashboard as if logged in. Even if a session was returned
  // by Supabase, sign out and redirect to login with confirmation notice.
  if (data.session) {
    await supabase.auth.signOut();
  }

  redirect(
    "/login?notice=" +
      encodeURIComponent(
        "Account created! Please check your email to confirm your account before logging in.",
      ),
  );
}

export async function signOut() {
  const supabase = await createClient();
  await supabase.auth.signOut();
  revalidatePath("/", "layout");
  redirect("/login");
}

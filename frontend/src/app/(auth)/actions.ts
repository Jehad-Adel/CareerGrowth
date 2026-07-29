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
 * Every signup outcome that is not an outright failure ends here — new
 * account, address already registered, or Supabase declining to say which.
 * One destination is the point: differing responses are what leak whether an
 * address has an account.
 */
const CONFIRMATION_NOTICE =
  "/login?notice=" +
  encodeURIComponent(
    "Account created! Please check your email to confirm your account before logging in. If you already had an account, log in instead.",
  );

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
    // "This email is taken" is a registration oracle: anyone can type an
    // address and learn whether its owner uses the product. Supabase's own
    // enumeration protection exists to prevent exactly that, so the answer
    // here is the same neutral confirmation notice a new signup gets — the
    // person who really owns the address finds out by email, and nobody else
    // finds out at all. Same rule as the login form, which never says which
    // half of the credentials was wrong.
    if (
      msg.includes("already registered") ||
      msg.includes("already exists") ||
      msg.includes("user already registered") ||
      (error.status === 422 && msg.includes("registered"))
    ) {
      redirect(CONFIRMATION_NOTICE);
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

  // An empty `identities` array used to be treated as "this address is already
  // registered". It is not a reliable signal: with email confirmation on,
  // GoTrue returns an empty array for *new* signups too, so a perfectly good
  // registration was rejected with "an account already exists" while the
  // confirmation email sat in the person's inbox. The check is gone, and the
  // ambiguous case now resolves the same way as the unambiguous one.
  //
  // This project has email confirmation enabled (mailer_autoconfirm is off),
  // so signUp returns a user with no session. Never redirect as if logged in;
  // if a session ever does come back, drop it first.
  if (data.session) {
    await supabase.auth.signOut();
  }

  redirect(CONFIRMATION_NOTICE);
}

export async function signOut() {
  const supabase = await createClient();
  await supabase.auth.signOut();
  revalidatePath("/", "layout");
  redirect("/login");
}

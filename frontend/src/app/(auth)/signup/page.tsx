import Link from "next/link";
import { connection } from "next/server";

import { signUp } from "@/app/(auth)/actions";
import { AuthForm } from "@/components/auth/auth-form";

// Dynamic on purpose — a prerendered page has no request to take a CSP nonce
// from, so its scripts get blocked and the form never hydrates. `/login` is
// already dynamic because it awaits searchParams.
export default async function SignupPage({
  searchParams,
}: {
  searchParams: Promise<{ notice?: string; error?: string }>;
}) {
  await connection();
  const { notice, error } = await searchParams;

  return (
    <div className="rounded-2xl border bg-card p-8">
      <h1 className="text-2xl">Start growing</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Create your farm in under a minute.
      </p>

      <AuthForm
        action={signUp}
        submitLabel="Create account"
        initialNotice={notice}
        initialError={error}
        fields={[
          {
            name: "name",
            label: "Name",
            placeholder: "Nour Hassan",
            autoComplete: "name",
          },
          {
            name: "email",
            label: "Email",
            type: "email",
            placeholder: "you@example.com",
            autoComplete: "email",
          },
          {
            name: "password",
            label: "Password",
            type: "password",
            placeholder: "At least 8 characters",
            autoComplete: "new-password",
          },
        ]}
      />

      <p className="mt-6 text-center text-sm text-muted-foreground">
        Already have an account?{" "}
        <Link href="/login" className="text-primary hover:underline">
          Log in
        </Link>
      </p>
    </div>
  );
}

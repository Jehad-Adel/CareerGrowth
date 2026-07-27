import Link from "next/link";

import { signUp } from "@/app/(auth)/actions";
import { AuthForm } from "@/components/auth/auth-form";

export default function SignupPage() {
  return (
    <div className="rounded-2xl border bg-card p-8">
      <h1 className="text-2xl">Start growing</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Create your farm in under a minute.
      </p>

      <AuthForm
        action={signUp}
        submitLabel="Create account"
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

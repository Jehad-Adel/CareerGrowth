import Link from "next/link";

import { signIn } from "@/app/(auth)/actions";
import { AuthForm } from "@/components/auth/auth-form";

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ next?: string; notice?: string; error?: string }>;
}) {
  const { next, notice, error } = await searchParams;

  return (
    <div className="rounded-2xl border bg-card p-8">
      <h1 className="text-2xl">Welcome back</h1>
      <p className="mt-1 text-sm text-muted-foreground">Log in to keep growing.</p>

      <AuthForm
        action={signIn}
        submitLabel="Log in"
        next={next}
        initialNotice={notice}
        initialError={error}
        fields={[
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
            placeholder: "••••••••",
            autoComplete: "current-password",
          },
        ]}
      />

      <p className="mt-6 text-center text-sm text-muted-foreground">
        No account?{" "}
        <Link href="/signup" className="text-primary hover:underline">
          Sign up
        </Link>
      </p>
    </div>
  );
}

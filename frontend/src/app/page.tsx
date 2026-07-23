import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6 p-8 text-center">
      <span className="text-5xl">🌱</span>
      <h1 className="text-4xl font-bold tracking-tight">CareerFarm</h1>
      <p className="max-w-md text-muted-foreground">
        Grow your career like a farm. Analyze your profile, close skill gaps,
        and track real progress — all in one connected space.
      </p>
      <Link href="/dashboard" className={buttonVariants({ size: "lg" })}>
        Enter the farm
      </Link>
    </main>
  );
}

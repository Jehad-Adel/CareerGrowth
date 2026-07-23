import Link from "next/link";

import { Plant } from "@/components/farm/plant";
import { buttonVariants } from "@/components/ui/button";
import { stageLabel } from "@/lib/growth";
import type { GrowthStage } from "@/types";

const STAGES: GrowthStage[] = ["seed", "sprout", "growing", "tree"];

const FEATURES = [
  { emoji: "🏡", title: "Dashboard", text: "Your career at a glance — level, progress, next actions." },
  { emoji: "🌱", title: "Career Farm", text: "Skills as plants that grow from seed to tree as you master them." },
  { emoji: "📄", title: "CV Studio", text: "Structured, specific feedback on your CV and ATS readiness." },
  { emoji: "🎯", title: "Job Match", text: "See your fit for a role and what to close before applying." },
  { emoji: "🎤", title: "Interview Coach", text: "Practice questions with feedback that makes you sharper." },
  { emoji: "🗺️", title: "Roadmap", text: "A personalized path toward your target role." },
  { emoji: "💬", title: "Career Chat", text: "Answers grounded in your own profile and progress." },
];

export default function Home() {
  return (
    <div className="min-h-screen">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
        <span className="flex items-center gap-2">
          <span className="grid h-9 w-9 place-items-center rounded-xl bg-primary/12 text-xl">
            🌱
          </span>
          <span className="font-heading text-lg font-semibold">CareerFarm</span>
        </span>
        <nav className="flex items-center gap-2">
          <Link href="/login" className={buttonVariants({ variant: "ghost", size: "sm" })}>
            Log in
          </Link>
          <Link href="/signup" className={buttonVariants({ size: "sm" })}>
            Get started
          </Link>
        </nav>
      </header>

      <main className="mx-auto max-w-6xl px-6">
        <section className="pt-16 pb-20 text-center">
          <p className="font-mono text-xs uppercase tracking-[0.3em] text-muted-foreground">
            AI career growth
          </p>
          <h1 className="mx-auto mt-4 max-w-3xl text-5xl leading-[1.05] tracking-tight sm:text-6xl">
            Grow your career like a farm.
          </h1>
          <p className="mx-auto mt-5 max-w-xl text-lg text-muted-foreground">
            Understand where you stand, find your skill gaps, and take real steps
            to grow — all in one connected space that makes progress visible.
          </p>
          <div className="mt-8 flex items-center justify-center gap-3">
            <Link href="/signup" className={buttonVariants({ size: "lg" })}>
              Start growing
            </Link>
            <Link
              href="/dashboard"
              className={buttonVariants({ variant: "outline", size: "lg" })}
            >
              See the demo
            </Link>
          </div>

          <div className="mx-auto mt-16 max-w-2xl rounded-3xl border bg-card px-8 py-10">
            <div className="flex items-end justify-center gap-6 sm:gap-12">
              {STAGES.map((stage, i) => (
                <div key={stage} className="flex flex-col items-center gap-2">
                  <div className="h-24 w-20">
                    <Plant stage={stage} />
                  </div>
                  <span className="font-mono text-[11px] uppercase tracking-widest text-muted-foreground">
                    {stageLabel[stage]}
                  </span>
                  <span className="font-mono text-[10px] text-muted-foreground/70">
                    {i * 30}%+
                  </span>
                </div>
              ))}
            </div>
            <p className="mt-8 text-sm text-muted-foreground">
              Every skill you build grows a plant. Master it, and it becomes a tree.
            </p>
          </div>
        </section>

        <section className="pb-24">
          <h2 className="mb-8 text-center text-2xl">One connected platform</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((f) => (
              <div key={f.title} className="rounded-2xl border bg-card p-6">
                <span className="text-2xl">{f.emoji}</span>
                <h3 className="mt-3 text-lg">{f.title}</h3>
                <p className="mt-1 text-sm text-muted-foreground">{f.text}</p>
              </div>
            ))}
          </div>
        </section>
      </main>

      <footer className="border-t">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-2 px-6 py-6 text-sm text-muted-foreground">
          <span>© {new Date().getFullYear()} CareerFarm</span>
          <span className="font-mono text-xs">Grow your career like a farm.</span>
        </div>
      </footer>
    </div>
  );
}

import Link from "next/link";

import { LogoMark } from "@/components/brand/logo";
import { Reveal } from "@/components/landing/reveal";
import { buttonVariants } from "@/components/ui/button";

export function ClosingCta() {
  return (
    <section className="cv-section relative overflow-hidden px-6 py-28">
      <div
        aria-hidden
        className="cf-blob pointer-events-none absolute left-1/2 top-1/2 -z-10 h-[440px] w-[440px] -translate-x-1/2 -translate-y-1/2 rounded-full opacity-50 blur-3xl"
        style={{
          background:
            "radial-gradient(circle, color-mix(in oklch, var(--sprout) 40%, transparent), transparent 68%)",
        }}
      />
      <Reveal className="mx-auto max-w-2xl text-center">
        <LogoMark className="mx-auto h-12 w-12 text-primary" />
        <h2 className="mt-4 text-4xl sm:text-5xl">Your career, growing.</h2>
        <p className="mx-auto mt-4 max-w-lg text-muted-foreground">
          Plant your first skill today and watch it grow. Free to start — no card
          required.
        </p>
        <div className="mt-8 flex items-center justify-center gap-3">
          <Link href="/signup" className={buttonVariants({ size: "lg" })}>
            Start growing — free
          </Link>
          <Link
            href="/dashboard"
            className={buttonVariants({ variant: "outline", size: "lg" })}
          >
            See the demo
          </Link>
        </div>
      </Reveal>
    </section>
  );
}

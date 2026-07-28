"use client";

import Link from "next/link";
import { useRef } from "react";
import {
  m,
  useReducedMotion,
  useScroll,
  useTransform,
  type Variants,
} from "motion/react";

import { Plant } from "@/components/farm/plant";
import { buttonVariants } from "@/components/ui/button";
import { stageLabel } from "@/lib/growth";
import { cn } from "@/lib/utils";
import type { GrowthStage } from "@/types";

const STAGES: GrowthStage[] = ["seed", "sprout", "growing", "tree"];
const HEADLINE = ["Grow", "your", "career", "like", "a", "farm."];

const container: Variants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.09, delayChildren: 0.1 } },
};
const word: Variants = {
  hidden: { opacity: 0, y: "0.7em" },
  show: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.7, ease: [0.22, 1, 0.36, 1] },
  },
};

export function Hero() {
  const ref = useRef<HTMLElement>(null);
  const reduce = useReducedMotion();
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start start", "end start"],
  });
  const blobA = useTransform(scrollYProgress, [0, 1], [0, -140]);
  const blobB = useTransform(scrollYProgress, [0, 1], [0, 100]);
  const contentY = useTransform(scrollYProgress, [0, 1], [0, 70]);
  const contentOpacity = useTransform(scrollYProgress, [0, 0.85], [1, 0]);

  return (
    <section ref={ref} className="relative overflow-hidden px-5 pt-28 pb-16 sm:px-6 sm:pt-40 sm:pb-24">
      {/* Depth 0–1 — ambient atmosphere */}
      <m.div
        aria-hidden
        style={{ y: reduce ? 0 : blobA }}
        className="pointer-events-none absolute -top-24 left-1/2 -z-10 h-[520px] w-[520px] -translate-x-1/2"
      >
        <div
          className="cf-blob h-full w-full rounded-full opacity-60 blur-3xl"
          style={{
            background:
              "radial-gradient(circle, color-mix(in oklch, var(--sprout) 45%, transparent), transparent 68%)",
          }}
        />
      </m.div>
      <m.div
        aria-hidden
        style={{ y: reduce ? 0 : blobB }}
        className="pointer-events-none absolute right-[6%] top-40 -z-10 h-72 w-72"
      >
        <div
          className="cf-blob h-full w-full rounded-full opacity-50 blur-3xl"
          style={{
            background:
              "radial-gradient(circle, color-mix(in oklch, var(--harvest) 42%, transparent), transparent 70%)",
          }}
        />
      </m.div>

      <m.div
        style={reduce ? undefined : { y: contentY, opacity: contentOpacity }}
        className="mx-auto max-w-4xl text-center"
      >
        <m.p
          initial={reduce ? false : { opacity: 0, y: 10 }}
          animate={reduce ? undefined : { opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="font-mono text-xs uppercase tracking-[0.35em] text-muted-foreground"
        >
          AI career growth
        </m.p>

        <m.h1
          variants={container}
          initial={reduce ? false : "hidden"}
          animate={reduce ? undefined : "show"}
          aria-label="Grow your career like a farm."
          className="mx-auto mt-5 max-w-3xl text-4xl leading-[1.05] tracking-tight sm:text-6xl sm:leading-[1.03] md:text-7xl"
        >
          {HEADLINE.map((w, i) => (
            <span
              key={i}
              aria-hidden
              className="inline-block overflow-hidden pb-1 align-bottom"
            >
              <m.span
                variants={word}
                className={
                  i >= 3 ? "me-[0.22em] inline-block text-primary" : "me-[0.22em] inline-block"
                }
              >
                {w}
              </m.span>
            </span>
          ))}
        </m.h1>

        <m.p
          initial={reduce ? false : { opacity: 0, y: 12 }}
          animate={reduce ? undefined : { opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.7 }}
          className="mx-auto mt-5 max-w-xl text-base text-muted-foreground sm:mt-6 sm:text-lg"
        >
          Understand where you stand, find your skill gaps, and take real steps
          to grow — in one connected space that makes progress something you can
          actually see.
        </m.p>

        <m.div
          initial={reduce ? false : { opacity: 0, y: 12 }}
          animate={reduce ? undefined : { opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.85 }}
          // Two `lg` buttons side by side are wider than a 375px screen, which
          // squeezed both labels onto two cramped lines. They stack until
          // there is room for a row.
          className="mt-8 flex flex-col items-stretch justify-center gap-3 sm:mt-9 sm:flex-row sm:items-center"
        >
          <Link
            href="/signup"
            className={cn(buttonVariants({ size: "lg" }), "w-full sm:w-auto")}
          >
            Start growing — free
          </Link>
          {/* Was "See the live demo" pointing at /dashboard, which is a
              protected route: a logged-out visitor clicking the demo landed on
              the login screen. This keeps them on the page instead, scrolling
              to the explanation the button promises. */}
          <a
            href="#how"
            className={cn(
              buttonVariants({ variant: "outline", size: "lg" }),
              "w-full sm:w-auto",
            )}
          >
            See how it works
          </a>
        </m.div>
      </m.div>

      {/* Signature — the growth strip */}
      <div className="mx-auto mt-12 max-w-3xl sm:mt-16">
        <div className="rounded-3xl border bg-card/70 px-3 py-8 backdrop-blur-sm sm:px-12 sm:py-10">
          <div className="flex items-end justify-between gap-2 sm:gap-8">
            {STAGES.map((stage, i) => (
              <m.div
                key={stage}
                initial={reduce ? false : { opacity: 0, scale: 0.6, y: 20 }}
                whileInView={reduce ? undefined : { opacity: 1, scale: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{
                  duration: 0.6,
                  delay: 0.15 * i,
                  ease: [0.22, 1, 0.36, 1],
                }}
                className="flex flex-1 flex-col items-center gap-2"
              >
                {/* Five 80px plants plus gaps overflow a phone. They shrink
                    rather than clip, so the whole growth arc stays visible. */}
                <div className="cf-sway h-16 w-12 sm:h-24 sm:w-20" style={{ animationDelay: `${i * 0.4}s` }}>
                  <Plant stage={stage} />
                </div>
                <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                  {stageLabel[stage]}
                </span>
              </m.div>
            ))}
          </div>
          <p className="mt-8 text-center text-sm text-muted-foreground">
            Every skill you build grows a plant. Master it, and it becomes a tree.
          </p>
        </div>
      </div>
    </section>
  );
}

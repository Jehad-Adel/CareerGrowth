"use client";

import Link from "next/link";
import { useRef } from "react";
import {
  motion,
  useReducedMotion,
  useScroll,
  useTransform,
  type Variants,
} from "motion/react";

import { Plant } from "@/components/farm/plant";
import { buttonVariants } from "@/components/ui/button";
import { stageLabel } from "@/lib/growth";
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
    <section ref={ref} className="relative overflow-hidden px-6 pt-40 pb-24">
      {/* Depth 0–1 — ambient atmosphere */}
      <motion.div
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
      </motion.div>
      <motion.div
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
      </motion.div>

      <motion.div
        style={reduce ? undefined : { y: contentY, opacity: contentOpacity }}
        className="mx-auto max-w-4xl text-center"
      >
        <motion.p
          initial={reduce ? false : { opacity: 0, y: 10 }}
          animate={reduce ? undefined : { opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="font-mono text-xs uppercase tracking-[0.35em] text-muted-foreground"
        >
          AI career growth
        </motion.p>

        <motion.h1
          variants={container}
          initial={reduce ? false : "hidden"}
          animate={reduce ? undefined : "show"}
          aria-label="Grow your career like a farm."
          className="mx-auto mt-5 max-w-3xl text-5xl leading-[1.03] tracking-tight sm:text-7xl"
        >
          {HEADLINE.map((w, i) => (
            <span
              key={i}
              aria-hidden
              className="inline-block overflow-hidden pb-1 align-bottom"
            >
              <motion.span
                variants={word}
                className={
                  i >= 3 ? "mr-[0.22em] inline-block text-primary" : "mr-[0.22em] inline-block"
                }
              >
                {w}
              </motion.span>
            </span>
          ))}
        </motion.h1>

        <motion.p
          initial={reduce ? false : { opacity: 0, y: 12 }}
          animate={reduce ? undefined : { opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.7 }}
          className="mx-auto mt-6 max-w-xl text-lg text-muted-foreground"
        >
          Understand where you stand, find your skill gaps, and take real steps
          to grow — in one connected space that makes progress something you can
          actually see.
        </motion.p>

        <motion.div
          initial={reduce ? false : { opacity: 0, y: 12 }}
          animate={reduce ? undefined : { opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.85 }}
          className="mt-9 flex items-center justify-center gap-3"
        >
          <Link href="/signup" className={buttonVariants({ size: "lg" })}>
            Start growing — free
          </Link>
          <Link
            href="/dashboard"
            className={buttonVariants({ variant: "outline", size: "lg" })}
          >
            See the live demo
          </Link>
        </motion.div>
      </motion.div>

      {/* Signature — the growth strip */}
      <div className="mx-auto mt-16 max-w-3xl">
        <div className="rounded-3xl border bg-card/70 px-6 py-10 backdrop-blur-sm sm:px-12">
          <div className="flex items-end justify-between gap-2 sm:gap-8">
            {STAGES.map((stage, i) => (
              <motion.div
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
                <div className="h-24 w-20 cf-sway" style={{ animationDelay: `${i * 0.4}s` }}>
                  <Plant stage={stage} />
                </div>
                <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                  {stageLabel[stage]}
                </span>
              </motion.div>
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

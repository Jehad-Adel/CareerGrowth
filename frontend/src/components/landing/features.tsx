"use client";

import {
  FileText,
  Home,
  Map,
  MessageCircle,
  Mic,
  Target,
  type LucideIcon,
} from "lucide-react";
import { motion, useReducedMotion, type Variants } from "motion/react";

import { Plant } from "@/components/farm/plant";
import type { GrowthStage } from "@/types";

const OTHER: { icon: LucideIcon; title: string; text: string }[] = [
  { icon: Home, title: "Dashboard", text: "Your level, progress, and next actions in one glance." },
  { icon: FileText, title: "CV Studio", text: "Specific, structured feedback and ATS readiness." },
  { icon: Target, title: "Job Match", text: "See your fit for a role and what to close first." },
  { icon: Mic, title: "Interview Coach", text: "Practice questions with feedback that sharpens you." },
  { icon: Map, title: "Roadmap", text: "A personalized path toward your target role." },
  { icon: MessageCircle, title: "Career Chat", text: "Answers grounded in your own profile." },
];

const SHOWCASE_STAGES: GrowthStage[] = ["seed", "sprout", "growing", "tree"];

const grid: Variants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.07 } },
};
const item: Variants = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] } },
};

export function Features() {
  const reduce = useReducedMotion();

  return (
    <section id="features" className="mx-auto max-w-6xl px-6 py-24">
      <div className="mx-auto mb-14 max-w-2xl text-center">
        <p className="mb-3 font-mono text-xs uppercase tracking-widest text-muted-foreground">
          The platform
        </p>
        <h2 className="text-3xl sm:text-4xl">Everything your career needs, in one place</h2>
      </div>

      {/* Signature feature — the farm */}
      <motion.div
        initial={reduce ? false : { opacity: 0, y: 24 }}
        whileInView={reduce ? undefined : { opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-80px" }}
        transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
        className="grid items-center gap-8 overflow-hidden rounded-3xl border bg-card p-8 sm:p-10 lg:grid-cols-2"
      >
        <div>
          <span className="text-2xl">🌱</span>
          <h3 className="mt-3 text-2xl">The Career Farm</h3>
          <p className="mt-2 max-w-md text-muted-foreground">
            Your signature view. Skills are plants that grow from seed to tree as
            you build mastery — so progress stops being a checklist and starts
            feeling like something alive.
          </p>
        </div>
        <div className="flex items-end justify-center gap-4 rounded-2xl bg-[linear-gradient(to_bottom,transparent_60%,color-mix(in_oklch,var(--soil)_12%,transparent))] py-6 sm:gap-8">
          {SHOWCASE_STAGES.map((stage, i) => (
            <div
              key={stage}
              className="h-24 w-20 cf-sway"
              style={{ animationDelay: `${i * 0.35}s` }}
            >
              <Plant stage={stage} />
            </div>
          ))}
        </div>
      </motion.div>

      {/* The rest */}
      <motion.div
        variants={grid}
        initial={reduce ? false : "hidden"}
        whileInView={reduce ? undefined : "show"}
        viewport={{ once: true, margin: "-60px" }}
        className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
      >
        {OTHER.map((f) => (
          <motion.div
            key={f.title}
            variants={item}
            whileHover={reduce ? undefined : { y: -4 }}
            transition={{ type: "spring", stiffness: 300, damping: 20 }}
            className="rounded-2xl border bg-card p-6"
          >
            <span className="grid h-11 w-11 place-items-center rounded-xl bg-primary/12">
              <f.icon className="h-5 w-5 text-primary" />
            </span>
            <h3 className="mt-4 text-lg">{f.title}</h3>
            <p className="mt-1 text-sm text-muted-foreground">{f.text}</p>
          </motion.div>
        ))}
      </motion.div>
    </section>
  );
}

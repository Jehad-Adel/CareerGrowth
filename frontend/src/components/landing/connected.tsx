"use client";

import {
  FileText,
  Map,
  MessageCircle,
  Mic,
  Sprout,
  Target,
  type LucideIcon,
} from "lucide-react";
import { m, useReducedMotion } from "motion/react";

import { LogoMark } from "@/components/brand/logo";

const NODES: { label: string; icon: LucideIcon; x: number; y: number }[] = [
  { label: "CV Studio", icon: FileText, x: 50, y: 11 },
  { label: "Roadmap", icon: Map, x: 84, y: 31 },
  { label: "Job Match", icon: Target, x: 84, y: 69 },
  { label: "Interview", icon: Mic, x: 50, y: 89 },
  { label: "Career Chat", icon: MessageCircle, x: 16, y: 69 },
  { label: "Career Farm", icon: Sprout, x: 16, y: 31 },
];

export function Connected() {
  const reduce = useReducedMotion();

  return (
    <section id="connected" className="cv-section mx-auto max-w-6xl px-6 py-24">
      <div className="mx-auto max-w-2xl text-center">
        <p className="mb-3 font-mono text-xs uppercase tracking-widest text-muted-foreground">
          Connected
        </p>
        <h2 className="text-3xl sm:text-4xl">Every feature feeds the next</h2>
        <p className="mt-3 text-muted-foreground">
          Your profile sits at the center. Analyzing your CV grows your farm;
          your gaps build your roadmap; finishing a step preps you for the job.
          Nothing is a silo.
        </p>
      </div>

      <div className="relative mx-auto mt-16 aspect-square w-full max-w-lg">
        <svg
          viewBox="0 0 100 100"
          className="absolute inset-0 h-full w-full"
          aria-hidden
        >
          {NODES.map((n, i) => (
            <m.line
              key={n.label}
              x1="50"
              y1="50"
              x2={n.x}
              y2={n.y}
              stroke="var(--primary)"
              strokeWidth="0.4"
              strokeLinecap="round"
              initial={reduce ? false : { pathLength: 0, opacity: 0 }}
              whileInView={reduce ? undefined : { pathLength: 1, opacity: 0.5 }}
              viewport={{ once: true, margin: "-60px" }}
              transition={{ duration: 0.8, delay: 0.12 * i, ease: "easeOut" }}
            />
          ))}
        </svg>

        {/* Center node */}
        <m.div
          initial={reduce ? false : { scale: 0.7, opacity: 0 }}
          whileInView={reduce ? undefined : { scale: 1, opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
          className="absolute left-1/2 top-1/2 grid h-28 w-28 -translate-x-1/2 -translate-y-1/2 place-items-center rounded-full border border-primary/30 bg-primary text-center text-primary-foreground shadow-lg"
        >
          <span>
            <LogoMark className="mx-auto h-6 w-6" />
            <span className="mt-1 block text-xs font-medium leading-tight">
              Your
              <br />
              profile
            </span>
          </span>
        </m.div>

        {/* Feature chips */}
        {NODES.map((n, i) => (
          <m.div
            key={n.label}
            style={{ left: `${n.x}%`, top: `${n.y}%` }}
            initial={reduce ? false : { scale: 0.6, opacity: 0 }}
            whileInView={reduce ? undefined : { scale: 1, opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4, delay: 0.12 * i + 0.3 }}
            className="absolute -translate-x-1/2 -translate-y-1/2"
          >
            <div className="flex items-center gap-1.5 whitespace-nowrap rounded-full border bg-card px-3 py-1.5 text-xs font-medium shadow-sm">
              <n.icon className="h-3.5 w-3.5 text-primary" />
              {n.label}
            </div>
          </m.div>
        ))}
      </div>
    </section>
  );
}

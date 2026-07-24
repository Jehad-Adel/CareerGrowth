import { LineChart, Sprout, Trophy } from "lucide-react";

import { Reveal } from "@/components/landing/reveal";

const STEPS = [
  {
    n: 1,
    icon: LineChart,
    title: "Map where you stand",
    text: "Upload your CV and we analyze your skills, level, and the gaps between you and the role you want.",
  },
  {
    n: 2,
    icon: Sprout,
    title: "Grow with a plan",
    text: "A personalized roadmap turns those gaps into clear next steps — and each skill you build grows on your farm.",
  },
  {
    n: 3,
    icon: Trophy,
    title: "Prove you're ready",
    text: "Practice interviews, check your fit for real jobs, and watch progress compound into trees you can see.",
  },
];

export function Steps() {
  return (
    <section id="how" className="cv-section mx-auto max-w-6xl px-6 py-24">
      <Reveal className="mx-auto mb-14 max-w-2xl text-center">
        <p className="mb-3 font-mono text-xs uppercase tracking-widest text-muted-foreground">
          How it works
        </p>
        <h2 className="text-3xl sm:text-4xl">From lost to growing in three steps</h2>
        <p className="mt-3 text-muted-foreground">
          Most tools solve one piece. CareerFarm connects them, so every bit of
          progress feeds the next.
        </p>
      </Reveal>

      <div className="grid gap-6 md:grid-cols-3">
        {STEPS.map((s, i) => (
          <Reveal key={s.n} delay={i * 0.1}>
            <div className="h-full rounded-2xl border bg-card p-7">
              <div className="mb-5 flex items-center justify-between">
                <span className="grid h-11 w-11 place-items-center rounded-xl bg-primary/12">
                  <s.icon className="h-5 w-5 text-primary" />
                </span>
                <span className="font-mono text-sm text-muted-foreground">
                  0{s.n}
                </span>
              </div>
              <h3 className="text-xl">{s.title}</h3>
              <p className="mt-2 text-sm text-muted-foreground">{s.text}</p>
            </div>
          </Reveal>
        ))}
      </div>
    </section>
  );
}

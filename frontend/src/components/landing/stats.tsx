import { CountUp } from "@/components/landing/count-up";
import { Reveal } from "@/components/landing/reveal";

const STATS = [
  { to: 7, suffix: "", label: "connected features" },
  { to: 4, suffix: "", label: "growth stages" },
  { to: 6, suffix: "", label: "skill categories" },
  { to: 1, suffix: "", label: "profile, one source of truth" },
];

export function Stats() {
  return (
    <section className="border-y bg-card/40 py-16">
      <div className="mx-auto grid max-w-6xl grid-cols-2 gap-8 px-6 text-center md:grid-cols-4">
        {STATS.map((s, i) => (
          <Reveal key={s.label} delay={i * 0.08}>
            <p className="font-heading text-5xl text-primary">
              <CountUp to={s.to} suffix={s.suffix} />
            </p>
            <p className="mt-2 text-sm text-muted-foreground">{s.label}</p>
          </Reveal>
        ))}
      </div>
    </section>
  );
}

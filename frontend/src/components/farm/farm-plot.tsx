import { Plant } from "@/components/farm/plant";
import { masteryToStage, stageLabel } from "@/lib/growth";
import type { Skill, SkillCategory } from "@/types";

const CATEGORY_ORDER: SkillCategory[] = [
  "Languages",
  "Backend",
  "Frontend",
  "Data",
  "DevOps",
  "Foundations",
];

export function SkillPlant({ skill }: { skill: Skill }) {
  const stage = masteryToStage(skill.mastery);
  return (
    <div className="group flex flex-col items-center gap-2">
      <div className="relative flex h-24 w-full items-end justify-center rounded-xl border bg-[linear-gradient(to_bottom,transparent_55%,color-mix(in_oklch,var(--soil)_16%,transparent))] pb-1 transition-colors group-hover:border-primary/40">
        <span className="absolute right-1.5 top-1.5 font-mono text-[10px] text-muted-foreground">
          {skill.mastery}%
        </span>
        <div className="h-20 w-16 transition-transform duration-300 group-hover:-translate-y-0.5">
          <Plant stage={stage} />
        </div>
      </div>
      <div className="text-center">
        <p className="text-sm font-medium leading-tight">{skill.name}</p>
        <p className="font-mono text-[10px] uppercase tracking-wide text-muted-foreground">
          {stageLabel[stage]}
        </p>
      </div>
    </div>
  );
}

export function FarmPlot({ skills }: { skills: Skill[] }) {
  const beds = CATEGORY_ORDER.map(
    (cat) => [cat, skills.filter((s) => s.category === cat)] as const,
  ).filter(([, items]) => items.length > 0);

  return (
    <div className="space-y-8">
      {beds.map(([cat, items]) => (
        <section key={cat}>
          <div className="mb-3 flex items-center gap-3">
            <h3 className="text-lg">{cat}</h3>
            <span className="h-px flex-1 bg-border" />
            <span className="font-mono text-xs text-muted-foreground">
              {items.length} {items.length === 1 ? "plant" : "plants"}
            </span>
          </div>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
            {items.map((s) => (
              <SkillPlant key={s.id} skill={s} />
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}

export function FarmPreview({ skills }: { skills: Skill[] }) {
  return (
    <div className="grid grid-cols-4 gap-3 sm:grid-cols-6">
      {skills.map((s) => (
        <SkillPlant key={s.id} skill={s} />
      ))}
    </div>
  );
}

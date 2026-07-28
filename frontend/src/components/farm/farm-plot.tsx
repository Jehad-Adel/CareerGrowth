import { Plant } from "@/components/farm/plant";
import { stageLabel } from "@/lib/growth";
import type { FarmPlant } from "@/lib/services";

/** Named beds first, in a deliberate order; anything else falls into Other. */
const CATEGORY_ORDER = [
  "Languages",
  "Backend",
  "Frontend",
  "Data",
  "DevOps",
  "Foundations",
] as const;

const OTHER = "Other";

export function SkillPlant({ plant }: { plant: FarmPlant }) {
  // The stage comes from the API. The farm is a server-side projection, and
  // recomputing it here with a second set of thresholds is how the two drift.
  return (
    <div className="group flex flex-col items-center gap-2">
      <div className="relative flex h-24 w-full items-end justify-center rounded-xl border bg-[linear-gradient(to_bottom,transparent_55%,color-mix(in_oklch,var(--soil)_16%,transparent))] pb-1 transition-colors group-hover:border-primary/40">
        <span className="absolute right-1.5 top-1.5 font-mono text-[10px] text-muted-foreground">
          {plant.mastery}%
        </span>
        <div className="h-20 w-16 transition-transform duration-300 group-hover:-translate-y-0.5">
          <Plant stage={plant.stage} />
        </div>
      </div>
      <div className="text-center">
        <p className="text-sm font-medium leading-tight">{plant.name}</p>
        <p className="font-mono text-[10px] uppercase tracking-wide text-muted-foreground">
          {stageLabel[plant.stage]}
        </p>
      </div>
    </div>
  );
}

export function FarmPlot({ plants }: { plants: FarmPlant[] }) {
  const bucket = (p: FarmPlant) =>
    p.category && (CATEGORY_ORDER as readonly string[]).includes(p.category)
      ? p.category
      : OTHER;

  const beds = [...CATEGORY_ORDER, OTHER]
    .map((cat) => [cat, plants.filter((p) => bucket(p) === cat)] as const)
    .filter(([, items]) => items.length > 0);

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
            {items.map((p) => (
              <SkillPlant key={p.id} plant={p} />
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}

export function FarmPreview({ plants }: { plants: FarmPlant[] }) {
  return (
    <div className="grid grid-cols-3 gap-3 sm:grid-cols-6">
      {plants.map((p) => (
        <SkillPlant key={p.id} plant={p} />
      ))}
    </div>
  );
}

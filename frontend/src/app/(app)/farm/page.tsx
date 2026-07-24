import { Sprout, Wheat } from "lucide-react";

import { FarmPlot } from "@/components/farm/farm-plot";
import { Plant } from "@/components/farm/plant";
import { PageHeader } from "@/components/layout/page-header";
import { Stat } from "@/components/layout/stat";
import { Progress } from "@/components/ui/progress";
import { stageLabel } from "@/lib/growth";
import { getFarm } from "@/lib/services";
import type { GrowthStage } from "@/types";

const LEGEND: { stage: GrowthStage; range: string }[] = [
  { stage: "seed", range: "0–19%" },
  { stage: "sprout", range: "20–49%" },
  { stage: "growing", range: "50–79%" },
  { stage: "tree", range: "80–100%" },
];

export default async function FarmPage() {
  const { skills, goals } = await getFarm();

  const trees = skills.filter((s) => s.mastery >= 80).length;
  const growing = skills.filter((s) => s.mastery >= 50 && s.mastery < 80).length;
  const seeds = skills.filter((s) => s.mastery < 20).length;

  return (
    <>
      <PageHeader
        eyebrow="My Farm"
        title="Your career, growing"
        subtitle="Each plant is a skill. It grows from seed to tree as you build mastery — so progress is something you can actually see."
      />

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Stat label="Total plants" value={skills.length} hint="skills tracked" />
        <Stat label="Mastered" value={trees} hint="fully grown trees" />
        <Stat label="Growing well" value={growing} hint="50%+ mastery" />
        <Stat label="Seeds" value={seeds} hint="just planted" />
      </div>

      <div className="mt-6 flex flex-wrap items-center gap-x-8 gap-y-4 rounded-2xl border bg-card px-6 py-4">
        <span className="font-mono text-xs uppercase tracking-widest text-muted-foreground">
          Growth stages
        </span>
        {LEGEND.map(({ stage, range }) => (
          <div key={stage} className="flex items-center gap-2">
            <div className="h-9 w-8">
              <Plant stage={stage} />
            </div>
            <div className="leading-tight">
              <p className="text-sm">{stageLabel[stage]}</p>
              <p className="font-mono text-[10px] text-muted-foreground">{range}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-8 rounded-2xl border bg-card p-6">
        <FarmPlot skills={skills} />
      </div>

      <section className="mt-8">
        <div className="mb-3 flex items-center gap-3">
          <h2 className="text-lg">Harvest</h2>
          <span className="h-px flex-1 bg-border" />
          <span className="font-mono text-xs text-muted-foreground">goals</span>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {goals.map((g) => (
            <div key={g.id} className="rounded-2xl border bg-card p-5">
              <div className="mb-2 flex items-center justify-between gap-3">
                <span className="text-sm font-medium">{g.title}</span>
                {g.status === "done" ? (
                  <Wheat className="h-5 w-5 shrink-0 text-[var(--harvest)]" />
                ) : (
                  <Sprout className="h-5 w-5 shrink-0 text-primary" />
                )}
              </div>
              <Progress value={g.progress} className="h-1.5" />
              <p className="mt-2 font-mono text-[11px] text-muted-foreground">
                {g.status === "done" ? "Harvested" : `${g.progress}% · due ${g.due}`}
              </p>
            </div>
          ))}
        </div>
      </section>
    </>
  );
}

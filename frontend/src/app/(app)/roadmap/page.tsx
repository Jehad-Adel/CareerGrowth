import { Sprout } from "lucide-react";
import Link from "next/link";

import { CompleteStep, GenerateRoadmap } from "@/components/roadmap/roadmap-controls";
import { PageHeader } from "@/components/layout/page-header";
import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";
import { getCvStatus, getProfile, getRoadmapData } from "@/lib/services";

export default async function RoadmapPage() {
  const [status, profile, roadmap] = await Promise.all([
    getCvStatus(),
    getProfile(),
    getRoadmapData(),
  ]);

  const header = (
    <PageHeader
      eyebrow="Roadmap"
      title="The path from here to there"
      subtitle="Built from the skills your profile actually proves — with prerequisites ordered before what depends on them."
    />
  );

  if (!status.has_cv) {
    return (
      <>
        {header}
        <section className="rounded-2xl border border-dashed bg-card p-10 text-center">
          <Sprout className="mx-auto h-8 w-8 text-primary" />
          <h2 className="mt-3 text-lg">Analyze your CV first</h2>
          <p className="mx-auto mt-1 max-w-sm text-sm text-muted-foreground">
            A roadmap plans from where you actually are, so it needs to know
            that first.
          </p>
          <Link href="/cv" className={`${buttonVariants()} mt-4`}>
            Go to CV Studio
          </Link>
        </section>
      </>
    );
  }

  const done = roadmap?.steps.filter((s) => s.status === "done").length ?? 0;
  const total = roadmap?.steps.length ?? 0;
  const pct = total > 0 ? Math.round((done / total) * 100) : 0;

  return (
    <>
      {header}

      <section className="mb-6 rounded-2xl border bg-card p-6">
        <GenerateRoadmap targetRole={roadmap?.target_role ?? profile.targetRole} />
        {roadmap ? (
          <p className="mt-3 text-xs text-muted-foreground">
            Rebuilding replaces the plan below with a fresh one. Completed steps
            stay in your history — the farm grew from them already.
          </p>
        ) : null}
      </section>

      {!roadmap ? (
        <section className="rounded-2xl border border-dashed bg-card p-10 text-center text-sm text-muted-foreground">
          No roadmap yet. Name a target role above and we&apos;ll plan the route.
        </section>
      ) : (
        <>
          <section className="mb-6 rounded-2xl border bg-card p-6">
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <h2 className="text-lg">Toward {roadmap.target_role}</h2>
              <span className="font-mono text-xs text-muted-foreground">
                {done}/{total} steps · ~{roadmap.total_estimated_months} months
              </span>
            </div>
            <p className="mt-1.5 text-sm text-muted-foreground">
              {roadmap.summary}
            </p>
            <Progress value={pct} className="mt-4 h-1.5" />
          </section>

          <ol className="space-y-4">
            {roadmap.steps.map((step, i) => (
              <li
                key={step.id}
                className={cn(
                  "rounded-2xl border bg-card p-6",
                  step.status === "done" && "opacity-70",
                )}
              >
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2.5">
                      <span className="font-mono text-xs text-muted-foreground">
                        {String(i + 1).padStart(2, "0")}
                      </span>
                      <h3
                        className={cn(
                          "text-base",
                          step.status === "done" && "line-through",
                        )}
                      >
                        {step.title}
                      </h3>
                      <Badge variant="outline">
                        ~{step.estimated_months} mo
                      </Badge>
                    </div>
                    <p className="mt-2 text-sm text-muted-foreground">
                      {step.description}
                    </p>

                    {step.skills_to_acquire.length > 0 ? (
                      <div className="mt-3 flex flex-wrap gap-1.5">
                        {step.skills_to_acquire.map((s) => (
                          <Badge key={s} variant="secondary">
                            {s}
                          </Badge>
                        ))}
                      </div>
                    ) : null}

                    {step.prerequisite_skills.length > 0 ? (
                      <p className="mt-2 text-xs text-muted-foreground">
                        Needs first: {step.prerequisite_skills.join(", ")}
                      </p>
                    ) : null}
                  </div>

                  <CompleteStep
                    stepId={step.id}
                    done={step.status === "done"}
                  />
                </div>
              </li>
            ))}
          </ol>
        </>
      )}
    </>
  );
}

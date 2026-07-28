import { Sprout } from "lucide-react";
import Link from "next/link";
import { Suspense } from "react";

import { CompleteStep, GenerateRoadmap } from "@/components/roadmap/roadmap-controls";
import { PageHeader } from "@/components/layout/page-header";
import { RoadmapSkeleton } from "@/components/skeletons";
import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  getProfile,
  getRoadmapById,
  getRoadmapData,
  getRoadmapHistory,
  type RoadmapRecord,
} from "@/lib/services";
import { cn } from "@/lib/utils";

function RoadmapHistoryBar({
  history,
  activeId,
}: {
  history: RoadmapRecord[];
  activeId: string | undefined;
}) {
  if (history.length === 0) return null;

  return (
    <section className="mb-6 rounded-2xl border bg-card p-5">
      <div className="flex items-center justify-between gap-2 mb-3">
        <h3 className="text-sm font-semibold">Roadmap History</h3>
        <span className="font-mono text-xs text-muted-foreground">
          {history.length} {history.length === 1 ? "roadmap" : "roadmaps"} saved
        </span>
      </div>
      <div className="flex flex-wrap gap-2.5">
        {history.map((r, index) => {
          const isLatest = index === 0;
          const isActive = activeId ? r.id === activeId : isLatest;
          const done = r.steps.filter((s) => s.status === "done").length;
          const total = r.steps.length;
          const createdDate = r.created_at ? new Date(r.created_at).toLocaleDateString() : "";
          return (
            <Link
              key={r.id}
              href={isLatest ? "/roadmap" : `/roadmap?id=${r.id}`}
              className={cn(
                "min-h-11 flex items-center gap-2.5 rounded-xl border px-4 py-2 text-xs transition-all hover:border-primary/60 hover:shadow-sm focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1",
                isActive
                  ? "border-primary bg-primary/10 text-foreground font-semibold shadow-sm"
                  : "bg-background text-muted-foreground",
              )}
            >
              <span className="truncate max-w-[160px] sm:max-w-[220px]">{r.target_role}</span>
              <span className="rounded-md bg-muted px-1.5 py-0.5 font-mono text-[11px] text-foreground">
                {done}/{total}
              </span>
              {createdDate ? (
                <span className="hidden sm:inline font-mono text-[10px] text-muted-foreground">
                  {createdDate}
                </span>
              ) : null}
              {isLatest && (
                <span className="rounded bg-primary/20 px-1.5 py-0.5 text-[10px] font-medium text-primary">
                  Latest
                </span>
              )}
            </Link>
          );
        })}
      </div>
    </section>
  );
}

export default async function RoadmapPage({
  searchParams,
}: {
  searchParams: Promise<{ id?: string }>;
}) {
  const profile = await getProfile();
  const { id: selectedId } = await searchParams;

  const header = (
    <PageHeader
      eyebrow="Roadmap"
      title="The path from here to there"
      subtitle="Built from the skills your profile actually proves — with prerequisites ordered before what depends on them."
    />
  );

  if (!profile.hasCv) {
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

  return (
    <>
      {header}
      <Suspense fallback={<RoadmapSkeleton />}>
        <RoadmapBody
          fallbackTarget={profile.targetRole}
          selectedId={selectedId}
        />
      </Suspense>
    </>
  );
}

/** The plan itself. Streams in behind the header rather than blocking it. */
async function RoadmapBody({
  fallbackTarget,
  selectedId,
}: {
  fallbackTarget: string;
  selectedId?: string;
}) {
  const [history, defaultRoadmap] = await Promise.all([
    getRoadmapHistory().catch(() => []),
    getRoadmapData(),
  ]);

  const roadmap = selectedId
    ? (await getRoadmapById(selectedId)) ?? defaultRoadmap
    : defaultRoadmap;

  const done = roadmap?.steps.filter((s) => s.status === "done").length ?? 0;
  const total = roadmap?.steps.length ?? 0;
  const pct = total > 0 ? Math.round((done / total) * 100) : 0;

  return (
    <>
      <RoadmapHistoryBar history={history} activeId={selectedId} />
      <section className="mb-6 rounded-2xl border bg-card p-6">
        <GenerateRoadmap targetRole={roadmap?.target_role ?? fallbackTarget} />
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
                  "rounded-2xl border bg-card p-5 sm:p-6",
                  step.status === "done" && "opacity-70",
                )}
              >
                <div className="flex flex-wrap items-start justify-between gap-3 sm:gap-4">
                  <div className="min-w-0 flex-1">
                    {/* Step number, effort and difficulty on their own line.
                        Sharing a row with the title left the title a sliver of
                        width on a phone — one word per line under two badges
                        that never shrink. */}
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-mono text-xs text-muted-foreground">
                        {String(i + 1).padStart(2, "0")}
                      </span>
                      <Badge variant="outline">
                        ~{step.estimated_months} mo
                        {step.estimated_weekly_hours > 0 &&
                          ` · ${step.estimated_weekly_hours} h/wk`}
                      </Badge>
                      {step.difficulty && (
                        <Badge variant="outline">{step.difficulty}</Badge>
                      )}
                    </div>
                    <h3
                      className={cn(
                        "mt-1.5 text-base break-words",
                        step.status === "done" && "line-through",
                      )}
                    >
                      {step.title}
                    </h3>
                    <p className="mt-2 text-sm text-muted-foreground">
                      {step.description}
                    </p>

                    {/* Empty on roadmaps generated before these fields
                        existed, so every one of them is rendered
                        conditionally rather than as an empty row. */}
                    {step.reason ? (
                      <p className="mt-2 text-sm text-muted-foreground">
                        <span className="text-foreground">Why now: </span>
                        {step.reason}
                      </p>
                    ) : null}

                    {step.skills_to_acquire.length > 0 ? (
                      <div className="mt-3 flex flex-wrap gap-1.5">
                        {step.skills_to_acquire.map((s) => (
                          <Badge
                            key={s}
                            variant="secondary"
                            className="whitespace-normal text-left h-auto max-w-full py-1 leading-relaxed break-words"
                          >
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

                    {step.project_to_practice ? (
                      <p className="mt-2 text-xs text-muted-foreground">
                        Build: {step.project_to_practice}
                      </p>
                    ) : null}

                    {step.recommended_resources.length > 0 ? (
                      // Names, not links — the backend never stores URLs from
                      // a generation, so there is nothing to link to.
                      <p className="mt-2 text-xs text-muted-foreground">
                        Learn from: {step.recommended_resources.join(", ")}
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

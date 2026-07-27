import { Sprout } from "lucide-react";
import Link from "next/link";

import { Suspense } from "react";

import { FarmPlot } from "@/components/farm/farm-plot";
import { PageHeader } from "@/components/layout/page-header";
import { Stat } from "@/components/layout/stat";
import { FarmSkeleton } from "@/components/skeletons";
import { buttonVariants } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { getFarmData, type FarmFeedItem } from "@/lib/services";

/** Every event type the log can emit, rendered as something a person reads. */
function describe(event: FarmFeedItem): string {
  const p = event.payload as Record<string, string>;
  switch (event.type) {
    case "cv_analyzed":
      return `CV analyzed — ${p.skills_found ?? "0"} skills found`;
    case "skill_discovered":
      return `Discovered ${p.skill}`;
    case "skill_leveled":
      return `${p.skill} grew to ${p.mastery}%`;
    case "job_matched":
      return `Matched a job at ${p.score}%`;
    case "gap_analyzed":
      return `Gap analysis — ${p.gap_score}% to close`;
    case "roadmap_created":
      return `Roadmap set toward ${p.target_role}`;
    case "goal_completed":
      return `Completed: ${p.title}`;
    case "interview_completed":
      return "Finished a mock interview";
    default:
      return event.type.replaceAll("_", " ");
  }
}

async function FarmBody() {
  const farm = await getFarmData();
  const pct = Math.round((farm.xp / farm.xp_for_next) * 100);

  return (
    <>
      <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Level" value={`${farm.level} · ${farm.level_title}`} />
        <Stat label="Plants" value={String(farm.counts.total)} />
        <Stat label="Mastered" value={String(farm.counts.trees)} />
        <Stat label="Streak" value={`${farm.streak_days}d`} />
      </div>

      <section className="mb-8 rounded-2xl border bg-card p-6">
        <div className="flex justify-between font-mono text-xs text-muted-foreground">
          <span>
            Level {farm.level} · {farm.level_title}
          </span>
          <span>
            {farm.xp}/{farm.xp_for_next} XP
          </span>
        </div>
        <Progress value={pct} className="mt-2 h-1.5" />
        {farm.roadmap.has_roadmap ? (
          <p className="mt-3 text-xs text-muted-foreground">
            Roadmap toward {farm.roadmap.target_role} —{" "}
            {farm.roadmap.done}/{farm.roadmap.total} steps done.
          </p>
        ) : null}
      </section>

      <div className="grid gap-8 lg:grid-cols-3">
        <div className="lg:col-span-2">
          {farm.plants.length === 0 ? (
            <section className="rounded-2xl border border-dashed bg-card p-10 text-center">
              <Sprout className="mx-auto h-8 w-8 text-primary" />
              <h2 className="mt-3 text-lg">Bare soil</h2>
              <p className="mx-auto mt-1 max-w-sm text-sm text-muted-foreground">
                Analyze your CV and the skills it proves become your first
                plants.
              </p>
              <Link href="/cv" className={`${buttonVariants()} mt-4`}>
                Go to CV Studio
              </Link>
            </section>
          ) : (
            <FarmPlot plants={farm.plants} />
          )}
        </div>

        <aside>
          <h2 className="mb-3 text-lg">Recent growth</h2>
          {farm.feed.length === 0 ? (
            <p className="text-sm text-muted-foreground">Nothing yet.</p>
          ) : (
            <ol className="space-y-3">
              {farm.feed.map((event) => (
                <li
                  key={event.id}
                  className="flex items-start justify-between gap-3 rounded-xl border bg-card px-4 py-3"
                >
                  <div className="min-w-0">
                    <p className="text-sm leading-tight">{describe(event)}</p>
                    <p className="mt-0.5 font-mono text-[10px] text-muted-foreground">
                      {new Date(event.at).toLocaleDateString()}
                    </p>
                  </div>
                  {event.xp > 0 ? (
                    <span className="shrink-0 font-mono text-xs text-primary">
                      +{event.xp}
                    </span>
                  ) : null}
                </li>
              ))}
            </ol>
          )}
        </aside>
      </div>
    </>
  );
}

export default function FarmPage() {
  return (
    <>
      <PageHeader
        eyebrow="Your farm"
        title="What you've grown"
        subtitle="Every plant here came from something you actually did. Nothing is decorative."
      />

      <Suspense fallback={<FarmSkeleton />}>
        <FarmBody />
      </Suspense>
    </>
  );
}

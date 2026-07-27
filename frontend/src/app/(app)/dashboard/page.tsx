import { ArrowRight, Sprout } from "lucide-react";
import Link from "next/link";
import { Suspense } from "react";

import { FarmPreview } from "@/components/farm/farm-plot";
import { PageHeader } from "@/components/layout/page-header";
import { Stat } from "@/components/layout/stat";
import { DashboardSkeleton } from "@/components/skeletons";
import { buttonVariants } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { getDashboardData, getProfile, type Dashboard } from "@/lib/services";

/** The single most useful thing to do next, given what exists so far. */
function nextAction(d: Dashboard) {
  if (!d.has_cv) {
    return {
      title: "Analyze your CV",
      body: "Everything else reads from it — job matching, gaps, and your roadmap.",
      href: "/cv",
      cta: "Go to CV Studio",
    };
  }
  if (!d.farm.roadmap.has_roadmap) {
    return {
      title: "Set a target role",
      body: "We'll plan the route from where you are to where you want to be.",
      href: "/roadmap",
      cta: "Build a roadmap",
    };
  }
  if (d.farm.roadmap.done < d.farm.roadmap.total) {
    const left = d.farm.roadmap.total - d.farm.roadmap.done;
    return {
      title: "Finish your next step",
      body: `${left} ${left === 1 ? "step" : "steps"} left toward ${d.farm.roadmap.target_role}.`,
      href: "/roadmap",
      cta: "Open roadmap",
    };
  }
  return {
    title: "Measure yourself against a role",
    body: "Paste a job description and see honestly where you stand.",
    href: "/jobs",
    cta: "Match a job",
  };
}

/** Everything below the header, from one round trip. */
async function DashboardBody() {
  const data = await getDashboardData();
  const { profile, farm } = data;
  const pct = Math.round((farm.xp / farm.xp_for_next) * 100);
  const next = nextAction(data);

  return (
    <>
      <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label="Level" value={profile.level} hint={profile.level_title} />
        <Stat label="Plants" value={farm.counts.total} hint="skills tracked" />
        <Stat
          label="Mastered"
          value={farm.counts.trees}
          hint={`${farm.counts.seeds} still seeds`}
        />
        <Stat label="Streak" value={`${farm.streak_days}d`} />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <section className="rounded-2xl border bg-card p-6">
            <div className="flex items-center justify-between gap-3">
              <h2 className="text-lg">Your farm</h2>
              <Link
                href="/farm"
                className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
              >
                See all <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>

            {farm.plants.length === 0 ? (
              <div className="mt-6 text-center">
                <Sprout className="mx-auto h-7 w-7 text-primary" />
                <p className="mt-2 text-sm text-muted-foreground">
                  Nothing planted yet.
                </p>
              </div>
            ) : (
              <div className="mt-5">
                <FarmPreview plants={farm.plants.slice(0, 6)} />
              </div>
            )}
          </section>

          <section className="rounded-2xl border bg-card p-6">
            <h2 className="mb-3 text-lg">Recent growth</h2>
            {farm.feed.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                Your activity will show up here.
              </p>
            ) : (
              <ol className="space-y-2.5">
                {farm.feed.slice(0, 6).map((e) => (
                  <li
                    key={e.id}
                    className="flex items-center justify-between gap-3 text-sm"
                  >
                    <span className="truncate">
                      {e.type.replaceAll("_", " ")}
                    </span>
                    <span className="shrink-0 font-mono text-xs text-muted-foreground">
                      {new Date(e.at).toLocaleDateString()}
                      {e.xp > 0 ? ` · +${e.xp}` : ""}
                    </span>
                  </li>
                ))}
              </ol>
            )}
          </section>
        </div>

        <aside className="space-y-6">
          <section className="rounded-2xl border bg-card p-6">
            <div className="flex justify-between font-mono text-xs text-muted-foreground">
              <span>Level {profile.level}</span>
              <span>
                {farm.xp}/{farm.xp_for_next} XP
              </span>
            </div>
            <Progress value={pct} className="mt-2 h-1.5" />
            {farm.roadmap.has_roadmap ? (
              <p className="mt-3 text-xs text-muted-foreground">
                {farm.roadmap.done}/{farm.roadmap.total} roadmap steps done
              </p>
            ) : null}
          </section>

          <section className="rounded-2xl border bg-card p-6">
            <h2 className="text-base">Do this next</h2>
            <p className="mt-1.5 text-sm text-muted-foreground">
              <span className="font-medium text-foreground">{next.title}.</span>{" "}
              {next.body}
            </p>
            <Link
              href={next.href}
              className={`${buttonVariants({ size: "sm" })} mt-4`}
            >
              {next.cta}
            </Link>
          </section>
        </aside>
      </div>
    </>
  );
}

export default async function DashboardPage() {
  // Resolved already by the layout — `cache()` makes this read free, so the
  // greeting paints with the shell instead of waiting on /dashboard.
  const profile = await getProfile();
  const name = profile.name.split(" ")[0];
  const hasTarget = profile.targetRole !== "Not set yet";

  return (
    <>
      <PageHeader
        eyebrow="Dashboard"
        title={`Welcome back, ${name}`}
        subtitle={
          hasTarget
            ? `Growing toward ${profile.targetRole}.`
            : "Let's find out where you're headed."
        }
      />

      <Suspense fallback={<DashboardSkeleton />}>
        <DashboardBody />
      </Suspense>
    </>
  );
}

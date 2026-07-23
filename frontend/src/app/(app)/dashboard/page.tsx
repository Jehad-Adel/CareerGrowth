import Link from "next/link";
import { ArrowRight, Sprout } from "lucide-react";

import { FarmPreview } from "@/components/farm/farm-plot";
import { PageHeader } from "@/components/layout/page-header";
import { Stat } from "@/components/layout/stat";
import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { getDashboard } from "@/lib/services";

export default async function DashboardPage() {
  const { profile, skills, goals, events, recommended } = await getDashboard();

  const firstName = profile.name.split(" ")[0];
  const growing = skills.filter((s) => s.mastery >= 20 && s.mastery < 80).length;
  const mastered = skills.filter((s) => s.mastery >= 80).length;
  const activeGoals = goals.filter((g) => g.status === "active");
  const doneGoals = goals.filter((g) => g.status === "done").length;
  const topSkills = [...skills].sort((a, b) => b.mastery - a.mastery).slice(0, 6);

  return (
    <>
      <PageHeader
        eyebrow={`Level ${profile.level} · ${profile.levelTitle}`}
        title={`Welcome back, ${firstName}`}
        subtitle="Here's how your farm is growing today."
      />

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Stat
          label="Career level"
          value={`Lv ${profile.level}`}
          hint={`${profile.xp}/${profile.xpForNext} XP`}
        />
        <Stat label="Skills growing" value={growing} hint={`${mastered} mastered`} />
        <Stat
          label="Active goals"
          value={activeGoals.length}
          hint={`${doneGoals} completed`}
        />
        <Stat label="CV score" value="74" hint="last analysis" />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <section className="rounded-2xl border bg-card p-6">
            <div className="mb-5 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Sprout className="h-4 w-4 text-primary" />
                <h2 className="text-lg">Your farm</h2>
              </div>
              <Link
                href="/farm"
                className="flex items-center gap-1 text-sm text-primary hover:underline"
              >
                Open farm <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>
            <FarmPreview skills={topSkills} />
          </section>

          <section className="rounded-2xl border bg-card p-6">
            <h2 className="mb-4 text-lg">Recommended next</h2>
            <ul className="divide-y">
              {recommended.map((r) => (
                <li key={r.id} className="flex items-center justify-between gap-4 py-3 first:pt-0 last:pb-0">
                  <span className="text-sm">{r.title}</span>
                  <Link
                    href={r.href}
                    className={buttonVariants({ variant: "outline", size: "sm" })}
                  >
                    {r.cta}
                  </Link>
                </li>
              ))}
            </ul>
          </section>
        </div>

        <div className="space-y-6">
          <section className="rounded-2xl border bg-card p-6">
            <h2 className="mb-4 text-lg">Active goals</h2>
            <ul className="space-y-4">
              {activeGoals.map((g) => (
                <li key={g.id}>
                  <div className="mb-1.5 flex items-center justify-between gap-3 text-sm">
                    <span>{g.title}</span>
                    <span className="font-mono text-xs text-muted-foreground">
                      {g.progress}%
                    </span>
                  </div>
                  <Progress value={g.progress} className="h-1.5" />
                </li>
              ))}
            </ul>
          </section>

          <section className="rounded-2xl border bg-card p-6">
            <h2 className="mb-4 text-lg">Recent growth</h2>
            <ul className="space-y-3">
              {events.map((e) => (
                <li key={e.id} className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm leading-tight">{e.label}</p>
                    <p className="font-mono text-[11px] text-muted-foreground">{e.at}</p>
                  </div>
                  <Badge variant="secondary" className="shrink-0 font-mono">
                    +{e.xp}
                  </Badge>
                </li>
              ))}
            </ul>
          </section>
        </div>
      </div>
    </>
  );
}

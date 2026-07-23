import { ArrowRight, Check, X } from "lucide-react";

import { PageHeader } from "@/components/layout/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScoreRing } from "@/components/ui/score-ring";
import { Textarea } from "@/components/ui/textarea";
import { getJobMatch } from "@/lib/services";

export default async function JobsPage() {
  const job = await getJobMatch();

  return (
    <>
      <PageHeader
        eyebrow="Job Match"
        title="Is this role a fit?"
        subtitle="Paste a job description. See how suitable you are, your relevant strengths, and what to close before applying."
      />

      <div className="grid gap-6 lg:grid-cols-3">
        <section className="rounded-2xl border bg-card p-6 lg:col-span-1">
          <h2 className="mb-3 text-lg">Job description</h2>
          <Textarea
            rows={12}
            placeholder="Paste the full job posting here…"
            className="resize-none"
          />
          <Button className="mt-4 w-full">Evaluate fit</Button>
          <p className="mt-3 text-center text-xs text-muted-foreground">
            Preview uses a sample posting.
          </p>
        </section>

        <section className="space-y-6 lg:col-span-2">
          <div className="rounded-2xl border bg-card p-6">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <h2 className="text-xl">{job.title}</h2>
                <p className="text-sm text-muted-foreground">{job.company}</p>
              </div>
              <ScoreRing value={job.fit} label="Fit" />
            </div>
          </div>

          <div className="grid gap-6 sm:grid-cols-2">
            <div className="rounded-2xl border bg-card p-6">
              <h3 className="mb-3 text-base">You match</h3>
              <div className="flex flex-wrap gap-2">
                {job.matched.map((m) => (
                  <Badge key={m} variant="secondary" className="gap-1">
                    <Check className="h-3 w-3 text-primary" />
                    {m}
                  </Badge>
                ))}
              </div>
            </div>
            <div className="rounded-2xl border bg-card p-6">
              <h3 className="mb-3 text-base">Gaps to close</h3>
              <div className="flex flex-wrap gap-2">
                {job.gaps.map((g) => (
                  <Badge key={g} variant="outline" className="gap-1">
                    <X className="h-3 w-3 text-muted-foreground" />
                    {g}
                  </Badge>
                ))}
              </div>
            </div>
          </div>

          <div className="rounded-2xl border bg-card p-6">
            <h3 className="mb-4 text-base">Before you apply</h3>
            <ul className="space-y-3">
              {job.actions.map((a) => (
                <li key={a} className="flex gap-3 text-sm">
                  <ArrowRight className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                  {a}
                </li>
              ))}
            </ul>
          </div>
        </section>
      </div>
    </>
  );
}

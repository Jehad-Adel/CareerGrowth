import { Check, FileUp, Lightbulb, TriangleAlert } from "lucide-react";

import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { ScoreRing } from "@/components/ui/score-ring";
import { getCvAnalysis } from "@/lib/services";

export default async function CvPage() {
  const cv = await getCvAnalysis();

  return (
    <>
      <PageHeader
        eyebrow="CV Studio"
        title="Sharpen your CV"
        subtitle="Upload your CV for structured, specific feedback — quality, ATS readiness, and what to fix before you apply."
      />

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6">
          <section className="rounded-2xl border bg-card p-6">
            <label className="flex cursor-pointer flex-col items-center gap-3 rounded-xl border border-dashed border-border px-6 py-10 text-center transition-colors hover:border-primary/50 hover:bg-accent/40">
              <FileUp className="h-7 w-7 text-primary" />
              <span className="text-sm font-medium">Drop your CV here</span>
              <span className="text-xs text-muted-foreground">PDF or DOCX, up to 5 MB</span>
              <input type="file" accept=".pdf,.docx" className="hidden" />
            </label>
            <Button className="mt-4 w-full">Analyze CV</Button>
            <p className="mt-3 text-center text-xs text-muted-foreground">
              Preview uses sample results.
            </p>
          </section>

          <section className="rounded-2xl border bg-card p-6">
            <h2 className="mb-4 text-lg">Scores</h2>
            <div className="flex items-center justify-around">
              <ScoreRing value={cv.overall} label="Overall" />
              <ScoreRing value={cv.atsScore} label="ATS" />
            </div>
          </section>
        </div>

        <div className="space-y-6 lg:col-span-2">
          <section className="rounded-2xl border bg-card p-6">
            <h2 className="mb-4 text-lg">Section breakdown</h2>
            <ul className="space-y-4">
              {cv.sections.map((s) => (
                <li key={s.name}>
                  <div className="mb-1.5 flex items-center justify-between gap-3 text-sm">
                    <span className="font-medium">{s.name}</span>
                    <span className="font-mono text-xs text-muted-foreground">
                      {s.score}
                    </span>
                  </div>
                  <Progress value={s.score} className="h-1.5" />
                  <p className="mt-1.5 text-sm text-muted-foreground">{s.note}</p>
                </li>
              ))}
            </ul>
          </section>

          <div className="grid gap-6 sm:grid-cols-2">
            <section className="rounded-2xl border bg-card p-6">
              <h3 className="mb-3 text-base">Strengths</h3>
              <ul className="space-y-2.5">
                {cv.strengths.map((t) => (
                  <li key={t} className="flex gap-2.5 text-sm">
                    <Check className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                    {t}
                  </li>
                ))}
              </ul>
            </section>
            <section className="rounded-2xl border bg-card p-6">
              <h3 className="mb-3 text-base">Missing</h3>
              <ul className="space-y-2.5">
                {cv.missing.map((t) => (
                  <li key={t} className="flex gap-2.5 text-sm">
                    <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0 text-[var(--harvest)]" />
                    {t}
                  </li>
                ))}
              </ul>
            </section>
          </div>

          <section className="rounded-2xl border bg-card p-6">
            <div className="mb-3 flex items-center gap-2">
              <Lightbulb className="h-4 w-4 text-primary" />
              <h3 className="text-base">Suggested rewrites</h3>
            </div>
            <ol className="space-y-3">
              {cv.suggestions.map((t, i) => (
                <li key={t} className="flex gap-3 text-sm">
                  <span className="font-mono text-xs text-muted-foreground">
                    {String(i + 1).padStart(2, "0")}
                  </span>
                  <span>{t}</span>
                </li>
              ))}
            </ol>
          </section>
        </div>
      </div>
    </>
  );
}

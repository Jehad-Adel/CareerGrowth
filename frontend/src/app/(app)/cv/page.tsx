import { Check, Lightbulb, Sprout, TriangleAlert } from "lucide-react";
import { Suspense } from "react";

import { CvUpload } from "@/components/cv/cv-upload";
import { PageHeader } from "@/components/layout/page-header";
import { CvSkeleton } from "@/components/skeletons";
import { Badge } from "@/components/ui/badge";
import { getCvStatus, getLatestCvAnalysis } from "@/lib/services";

function List({
  items,
  icon,
  empty,
}: {
  items: string[];
  icon: React.ReactNode;
  empty: string;
}) {
  if (items.length === 0) {
    return <p className="text-sm text-muted-foreground">{empty}</p>;
  }
  return (
    <ul className="space-y-2.5">
      {items.map((text) => (
        <li key={text} className="flex gap-2.5 text-sm break-words">
          <span className="mt-0.5 shrink-0">{icon}</span>
          <span className="break-words">{text}</span>
        </li>
      ))}
    </ul>
  );
}

async function CvBody() {
  // One round trip each, in parallel — not sequential awaits.
  const [status, analysis] = await Promise.all([
    getCvStatus(),
    getLatestCvAnalysis(),
  ]);

  const remaining = Math.max(status.daily_limit - status.analyses_today, 0);
  const cv = analysis?.result;

  return (
    <>
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6">
          <section className="rounded-2xl border bg-card p-6">
            <CvUpload remaining={remaining} />
          </section>

          {cv ? (
            <section className="rounded-2xl border bg-card p-6">
              <h2 className="mb-4 text-lg">Extracted</h2>
              <dl className="space-y-3 text-sm">
                <div>
                  <dt className="text-muted-foreground">Name</dt>
                  <dd>{cv.full_name ?? "Not found"}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Current role</dt>
                  <dd>{cv.current_role ?? "Not found"}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Seniority</dt>
                  <dd>{cv.seniority_level}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Experience</dt>
                  <dd>
                    {cv.years_of_experience === null
                      ? "Not stated clearly enough to compute"
                      : `${cv.years_of_experience} years`}
                  </dd>
                  {cv.employment_periods && cv.employment_periods.length > 0 && (
                    // Shown because the number is computed, not reported: if
                    // it looks wrong, the dates it was computed from are the
                    // only way to see why.
                    <dd className="mt-1.5 space-y-0.5 text-xs text-muted-foreground">
                      {cv.employment_periods.map((p, i) => (
                        <div key={`${p.company ?? "role"}-${i}`}>
                          {p.start_date ?? "?"} –{" "}
                          {p.is_current ? "now" : (p.end_date ?? "?")}
                          {p.title ? ` · ${p.title}` : ""}
                          {p.company ? ` @ ${p.company}` : ""}
                        </div>
                      ))}
                    </dd>
                  )}
                </div>
                {typeof cv.extraction_confidence === "number" &&
                  cv.extraction_confidence < 80 && (
                    <div>
                      <dt className="text-muted-foreground">
                        Extraction confidence
                      </dt>
                      {/* Only surfaced when it is low. A confident reading is
                          the expected case and does not need a number. */}
                      <dd className="text-[var(--harvest)]">
                        {cv.extraction_confidence}% — check the fields above
                      </dd>
                    </div>
                  )}
              </dl>
            </section>
          ) : null}
        </div>

        <div className="space-y-6 lg:col-span-2">
          {!cv ? (
            <section className="rounded-2xl border border-dashed bg-card p-10 text-center">
              <Sprout className="mx-auto h-8 w-8 text-primary" />
              <h2 className="mt-3 text-lg">Nothing planted yet</h2>
              <p className="mx-auto mt-1 max-w-sm text-sm text-muted-foreground">
                Upload your CV and we&apos;ll pull out your skills, tell you
                honestly what is weak, and grow your farm from what you already
                have.
              </p>
            </section>
          ) : (
            <>
              <section className="rounded-2xl border bg-card p-6">
                <h2 className="mb-2 text-lg">Summary</h2>
                <p className="text-sm text-muted-foreground">{cv.summary}</p>
                <div className="mt-4 flex flex-wrap gap-1.5">
                  {cv.skills.map((skill) => (
                    <Badge
                      key={skill}
                      variant="secondary"
                      className="whitespace-normal text-left h-auto max-w-full py-1 leading-relaxed break-words"
                    >
                      {skill}
                    </Badge>
                  ))}
                </div>
              </section>

              <div className="grid gap-6 sm:grid-cols-2">
                <section className="rounded-2xl border bg-card p-6">
                  <h3 className="mb-3 text-base">Strengths</h3>
                  <List
                    items={cv.strengths}
                    empty="None identified."
                    icon={<Check className="h-4 w-4 text-primary" />}
                  />
                </section>
                <section className="rounded-2xl border bg-card p-6">
                  <h3 className="mb-3 text-base">What weakens it</h3>
                  <List
                    items={cv.weaknesses}
                    empty="Nothing flagged."
                    icon={
                      <TriangleAlert className="h-4 w-4 text-[var(--harvest)]" />
                    }
                  />
                </section>
              </div>

              <section className="rounded-2xl border bg-card p-6">
                <div className="mb-3 flex items-center gap-2">
                  <Lightbulb className="h-4 w-4 text-primary" />
                  <h3 className="text-base">Suggested fixes</h3>
                </div>
                <ol className="space-y-3">
                  {cv.improvement_suggestions.map((text, i) => (
                    <li key={text} className="flex gap-3 text-sm">
                      <span className="font-mono text-xs text-muted-foreground">
                        {String(i + 1).padStart(2, "0")}
                      </span>
                      <span>{text}</span>
                    </li>
                  ))}
                </ol>
              </section>
            </>
          )}
        </div>
      </div>
    </>
  );
}

export default function CvPage() {
  return (
    <>
      <PageHeader
        eyebrow="CV Studio"
        title="Sharpen your CV"
        subtitle="Upload your CV for structured, specific feedback — and to seed your farm with the skills it already proves."
      />

      <Suspense fallback={<CvSkeleton />}>
        <CvBody />
      </Suspense>
    </>
  );
}

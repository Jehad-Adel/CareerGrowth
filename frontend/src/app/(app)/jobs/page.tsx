import { Sprout } from "lucide-react";
import Link from "next/link";
import { Suspense } from "react";

import {
  analyzeGap,
  matchJob,
  writeCoverLetter,
} from "@/app/(app)/jobs/actions";
import { CoverLetterActions } from "@/components/jobs/cover-letter-actions";
import { JobInput } from "@/components/jobs/job-input";
import { PageHeader } from "@/components/layout/page-header";
import { ResultsSkeleton } from "@/components/skeletons";
import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import { ScoreRing } from "@/components/ui/score-ring";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  getLatestCoverLetter,
  getLatestJobMatch,
  getLatestSkillGap,
  getProfile,
  type JobMatchResult,
  type SkillGapItemResult,
  type SkillMatchResult,
} from "@/lib/services";

const PRIORITY_STYLE: Record<SkillGapItemResult["priority"], string> = {
  Critical: "bg-destructive/12 text-destructive",
  High: "bg-[var(--harvest)]/15 text-[var(--harvest)]",
  Medium: "bg-primary/12 text-primary",
  Low: "bg-muted text-muted-foreground",
};

const SEVERITY_STYLE: Record<
  NonNullable<SkillMatchResult["severity_if_missing"]>,
  string
> = {
  Blocking: "bg-destructive/12 text-destructive",
  Significant: "bg-[var(--harvest)]/15 text-[var(--harvest)]",
  Minor: "bg-muted text-muted-foreground",
};

/** Worst gaps first, so the thing that sinks the application is at the top. */
const SEVERITY_ORDER = { Blocking: 0, Significant: 1, Minor: 2 } as const;

function sortedGaps(matches: SkillMatchResult[]): SkillMatchResult[] {
  return matches
    .filter((m) => !m.matched)
    .sort(
      (a, b) =>
        SEVERITY_ORDER[a.severity_if_missing ?? "Significant"] -
        SEVERITY_ORDER[b.severity_if_missing ?? "Significant"],
    );
}

/**
 * The detailed breakdown, when the stored result has one.
 *
 * Results generated before 2026-07-28 only carry the two flat name lists, and
 * there is no way to reconstruct severity or provenance from those — so the
 * old rendering stays as the fallback rather than showing an empty panel.
 */
function SkillBreakdown({ result }: { result: JobMatchResult }) {
  const matches = result.skill_matches;

  if (!matches?.length) {
    return (
      <div className="mt-5 space-y-3">
        <div>
          <p className="mb-1.5 text-xs text-muted-foreground">You have</p>
          <div className="flex flex-wrap gap-1.5">
            {result.matched_skills.map((s) => (
              <Badge key={s} variant="secondary">
                {s}
              </Badge>
            ))}
          </div>
        </div>
        <div>
          <p className="mb-1.5 text-xs text-muted-foreground">
            They want, you lack
          </p>
          <div className="flex flex-wrap gap-1.5">
            {result.missing_skills.map((s) => (
              <Badge key={s} variant="outline">
                {s}
              </Badge>
            ))}
          </div>
        </div>
      </div>
    );
  }

  const gaps = sortedGaps(matches);
  const have = matches.filter((m) => m.matched);

  return (
    <div className="mt-5 space-y-4">
      {gaps.length > 0 && (
        <div>
          <p className="mb-2 text-xs text-muted-foreground">
            They want, you lack
          </p>
          <ul className="space-y-1.5">
            {gaps.map((m) => (
              <li
                key={m.job_skill}
                className="flex items-center justify-between gap-3 rounded-lg border px-3 py-2 text-sm"
              >
                <span>
                  {m.job_skill}
                  {m.requirement_level === "Preferred" && (
                    <span className="ml-2 text-xs text-muted-foreground">
                      preferred
                    </span>
                  )}
                </span>
                <span
                  className={`shrink-0 rounded-full px-2 py-0.5 text-xs ${
                    SEVERITY_STYLE[m.severity_if_missing ?? "Significant"]
                  }`}
                >
                  {m.severity_if_missing ?? "Significant"}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {have.length > 0 && (
        <div>
          <p className="mb-2 text-xs text-muted-foreground">You have</p>
          <div className="flex flex-wrap gap-1.5">
            {have.map((m) => (
              <Badge
                key={m.job_skill}
                variant={m.is_transferable_match ? "outline" : "secondary"}
                // The transferable case is the one worth explaining: it looks
                // like a match and is only close enough to argue for.
                title={
                  m.is_transferable_match && m.matched_via
                    ? `Close match via ${m.matched_via}`
                    : (m.matched_via ?? undefined)
                }
              >
                {m.job_skill}
                {m.is_transferable_match && " ~"}
              </Badge>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function NoCv() {
  return (
    <section className="rounded-2xl border border-dashed bg-card p-10 text-center">
      <Sprout className="mx-auto h-8 w-8 text-primary" />
      <h2 className="mt-3 text-lg">Analyze your CV first</h2>
      <p className="mx-auto mt-1 max-w-sm text-sm text-muted-foreground">
        Both of these compare a job against the skills your CV already proves,
        so there is nothing to compare against yet.
      </p>
      <Link href="/cv" className={`${buttonVariants()} mt-4`}>
        Go to CV Studio
      </Link>
    </section>
  );
}

function Empty({ children }: { children: React.ReactNode }) {
  return (
    <section className="rounded-2xl border border-dashed bg-card p-10 text-center text-sm text-muted-foreground">
      {children}
    </section>
  );
}

/** The form beside this renders immediately; only the result waits on I/O. */
async function MatchResults() {
  const match = await getLatestJobMatch();

  if (!match) {
    return (
      <Empty>No match yet. Paste a job description to see where you stand.</Empty>
    );
  }

  return (
    <section className="space-y-6">
      <div className="rounded-2xl border bg-card p-6">
        <div className="flex items-center gap-6">
          <ScoreRing value={match.result.match_score} label="Match" />
          {typeof match.result.hiring_probability === "number" && (
            <ScoreRing
              value={match.result.hiring_probability}
              label="Screen odds"
            />
          )}
          <div>
            <h2 className="text-lg">{match.job_title ?? "Latest match"}</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              {match.result.summary}
            </p>
            {match.result.hiring_probability_reasoning && (
              <p className="mt-2 text-xs text-muted-foreground">
                {match.result.hiring_probability_reasoning}
              </p>
            )}
          </div>
        </div>

        <SkillBreakdown result={match.result} />
      </div>

      <div className="rounded-2xl border bg-card p-6">
        <h3 className="mb-3 text-base">What to do about it</h3>
        <ol className="space-y-2.5">
          {match.result.recommendations.map((r, i) => (
            <li key={r} className="flex gap-3 text-sm">
              <span className="font-mono text-xs text-muted-foreground">
                {String(i + 1).padStart(2, "0")}
              </span>
              {r}
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

async function CoverLetterResult() {
  const letter = await getLatestCoverLetter();

  if (!letter) {
    return <Empty>No letter yet. Paste a job description to write one.</Empty>;
  }

  const { result } = letter;

  return (
    <section className="space-y-4">
      <div className="rounded-2xl border bg-card p-6">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-lg">{letter.job_title ?? "Your letter"}</h2>
            <p className="mt-0.5 text-xs text-muted-foreground">
              {result.tone} tone
              {result.word_count_note ? ` · ${result.word_count_note}` : ""}
            </p>
          </div>
          <CoverLetterActions
            text={result.full_text}
            jobTitle={letter.job_title}
          />
        </div>

        {/* Plain text in a pre, never markup — same rule as the chat. */}
        <pre className="whitespace-pre-wrap rounded-xl bg-muted p-4 font-sans text-sm leading-relaxed">
          {result.full_text}
        </pre>
      </div>

      {result.evidence_used.length > 0 ? (
        <div className="rounded-2xl border bg-card p-6">
          <h3 className="mb-1 text-base">What it claimed about you</h3>
          <p className="mb-3 text-xs text-muted-foreground">
            Every line here should be something your CV genuinely says. If one
            is not, the letter overreached — edit it before sending.
          </p>
          <ul className="space-y-1.5">
            {result.evidence_used.map((item) => (
              <li key={item} className="flex gap-2 text-sm">
                <span className="text-muted-foreground">·</span>
                {item}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  );
}

async function GapResults() {
  const gap = await getLatestSkillGap();

  if (!gap) return <Empty>No gap analysis yet.</Empty>;

  return (
    <section className="space-y-6">
      <div className="rounded-2xl border bg-card p-6">
        <div className="flex items-center gap-6">
          <ScoreRing value={gap.result.overall_gap_score} label="Gap" />
          <div>
            <p className="text-sm text-muted-foreground">
              {gap.result.gap_summary}
            </p>
            <p className="mt-2 text-xs text-muted-foreground">
              Strongest: {gap.result.strongest_area} · Weakest:{" "}
              {gap.result.weakest_area}
            </p>
          </div>
        </div>
      </div>

      <div className="space-y-3">
        {gap.result.missing_skills.map((item) => (
          <div key={item.skill} className="rounded-2xl border bg-card p-5">
            <div className="flex items-center justify-between gap-3">
              <h3 className="text-base">{item.skill}</h3>
              <span
                className={`rounded-full px-2 py-0.5 text-xs ${PRIORITY_STYLE[item.priority]}`}
              >
                {item.priority}
              </span>
            </div>
            <p className="mt-1.5 text-sm text-muted-foreground">
              {item.importance_reason}
            </p>
            <dl className="mt-3 grid grid-cols-2 gap-2 text-xs">
              <div>
                <dt className="text-muted-foreground">You are at</dt>
                <dd>{item.current_level}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Time to close</dt>
                <dd>{item.estimated_learning_time}</dd>
              </div>
            </dl>
            <p className="mt-3 text-xs">
              <span className="text-muted-foreground">Build: </span>
              {item.project_to_practice}
            </p>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {item.recommended_resources.map((r) => (
                <Badge key={r} variant="secondary">
                  {r}
                </Badge>
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

export default async function JobsPage() {
  // `has_cv` rides along on the profile the layout already fetched, so the
  // gate costs nothing. A separate /cv/status call would be a second trip.
  const { hasCv } = await getProfile();

  const header = (
    <PageHeader
      eyebrow="Job Match"
      title="Measure yourself against a role"
      subtitle="Paste a job description. We compare it against the skills your CV already proves — no re-upload needed."
    />
  );

  if (!hasCv) {
    return (
      <>
        {header}
        <NoCv />
      </>
    );
  }

  return (
    <>
      {header}

      <Tabs defaultValue="match" className="space-y-6">
        <TabsList>
          <TabsTrigger value="match">Match</TabsTrigger>
          <TabsTrigger value="gap">Skill gap</TabsTrigger>
          <TabsTrigger value="letter">Cover letter</TabsTrigger>
        </TabsList>

        <TabsContent value="match">
          <div className="grid items-start gap-6 lg:grid-cols-2">
            <section className="rounded-2xl border bg-card p-6">
              <JobInput
                action={matchJob}
                label="Score this job"
                hint="We never invent skills you do not have. A low score is information, not a verdict."
              />
            </section>

            <Suspense
              fallback={<ResultsSkeleton label="Loading your latest match" />}
            >
              <MatchResults />
            </Suspense>
          </div>
        </TabsContent>

        <TabsContent value="gap">
          <div className="grid items-start gap-6 lg:grid-cols-2">
            <section className="rounded-2xl border bg-card p-6">
              <JobInput
                action={analyzeGap}
                label="Find my gaps"
                hint="Answers one question: what should I learn first? Ordered so prerequisites come before what depends on them."
              />
            </section>

            <Suspense
              fallback={<ResultsSkeleton label="Loading your latest gap analysis" />}
            >
              <GapResults />
            </Suspense>
          </div>
        </TabsContent>

        <TabsContent value="letter">
          <div className="grid items-start gap-6 lg:grid-cols-2">
            <section className="rounded-2xl border bg-card p-6">
              <JobInput
                action={writeCoverLetter}
                label="Write my letter"
                hint="Written only from what your CV actually evidences. Every claim it makes is listed underneath so you can check it."
              />
            </section>

            <Suspense
              fallback={<ResultsSkeleton label="Loading your latest letter" />}
            >
              <CoverLetterResult />
            </Suspense>
          </div>
        </TabsContent>
      </Tabs>
    </>
  );
}

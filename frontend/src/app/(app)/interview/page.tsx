import { Sprout } from "lucide-react";
import Link from "next/link";
import { Suspense } from "react";

import {
  AnswerQuestion,
  StartInterview,
} from "@/components/interview/interview-controls";
import { PageHeader } from "@/components/layout/page-header";
import { InterviewSkeleton } from "@/components/skeletons";
import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { ScoreRing } from "@/components/ui/score-ring";
import {
  getInterviewSession,
  getInterviewSessions,
  getLatestInterview,
  getProfile,
  type InterviewSessionRecord,
} from "@/lib/services";
import { cn, formatDate } from "@/lib/utils";

const LEVEL_LABEL: Record<string, string> = {
  friendly_hr: "Friendly HR",
  technical_lead: "Technical lead",
  stress_interview: "Stress interview",
};

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <div className="flex justify-between text-xs">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-mono">{value}</span>
      </div>
      <Progress value={value} className="mt-1 h-1" />
    </div>
  );
}

function InterviewHistoryList({
  sessions,
  activeId,
}: {
  sessions: InterviewSessionRecord[];
  activeId: string | undefined;
}) {
  if (sessions.length === 0) return null;

  return (
    <section className="rounded-2xl border bg-card p-6">
      <div className="flex items-center justify-between gap-2 mb-4">
        <h2 className="text-base font-semibold">Interview History</h2>
        <span className="font-mono text-xs text-muted-foreground">
          {sessions.length} {sessions.length === 1 ? "session" : "sessions"}
        </span>
      </div>
      <div className="space-y-2.5">
        {sessions.map((s, index) => {
          const isLatest = index === 0;
          const isActive = activeId ? s.id === activeId : isLatest;
          const label = LEVEL_LABEL[s.level] ?? s.level;
          const turnsCount = s.turns.filter((t) => t.answer !== null).length;
          return (
            <Link
              key={s.id}
              href={isLatest ? "/interview" : `/interview?session=${s.id}`}
              className={cn(
                "min-h-11 block rounded-xl border p-3.5 text-xs transition-all hover:border-primary/60 hover:shadow-sm focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1",
                isActive
                  ? "border-primary bg-primary/10 font-semibold shadow-sm"
                  : "bg-background text-muted-foreground",
              )}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="font-medium text-foreground truncate">
                  {s.interviewer_name ?? "Interviewer"} ({label})
                </span>
                <span className="font-mono text-[10px] text-muted-foreground shrink-0">
                  {formatDate(s.created_at)}
                </span>
              </div>
              <div className="mt-1.5 flex items-center justify-between gap-2 text-[11px] text-muted-foreground">
                <span>
                  {s.finished ? "Finished" : `${turnsCount} answers`}
                </span>
                {s.final_evaluation ? (
                  <span className="font-mono font-semibold text-primary">
                    Score: {s.final_evaluation.overall_score}
                  </span>
                ) : null}
              </div>
            </Link>
          );
        })}
      </div>
    </section>
  );
}

export default async function InterviewPage({
  searchParams,
}: {
  searchParams: Promise<{ session?: string }>;
}) {
  // Free: the layout already resolved the profile, and `has_cv` rides on it.
  const profile = await getProfile();
  const { session: selectedSessionId } = await searchParams;

  const header = (
    <PageHeader
      eyebrow="Interview Coach"
      title="Practise under pressure"
      subtitle="A turn-by-turn mock interview graded on what you actually say. Questions come from your CV and the role."
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
            The interviewer asks about your real experience, so it needs to
            know what that is.
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
      <Suspense fallback={<InterviewSkeleton />}>
        <InterviewBody selectedSessionId={selectedSessionId} />
      </Suspense>
    </>
  );
}

/** The transcript. Streams behind the header instead of blocking it. */
async function InterviewBody({
  selectedSessionId,
}: {
  selectedSessionId?: string;
}) {
  const [sessions, defaultSession] = await Promise.all([
    getInterviewSessions().catch(() => []),
    getLatestInterview(),
  ]);

  const session = selectedSessionId
    ? (await getInterviewSession(selectedSessionId)) ?? defaultSession
    : defaultSession;

  const open = session?.turns.find((t) => t.answer === null) ?? null;
  const answered = session?.turns.filter((t) => t.answer !== null) ?? [];
  const evaluation = session?.final_evaluation ?? null;

  return (
    <>
      <div className="grid items-start gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          {session ? (
            <>
              <section className="rounded-2xl border bg-card p-6">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 className="text-lg">
                      {session.interviewer_name ?? "Your interviewer"}
                    </h2>
                    <p className="text-sm text-muted-foreground">
                      {LEVEL_LABEL[session.level] ?? session.level}
                    </p>
                  </div>
                  <Badge variant={session.finished ? "secondary" : "default"}>
                    {session.finished
                      ? "Finished"
                      : `Question ${answered.length + 1}`}
                  </Badge>
                </div>
              </section>

              {answered.map((turn, idx) => (
                <section key={turn.id} className="rounded-2xl border bg-card p-5 shadow-sm sm:p-6">
                  {/* The number and the score used to bracket the question on
                      the same row, squeezing it into a narrow column that
                      broke after two or three words on a phone. They are a
                      meta line of their own now, and the question gets the
                      full width underneath. */}
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-mono text-xs text-muted-foreground">
                      Q{idx + 1}
                    </span>
                    {turn.score !== null ? (
                      <Badge variant="outline" className="shrink-0 font-mono text-xs text-primary border-primary/30 bg-primary/5">
                        Score: {turn.score}
                      </Badge>
                    ) : null}
                  </div>
                  <p className="mt-1.5 text-sm font-semibold text-foreground break-words">
                    {turn.question}
                  </p>
                  <p className="mt-3 whitespace-pre-wrap break-words rounded-xl bg-muted/60 border px-4 py-3 text-sm text-foreground">
                    {turn.answer}
                  </p>

                  {turn.feedback ? (
                    <div className="mt-5 grid gap-5 sm:grid-cols-2 border-t pt-4">
                      <div className="space-y-2.5">
                        <Metric
                          label="Technical accuracy"
                          value={turn.feedback.technical_accuracy}
                        />
                        <Metric
                          label="Communication"
                          value={turn.feedback.communication_score}
                        />
                        <Metric
                          label="Confidence"
                          value={turn.feedback.confidence_level}
                        />
                      </div>
                      <div className="space-y-3 text-xs">
                        {turn.feedback.weaknesses.length > 0 ? (
                          <div>
                            <p className="font-medium text-foreground mb-1.5">Weak spots</p>
                            <div className="flex flex-wrap gap-1.5">
                              {turn.feedback.weaknesses.map((w) => (
                                <Badge
                                  key={w}
                                  variant="secondary"
                                  className="text-[11px] font-normal whitespace-normal text-left h-auto max-w-full py-1 leading-relaxed break-words"
                                >
                                  {w}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        ) : null}
                        {turn.feedback.missing_concepts.length > 0 ? (
                          <div>
                            <p className="font-medium text-foreground mb-1.5">
                              You didn&apos;t mention
                            </p>
                            <div className="flex flex-wrap gap-1.5">
                              {turn.feedback.missing_concepts.map((c) => (
                                <Badge
                                  key={c}
                                  variant="outline"
                                  className="text-[11px] font-normal border-amber-500/30 text-amber-600 dark:text-amber-400 whitespace-normal text-left h-auto max-w-full py-1 leading-relaxed break-words"
                                >
                                  {c}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        ) : null}
                      </div>
                    </div>
                  ) : null}
                </section>
              ))}

              {open ? (
                <section className="rounded-2xl border border-primary/40 bg-card p-5 sm:p-6">
                  {/* Same treatment as an answered turn: the difficulty badge
                      sits above the question rather than stealing width from
                      it. */}
                  {open.difficulty ? (
                    <Badge variant="outline" className="mb-2">
                      {open.difficulty}
                    </Badge>
                  ) : null}
                  <p className="text-base break-words">{open.question}</p>
                  {open.expected_topics.length > 0 ? (
                    <p className="mt-2 text-xs text-muted-foreground break-words">
                      A strong answer touches: {open.expected_topics.join(", ")}
                    </p>
                  ) : null}
                  <div className="mt-4">
                    <AnswerQuestion sessionId={session.id} />
                  </div>
                </section>
              ) : null}
            </>
          ) : (
            <section className="rounded-2xl border border-dashed bg-card p-10 text-center text-sm text-muted-foreground">
              No interview yet. Pick an interviewer and paste a role to begin.
            </section>
          )}
        </div>

        <aside className="space-y-6">
          <InterviewHistoryList
            sessions={sessions}
            activeId={selectedSessionId}
          />
          {evaluation ? (
            <section className="rounded-2xl border bg-card p-6">
              <div className="flex items-center gap-5">
                <ScoreRing value={evaluation.overall_score} label="Overall" />
                <div>
                  <p className="text-sm font-medium">
                    {evaluation.hiring_recommendation}
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground break-words">
                    {evaluation.summary}
                  </p>
                </div>
              </div>
              <div className="mt-5 space-y-2">
                <Metric label="Technical" value={evaluation.technical_skills} />
                <Metric label="Communication" value={evaluation.communication} />
                <Metric label="Confidence" value={evaluation.confidence} />
                <Metric
                  label="Problem solving"
                  value={evaluation.problem_solving}
                />
              </div>
              {evaluation.weak_areas.length > 0 ? (
                <div className="mt-4 flex flex-wrap gap-1.5">
                  {evaluation.weak_areas.map((a) => (
                    <Badge
                      key={a}
                      variant="outline"
                      className="whitespace-normal text-left h-auto max-w-full py-1 leading-relaxed break-words"
                    >
                      {a}
                    </Badge>
                  ))}
                </div>
              ) : null}
            </section>
          ) : null}

          <section className="rounded-2xl border bg-card p-6">
            <h2 className="mb-4 text-base">
              {session && !session.finished
                ? "Start a different interview"
                : "New interview"}
            </h2>
            <StartInterview />
          </section>
        </aside>
      </div>
    </>
  );
}

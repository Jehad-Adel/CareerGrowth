import { Sprout } from "lucide-react";
import Link from "next/link";

import {
  AnswerQuestion,
  StartInterview,
} from "@/components/interview/interview-controls";
import { PageHeader } from "@/components/layout/page-header";
import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { ScoreRing } from "@/components/ui/score-ring";
import { getCvStatus, getLatestInterview } from "@/lib/services";

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

export default async function InterviewPage() {
  const [status, session] = await Promise.all([
    getCvStatus(),
    getLatestInterview(),
  ]);

  const header = (
    <PageHeader
      eyebrow="Interview Coach"
      title="Practise under pressure"
      subtitle="A turn-by-turn mock interview graded on what you actually say. Questions come from your CV and the role."
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

  const open = session?.turns.find((t) => t.answer === null) ?? null;
  const answered = session?.turns.filter((t) => t.answer !== null) ?? [];
  const evaluation = session?.final_evaluation ?? null;

  return (
    <>
      {header}

      <div className="grid gap-6 lg:grid-cols-3">
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

              {answered.map((turn) => (
                <section key={turn.id} className="rounded-2xl border bg-card p-6">
                  <div className="flex items-start justify-between gap-3">
                    <p className="text-sm font-medium">{turn.question}</p>
                    {turn.score !== null ? (
                      <span className="shrink-0 font-mono text-xs text-primary">
                        {turn.score}
                      </span>
                    ) : null}
                  </div>
                  <p className="mt-2 whitespace-pre-wrap rounded-xl bg-muted px-4 py-3 text-sm">
                    {turn.answer}
                  </p>

                  {turn.feedback ? (
                    <div className="mt-4 grid gap-4 sm:grid-cols-2">
                      <div className="space-y-2">
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
                      <div className="space-y-2 text-xs">
                        {turn.feedback.weaknesses.length > 0 ? (
                          <div>
                            <p className="text-muted-foreground">Weak spots</p>
                            <p>{turn.feedback.weaknesses.join(" · ")}</p>
                          </div>
                        ) : null}
                        {turn.feedback.missing_concepts.length > 0 ? (
                          <div>
                            <p className="text-muted-foreground">
                              You didn&apos;t mention
                            </p>
                            <p>{turn.feedback.missing_concepts.join(" · ")}</p>
                          </div>
                        ) : null}
                      </div>
                    </div>
                  ) : null}
                </section>
              ))}

              {open ? (
                <section className="rounded-2xl border border-primary/40 bg-card p-6">
                  <div className="flex items-start justify-between gap-3">
                    <p className="text-base">{open.question}</p>
                    {open.difficulty ? (
                      <Badge variant="outline">{open.difficulty}</Badge>
                    ) : null}
                  </div>
                  {open.expected_topics.length > 0 ? (
                    <p className="mt-2 text-xs text-muted-foreground">
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
          {evaluation ? (
            <section className="rounded-2xl border bg-card p-6">
              <div className="flex items-center gap-5">
                <ScoreRing value={evaluation.overall_score} label="Overall" />
                <div>
                  <p className="text-sm font-medium">
                    {evaluation.hiring_recommendation}
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">
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
                    <Badge key={a} variant="outline">
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

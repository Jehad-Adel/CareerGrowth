"use client";

import { AlertCircle, Check, Loader2, X } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScoreRing } from "@/components/ui/score-ring";
import { Select, SelectItem } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";

import { generateQuiz, submitQuizAnswers } from "./actions";

type QuestionDisplay = {
  question: string;
  options: string[];
  correctAnswer?: number;
  explanation?: string;
  userAnswer?: number;
  isCorrect?: boolean;
};

/** Shared error presentation, matching `jobs/job-input.tsx`. */
function ErrorNote({ message }: { message: string }) {
  return (
    <div
      role="alert"
      className="flex items-start gap-2.5 rounded-lg bg-destructive/10 px-3.5 py-2.5 text-xs text-destructive"
    >
      <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
      <span>{message}</span>
    </div>
  );
}

export function QuizBody() {
  const [phase, setPhase] = useState<"form" | "quiz" | "result">("form");
  const [questions, setQuestions] = useState<QuestionDisplay[]>([]);
  const [attemptId, setAttemptId] = useState<string | null>(null);
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleGenerate(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);

    setLoading(true);
    setError(null);
    try {
      const res = await generateQuiz({}, form);
      if (res.error) {
        setError(res.error);
        return;
      }
      if (res.attemptId && res.questions) {
        setAttemptId(res.attemptId);
        setQuestions(res.questions);
        setAnswers({});
        setPhase("quiz");
      }
    } finally {
      // `finally`, not a call on each branch: an early return used to leave
      // `loading` stuck true and the button disabled for good.
      setLoading(false);
    }
  }

  async function handleSubmitQuiz() {
    // Guard before the spinner goes up, not after.
    if (!attemptId) {
      setError("That quiz expired. Generate a new one.");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const form = new FormData();
      form.set("attempt_id", attemptId);
      form.set(
        "answers",
        JSON.stringify(questions.map((_, i) => answers[i] ?? -1)),
      );

      const res = await submitQuizAnswers({}, form);
      if (res.error) {
        setError(res.error);
        return;
      }
      if (res.questions) {
        setQuestions(res.questions);
        setPhase("result");
      }
    } finally {
      setLoading(false);
    }
  }

  function reset() {
    setPhase("form");
    setQuestions([]);
    setAnswers({});
    setAttemptId(null);
    setError(null);
  }

  if (phase === "quiz") {
    const allAnswered =
      questions.length > 0 && Object.keys(answers).length === questions.length;
    const answeredCount = Object.keys(answers).length;

    return (
      <div className="space-y-6 rounded-2xl border bg-card p-4 sm:p-6">
        <div>
          <h2 className="text-lg font-semibold">Answer the questions</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            {answeredCount} of {questions.length} answered.
          </p>
        </div>

        {questions.map((q, i) => (
          <fieldset key={i} className="space-y-3 rounded-xl border p-3 sm:p-4">
            <legend className="px-1 text-sm font-medium">
              Question {i + 1} of {questions.length}
            </legend>
            <p className="font-medium">{q.question}</p>
            <div className="space-y-2">
              {q.options.map((opt, j) => (
                <label
                  key={j}
                  className={`flex cursor-pointer items-center gap-3 rounded-lg border p-3 transition-colors ${
                    answers[i] === j
                      ? "border-primary bg-primary/5"
                      : "hover:bg-muted/50"
                  }`}
                >
                  <input
                    type="radio"
                    name={`q-${i}`}
                    value={j}
                    checked={answers[i] === j}
                    disabled={loading}
                    onChange={() => setAnswers((p) => ({ ...p, [i]: j }))}
                    className="h-4 w-4 shrink-0 accent-primary"
                  />
                  <span className="text-sm">{opt}</span>
                </label>
              ))}
            </div>
          </fieldset>
        ))}

        {error ? <ErrorNote message={error} /> : null}

        <Button
          onClick={handleSubmitQuiz}
          disabled={!allAnswered || loading}
          aria-busy={loading}
          className="w-full"
        >
          {loading ? (
            <>
              <Loader2 className="animate-spin" />
              Scoring your answers…
            </>
          ) : (
            "Submit answers"
          )}
        </Button>
      </div>
    );
  }

  if (phase === "result") {
    const correct = questions.filter((q) => q.isCorrect).length;
    // Guard the divide: a zero-question attempt rendered "NaN%".
    const pct = questions.length
      ? Math.round((correct / questions.length) * 100)
      : 0;

    return (
      <div className="space-y-6 rounded-2xl border bg-card p-4 sm:p-6">
        {/* The score is the answer to the only question the user has here,
            so it gets the ring the rest of the app uses for a headline
            number rather than a sentence they have to parse. */}
        <div className="flex flex-wrap items-center gap-5 border-b pb-5">
          <ScoreRing value={pct} label="Score" />
          <div className="min-w-0">
            <h2 className="text-lg font-semibold">
              {correct} of {questions.length} correct
            </h2>
            <p className="mt-1 text-sm text-muted-foreground">
              {pct === 100
                ? "Full marks. Try harder material next."
                : pct >= 70
                  ? "Solid. The misses below are worth a second look."
                  : "Worth another pass — the explanations below say why."}
            </p>
          </div>
        </div>

        {questions.map((q, i) => (
          <div
            key={i}
            className={`rounded-xl border p-3 sm:p-4 ${
              q.isCorrect
                ? "border-sprout/40 bg-sprout/5"
                : "border-destructive/40 bg-destructive/5"
            }`}
          >
            <div className="flex items-start gap-2">
              {q.isCorrect ? (
                <Check
                  className="mt-0.5 h-4 w-4 shrink-0 text-sprout"
                  aria-hidden
                />
              ) : (
                <X
                  className="mt-0.5 h-4 w-4 shrink-0 text-destructive"
                  aria-hidden
                />
              )}
              <p className="font-medium">
                <span className="sr-only">
                  {q.isCorrect ? "Correct." : "Incorrect."}{" "}
                </span>
                {i + 1}. {q.question}
              </p>
            </div>
            <p className="mt-1 text-sm">
              Your answer:{" "}
              <span
                className={
                  q.isCorrect
                    ? "font-medium text-sprout"
                    : "font-medium text-destructive"
                }
              >
                {q.userAnswer !== undefined
                  ? q.options[q.userAnswer]
                  : "Not answered"}
              </span>
            </p>
            {!q.isCorrect && q.correctAnswer !== undefined ? (
              <p className="text-sm text-sprout">
                Correct answer: {q.options[q.correctAnswer]}
              </p>
            ) : null}
            {q.explanation ? (
              <p className="mt-2 text-sm text-muted-foreground">
                {q.explanation}
              </p>
            ) : null}
          </div>
        ))}

        {/* Secondary action, sized to its label — a full-width outline bar
            read as the page's primary control. */}
        <div className="flex justify-end border-t pt-4">
          <Button variant="outline" size="sm" onClick={reset}>
            Try another quiz
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border bg-card p-4 sm:p-6">
      <div className="mb-6">
        <h2 className="text-lg font-semibold">Generate a quiz</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Paste learning material and we&apos;ll create questions tailored to
          your level.
        </p>
      </div>

      {/* `flex flex-col gap-4`, not `space-y-4` — see the note in
          `video/video-body.tsx`. `space-y` cannot reach past the
          `display: contents` fieldset, so every gap in this form collapsed. */}
      <form onSubmit={handleGenerate} className="flex flex-col gap-4">
        <fieldset disabled={loading} className="contents">
          <div className="space-y-1.5">
            <Label htmlFor="source_text" className="text-sm font-medium">
              Source material
            </Label>
            <Textarea
              id="source_text"
              name="source_text"
              placeholder="Paste an article, documentation, or your notes…"
              rows={8}
              required
              aria-required="true"
              minLength={10}
              aria-describedby="source-hint"
            />
            <p id="source-hint" className="text-xs text-muted-foreground">
              At least 10 characters. The questions come only from what you
              paste here.
            </p>
          </div>

          {/* One column on a phone: two 50%-width controls side by side are
              unusable below ~380px. */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label htmlFor="mastery_level" className="text-sm font-medium">
                Your level
              </Label>
              <Select id="mastery_level" name="mastery_level" defaultValue="1">
                <SelectItem value="1">Beginner</SelectItem>
                <SelectItem value="2">Elementary</SelectItem>
                <SelectItem value="3">Intermediate</SelectItem>
                <SelectItem value="4">Advanced</SelectItem>
                <SelectItem value="5">Expert</SelectItem>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="num_questions" className="text-sm font-medium">
                Number of questions
              </Label>
              <Input
                id="num_questions"
                name="num_questions"
                type="number"
                inputMode="numeric"
                defaultValue={5}
                min={1}
                max={20}
              />
            </div>
          </div>
        </fieldset>

        {error ? <ErrorNote message={error} /> : null}

        <Button
          type="submit"
          disabled={loading}
          aria-busy={loading}
          className="w-full"
        >
          {loading ? (
            <>
              <Loader2 className="animate-spin" />
              Writing your questions…
            </>
          ) : (
            "Generate quiz"
          )}
        </Button>
      </form>
    </div>
  );
}

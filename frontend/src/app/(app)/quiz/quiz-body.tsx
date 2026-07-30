"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
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

export function QuizBody() {
  const [phase, setPhase] = useState<"form" | "quiz" | "result">("form");
  const [questions, setQuestions] = useState<QuestionDisplay[]>([]);
  const [attemptId, setAttemptId] = useState<string | null>(null);
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleGenerate(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const form = new FormData(e.currentTarget);
    const res = await generateQuiz({}, form);
    if (res.error) {
      setError(res.error);
      setLoading(false);
      return;
    }
    if (res.attemptId) {
      try {
        const { getQuizAttempt } = await import("@/lib/services");
        const attempt = await getQuizAttempt(res.attemptId);
        setAttemptId(attempt.id);
        setQuestions(
          attempt.questions.map((q) => ({
            question: q.question,
            options: q.options,
          })),
        );
        setPhase("quiz");
      } catch {
        window.location.reload();
      }
    }
    setLoading(false);
  }

  async function handleSubmitQuiz() {
    setLoading(true);
    setError(null);
    if (!attemptId) return;

    const answerList = questions.map((_, i) => answers[i] ?? -1);
    const form = new FormData();
    form.set("attempt_id", attemptId);
    form.set("answers", JSON.stringify(answerList));
    const res = await submitQuizAnswers({}, form);
    if (res.error) {
      setError(res.error);
      setLoading(false);
      return;
    }

    try {
      const { getQuizAttempt } = await import("@/lib/services");
      const attempt = await getQuizAttempt(attemptId);
      setQuestions(
        attempt.questions.map((q) => ({
          question: q.question,
          options: q.options,
          correctAnswer: q.correct_answer ?? undefined,
          explanation: q.explanation ?? undefined,
          userAnswer: q.user_answer ?? undefined,
          isCorrect: q.is_correct ?? undefined,
        })),
      );
      setPhase("result");
    } catch {
      window.location.reload();
    }
    setLoading(false);
  }

  if (phase === "quiz") {
    const allAnswered = questions.length > 0 && Object.keys(answers).length === questions.length;
    return (
      <div className="rounded-2xl border bg-card p-6 space-y-6">
        <div>
          <h2 className="text-lg font-semibold">Answer the Questions</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Select the best answer for each question.
          </p>
        </div>
        {questions.map((q, i) => (
          <div key={i} className="rounded-xl border p-4 space-y-3">
            <p className="font-medium">
              {i + 1}. {q.question}
            </p>
            <div className="space-y-2">
              {q.options.map((opt, j) => (
                <label
                  key={j}
                  className={`flex items-center gap-3 rounded-lg border p-3 cursor-pointer transition-colors ${
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
                    onChange={() => setAnswers((p) => ({ ...p, [i]: j }))}
                    className="h-4 w-4"
                  />
                  <span className="text-sm">{opt}</span>
                </label>
              ))}
            </div>
          </div>
        ))}
        {error && <p className="text-sm text-red-600">{error}</p>}
        <Button onClick={handleSubmitQuiz} disabled={!allAnswered || loading} className="w-full">
          {loading ? "Submitting..." : "Submit Answers"}
        </Button>
      </div>
    );
  }

  if (phase === "result") {
    const correct = questions.filter((q) => q.isCorrect).length;
    return (
      <div className="rounded-2xl border bg-card p-6 space-y-6">
        <div>
          <h2 className="text-lg font-semibold">Results</h2>
          <p className="text-sm text-muted-foreground mt-1">
            You got {correct} of {questions.length} correct ({Math.round((correct / questions.length) * 100)}%)
          </p>
        </div>
        {questions.map((q, i) => (
          <div
            key={i}
            className={`rounded-xl border p-4 ${
              q.isCorrect ? "border-green-200 bg-green-50/50" : "border-red-200 bg-red-50/50"
            }`}
          >
            <p className="font-medium">
              {i + 1}. {q.question}
            </p>
            <p className="mt-1 text-sm">
              Your answer:{" "}
              <span className={q.isCorrect ? "text-green-700 font-medium" : "text-red-700 font-medium"}>
                {q.userAnswer !== undefined ? q.options[q.userAnswer] : "Not answered"}
              </span>
            </p>
            {q.correctAnswer !== undefined && (
              <p className="text-sm text-green-700">Correct answer: {q.options[q.correctAnswer]}</p>
            )}
            {q.explanation && <p className="mt-2 text-sm text-muted-foreground">{q.explanation}</p>}
          </div>
        ))}
        <Button variant="outline" onClick={() => { setPhase("form"); setQuestions([]); setAnswers({}); setAttemptId(null); setError(null); }} className="w-full">
          Try Another Quiz
        </Button>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border bg-card p-6">
      <div className="mb-6">
        <h2 className="text-lg font-semibold">Generate a Quiz</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Paste learning material and we&apos;ll create questions tailored to your level.
        </p>
      </div>
      <form onSubmit={handleGenerate} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="source_text">Source Material</Label>
          <Textarea
            id="source_text"
            name="source_text"
            placeholder="Paste article, documentation, or notes here..."
            rows={8}
            required
            minLength={10}
          />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="mastery_level">Your Level</Label>
            <select
              id="mastery_level"
              name="mastery_level"
              defaultValue="1"
              className="flex h-11 w-full rounded-lg border border-input bg-transparent px-3 py-2 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
            >
              <option value="1">Beginner</option>
              <option value="2">Elementary</option>
              <option value="3">Intermediate</option>
              <option value="4">Advanced</option>
              <option value="5">Expert</option>
            </select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="num_questions">Number of Questions</Label>
            <input
              id="num_questions"
              name="num_questions"
              type="number"
              defaultValue={5}
              min={1}
              max={20}
              className="flex h-11 w-full rounded-lg border border-input bg-transparent px-3 py-2 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
            />
          </div>
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <Button type="submit" disabled={loading} className="w-full">
          {loading ? "Generating..." : "Generate Quiz"}
        </Button>
      </form>
    </div>
  );
}

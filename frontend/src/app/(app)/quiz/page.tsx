import { Suspense } from "react";

import { CardSkeleton } from "@/components/skeletons";

import { QuizBody } from "./quiz-body";

export const metadata = { title: "Quiz — CareerFarm" };

export default function QuizPage() {
  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Quiz Engine</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Test your knowledge with AI-generated quizzes from any learning material.
        </p>
      </div>
      <Suspense fallback={<CardSkeleton />}>
        <QuizBody />
      </Suspense>
    </div>
  );
}

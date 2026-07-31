import { Suspense } from "react";

import { PageHeader } from "@/components/layout/page-header";
import { CardSkeleton } from "@/components/skeletons";

import { QuizBody } from "./quiz-body";

// The root layout applies `title.template: "%s · CareerGrowth"`, so repeating
// the suffix here renders it twice.
export const metadata = { title: "Quiz" };

export default function QuizPage() {
  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader
        eyebrow="Quiz"
        title="Check what actually stuck"
        subtitle="Paste anything you've been studying. We'll write questions at your level and mark them, so you find the gaps before an interviewer does."
      />
      <Suspense fallback={<CardSkeleton />}>
        <QuizBody />
      </Suspense>
    </div>
  );
}

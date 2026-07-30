import { Suspense } from "react";

import { CardSkeleton } from "@/components/skeletons";

import { OffersBody } from "./offers-body";

export const metadata = { title: "Offer Evaluator — CareerFarm" };

export default function OffersPage() {
  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Job Offer Evaluator</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Paste a job offer you received and get an objective evaluation.
        </p>
      </div>
      <Suspense fallback={<CardSkeleton />}>
        <OffersBody />
      </Suspense>
    </div>
  );
}

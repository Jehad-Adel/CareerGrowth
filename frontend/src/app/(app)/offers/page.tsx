import { Suspense } from "react";

import { PageHeader } from "@/components/layout/page-header";
import { CardSkeleton } from "@/components/skeletons";

import { OffersBody } from "./offers-body";

// The root layout applies `title.template: "%s · CareerGrowth"`, so repeating
// the suffix here renders it twice.
export const metadata = { title: "Offer Evaluator" };

export default function OffersPage() {
  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader
        eyebrow="Offers"
        title="Read the offer, not just the number"
        subtitle="Paste everything you were sent — salary, equity, benefits, the working arrangement. You get a scored breakdown and the points worth negotiating."
      />
      <Suspense fallback={<CardSkeleton />}>
        <OffersBody />
      </Suspense>
    </div>
  );
}

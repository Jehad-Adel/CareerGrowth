import { Suspense } from "react";

import { ApplicationsBoard } from "@/components/applications/board";
import { PageHeader } from "@/components/layout/page-header";
import { CardSkeleton } from "@/components/skeletons";
import { getApplications } from "@/lib/services";

/** The board waits on I/O; the header does not. */
async function Board() {
  const board = await getApplications();
  return <ApplicationsBoard board={board} />;
}

export default function ApplicationsPage() {
  return (
    <>
      <PageHeader
        eyebrow="Applications"
        title="Everything you're chasing"
        subtitle="The rest of the app answers whether to apply. This one remembers what you applied to, and how long it has been quiet."
      />

      <Suspense fallback={<CardSkeleton lines={8} />}>
        <Board />
      </Suspense>
    </>
  );
}

import { Suspense } from "react";

import { PageHeader } from "@/components/layout/page-header";
import { CardSkeleton } from "@/components/skeletons";

import { VideoBody } from "./video-body";

// The root layout applies `title.template: "%s · CareerGrowth"`, so repeating
// the suffix here renders it twice.
export const metadata = { title: "Video Summarizer" };

export default function VideoPage() {
  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader
        eyebrow="Video"
        title="Turn a talk into notes you'll keep"
        subtitle="Paste a YouTube link for a structured summary with key takeaways, or the full transcript to search through."
      />
      <Suspense fallback={<CardSkeleton />}>
        <VideoBody />
      </Suspense>
    </div>
  );
}

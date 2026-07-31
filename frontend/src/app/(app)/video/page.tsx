import { Suspense } from "react";

import { CardSkeleton } from "@/components/skeletons";

import { VideoBody } from "./video-body";

// The root layout applies `title.template: "%s · CareerFarm"`, so repeating
// the suffix here renders it twice.
export const metadata = { title: "Video Summarizer" };

export default function VideoPage() {
  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Video Summarizer</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Paste a video link to get a summary or full transcript.
        </p>
      </div>
      <Suspense fallback={<CardSkeleton />}>
        <VideoBody />
      </Suspense>
    </div>
  );
}

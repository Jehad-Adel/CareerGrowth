import { CardSkeleton, PageHeaderSkeleton } from "@/components/skeletons";

/**
 * Must mirror the route's own shell — same container width and the same
 * skeleton its `<Suspense>` fallback uses — or a soft navigation and a cold
 * load flash two different layouts. `PageHeaderSkeleton` matches `PageHeader`,
 * so the page has to use that component rather than a hand-rolled heading.
 */
export default function Loading() {
  return (
    <div className="mx-auto max-w-3xl">
      <PageHeaderSkeleton />
      <CardSkeleton />
    </div>
  );
}

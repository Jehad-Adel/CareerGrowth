import { CardSkeleton, PageHeaderSkeleton } from "@/components/skeletons";

/**
 * Must render the same skeleton the route's `<Suspense>` fallback uses, or a
 * soft navigation and a cold load flash two different layouts.
 */
export default function Loading() {
  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <PageHeaderSkeleton />
      <CardSkeleton />
    </div>
  );
}

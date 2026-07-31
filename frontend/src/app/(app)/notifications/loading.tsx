import { CardSkeleton, PageHeaderSkeleton } from "@/components/skeletons";

/** Mirrors the route's shell — see the note in the sibling routes' loading.tsx. */
export default function Loading() {
  return (
    <div className="mx-auto max-w-2xl">
      <PageHeaderSkeleton />
      <CardSkeleton />
    </div>
  );
}

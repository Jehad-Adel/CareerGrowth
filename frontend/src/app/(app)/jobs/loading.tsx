import {
  CardSkeleton,
  PageHeaderSkeleton,
  ResultsSkeleton,
} from "@/components/skeletons";

export default function Loading() {
  return (
    <>
      <PageHeaderSkeleton />
      <div className="grid gap-6 lg:grid-cols-2">
        <CardSkeleton lines={8} />
        <ResultsSkeleton label="Loading job match" />
      </div>
    </>
  );
}

import { CardSkeleton, PageHeaderSkeleton } from "@/components/skeletons";

export default function Loading() {
  return (
    <>
      <PageHeaderSkeleton />
      <CardSkeleton lines={8} />
    </>
  );
}

import { ChatSkeleton, PageHeaderSkeleton } from "@/components/skeletons";

export default function Loading() {
  return (
    <div className="mx-auto flex h-full max-w-3xl flex-col">
      <PageHeaderSkeleton />
      <div className="h-[calc(100dvh-13rem)] min-h-[26rem] rounded-2xl border bg-card sm:h-[560px]">
        <ChatSkeleton />
      </div>
    </div>
  );
}

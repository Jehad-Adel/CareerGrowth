import { ChatSkeleton, PageHeaderSkeleton } from "@/components/skeletons";

export default function Loading() {
  return (
    <div className="mx-auto flex h-[calc(100dvh-7rem)] min-h-[26rem] max-w-5xl flex-col sm:h-[calc(100dvh-8.5rem)]">
      <PageHeaderSkeleton />
      <div className="min-h-0 flex-1 rounded-2xl border bg-card">
        <ChatSkeleton />
      </div>
    </div>
  );
}

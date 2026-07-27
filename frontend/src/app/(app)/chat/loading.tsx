import { ChatSkeleton, PageHeaderSkeleton } from "@/components/skeletons";

export default function Loading() {
  return (
    <div className="mx-auto flex h-full max-w-3xl flex-col">
      <PageHeaderSkeleton />
      <div className="h-[560px] rounded-2xl border bg-card">
        <ChatSkeleton />
      </div>
    </div>
  );
}

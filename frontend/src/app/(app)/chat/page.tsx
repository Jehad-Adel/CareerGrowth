import { Sprout } from "lucide-react";
import Link from "next/link";
import { Suspense } from "react";

import { Conversation } from "@/components/chat/conversation";
import { PageHeader } from "@/components/layout/page-header";
import { ChatSkeleton } from "@/components/skeletons";
import { buttonVariants } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { getChatState, getProfile } from "@/lib/services";

/** The transcript plus its quota line, all from one round trip. */
async function ChatBody() {
  const chat = await getChatState();

  const grounded = chat.corpus_chunks > 0;
  const remaining = Math.max(chat.daily_limit - chat.messages_today, 0);

  return (
    <>
      <Conversation messages={chat.messages} disabled={remaining <= 0} />

      <p className="mt-3 text-center text-xs text-muted-foreground">
        {remaining <= 0
          ? "You've used today's messages. More tomorrow."
          : `${remaining} messages left today`}
        {grounded
          ? ` · grounded in ${chat.corpus_chunks} indexed passages`
          : " · nothing indexed yet"}
      </p>
    </>
  );
}

/** Same box as `Conversation`, so the transcript lands without a resize. */
function ChatBodyFallback() {
  return (
    <div className="flex h-[calc(100dvh-13rem)] min-h-[26rem] flex-col rounded-2xl border bg-card sm:h-[560px]">
      <div className="flex-1 overflow-hidden">
        <ChatSkeleton />
      </div>
      <div className="border-t p-4">
        <div className="mb-3 flex flex-wrap gap-2">
          <Skeleton className="h-6 w-40 rounded-full" />
          <Skeleton className="h-6 w-52 rounded-full" />
        </div>
        <Skeleton className="h-10 w-full rounded-lg" />
      </div>
    </div>
  );
}

export default async function ChatPage() {
  // Free: the layout already resolved the profile, and `has_cv` rides on it.
  const { hasCv } = await getProfile();

  return (
    <div className="mx-auto flex h-full max-w-3xl flex-col">
      <PageHeader
        eyebrow="Career Chat"
        title="Ask your career assistant"
        subtitle="Answers grounded in your own profile and documents — not generic advice."
      />

      {!hasCv ? (
        <section className="rounded-2xl border border-dashed bg-card p-10 text-center">
          <Sprout className="mx-auto h-8 w-8 text-primary" />
          <h2 className="mt-3 text-lg">Nothing to talk about yet</h2>
          <p className="mx-auto mt-1 max-w-sm text-sm text-muted-foreground">
            The assistant answers from your CV, job matches, and roadmap. Give
            it something to read first.
          </p>
          <Link href="/cv" className={`${buttonVariants()} mt-4`}>
            Go to CV Studio
          </Link>
        </section>
      ) : (
        <Suspense fallback={<ChatBodyFallback />}>
          <ChatBody />
        </Suspense>
      )}
    </div>
  );
}

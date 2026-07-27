import { Sprout } from "lucide-react";
import Link from "next/link";

import { LogoMark } from "@/components/brand/logo";
import { ChatInput } from "@/components/chat/chat-input";
import { PageHeader } from "@/components/layout/page-header";
import { buttonVariants } from "@/components/ui/button";
import { getChatState, getCvStatus } from "@/lib/services";
import { cn } from "@/lib/utils";

export default async function ChatPage() {
  const [status, chat] = await Promise.all([getCvStatus(), getChatState()]);

  const grounded = chat.corpus_chunks > 0;
  const remaining = Math.max(chat.daily_limit - chat.messages_today, 0);

  return (
    <div className="mx-auto flex h-full max-w-3xl flex-col">
      <PageHeader
        eyebrow="Career Chat"
        title="Ask your career assistant"
        subtitle="Answers grounded in your own profile and documents — not generic advice."
      />

      {!status.has_cv ? (
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
        <>
          <div className="flex h-[560px] flex-col rounded-2xl border bg-card">
            <div className="flex-1 space-y-4 overflow-y-auto p-6">
              {chat.messages.length === 0 ? (
                <p className="pt-16 text-center text-sm text-muted-foreground">
                  Ask the first question.
                </p>
              ) : (
                chat.messages.map((m) => (
                  <div
                    key={m.id}
                    className={cn(
                      "flex gap-3",
                      m.role === "user" && "flex-row-reverse",
                    )}
                  >
                    {m.role === "assistant" && (
                      <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-primary/12">
                        <LogoMark className="h-4 w-4 text-primary" />
                      </span>
                    )}
                    <div className="max-w-[80%]">
                      {/* Model output rendered as plain text, never as HTML or
                          markdown. Nothing the model returns can become markup. */}
                      <div
                        className={cn(
                          "whitespace-pre-wrap rounded-2xl px-4 py-2.5 text-sm",
                          m.role === "assistant"
                            ? "bg-muted"
                            : "bg-primary text-primary-foreground",
                        )}
                      >
                        {m.content}
                      </div>
                      {m.role === "assistant" &&
                      m.sources &&
                      m.sources.length > 0 ? (
                        <p className="mt-1 px-1 font-mono text-[10px] text-muted-foreground">
                          from:{" "}
                          {[...new Set(m.sources.map((s) => s.kind))].join(", ")}
                        </p>
                      ) : null}
                    </div>
                  </div>
                ))
              )}
            </div>

            <ChatInput disabled={remaining <= 0} />
          </div>

          <p className="mt-3 text-center text-xs text-muted-foreground">
            {remaining <= 0
              ? "You've used today's messages. More tomorrow."
              : `${remaining} messages left today`}
            {grounded
              ? ` · grounded in ${chat.corpus_chunks} indexed passages`
              : " · nothing indexed yet"}
          </p>
        </>
      )}
    </div>
  );
}

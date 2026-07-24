import { SendHorizontal } from "lucide-react";

import { LogoMark } from "@/components/brand/logo";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { getChatHistory } from "@/lib/services";

const SUGGESTIONS = [
  "What should I learn next?",
  "Improve my CV summary",
  "Prep me for a system-design question",
];

export default async function ChatPage() {
  const messages = await getChatHistory();

  return (
    <div className="mx-auto flex h-full max-w-3xl flex-col">
      <PageHeader
        eyebrow="Career Chat"
        title="Ask your career assistant"
        subtitle="Answers grounded in your own profile, skills, and progress — not generic advice."
      />

      <div className="flex h-[560px] flex-col rounded-2xl border bg-card">
        <div className="flex-1 space-y-4 overflow-y-auto p-6">
          {messages.map((m) => (
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
              <div
                className={cn(
                  "max-w-[80%] rounded-2xl px-4 py-2.5 text-sm",
                  m.role === "assistant"
                    ? "bg-muted"
                    : "bg-primary text-primary-foreground",
                )}
              >
                {m.content}
              </div>
            </div>
          ))}
        </div>

        <div className="border-t p-4">
          <div className="mb-3 flex flex-wrap gap-2">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                className="rounded-full border px-3 py-1 text-xs text-muted-foreground transition-colors hover:border-primary/50 hover:text-foreground"
              >
                {s}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-2">
            <input
              placeholder="Ask anything about your career…"
              className="h-10 flex-1 rounded-lg border bg-background px-3 text-sm outline-none placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/30"
            />
            <Button size="icon" className="h-10 w-10" aria-label="Send">
              <SendHorizontal className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

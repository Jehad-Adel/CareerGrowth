import { Check } from "lucide-react";

import { PageHeader } from "@/components/layout/page-header";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { getProfile, getRoadmap } from "@/lib/services";

const STATUS_BADGE = {
  done: { label: "Done", variant: "secondary" as const },
  current: { label: "In progress", variant: "default" as const },
  todo: { label: "Up next", variant: "outline" as const },
};

export default async function RoadmapPage() {
  const [profile, steps] = await Promise.all([getProfile(), getRoadmap()]);

  return (
    <>
      <PageHeader
        eyebrow="Roadmap"
        title={`Path to ${profile.targetRole}`}
        subtitle="A personalized sequence built from your current skills and target role — what to learn next, and why it comes now."
      />

      <ol className="space-y-5">
        {steps.map((step, i) => {
          const last = i === steps.length - 1;
          const badge = STATUS_BADGE[step.status];
          return (
            <li key={step.id} className="flex gap-4">
              <div className="flex flex-col items-center">
                <span
                  className={cn(
                    "grid h-9 w-9 shrink-0 place-items-center rounded-full border font-mono text-sm",
                    step.status === "done" &&
                      "border-primary bg-primary text-primary-foreground",
                    step.status === "current" &&
                      "border-primary bg-primary/10 text-primary",
                    step.status === "todo" && "text-muted-foreground",
                  )}
                >
                  {step.status === "done" ? (
                    <Check className="h-4 w-4" />
                  ) : (
                    step.order
                  )}
                </span>
                {!last && <span className="mt-1 w-px flex-1 bg-border" />}
              </div>

              <div
                className={cn(
                  "mb-1 flex-1 rounded-2xl border bg-card p-5",
                  step.status === "current" && "border-primary/50",
                )}
              >
                <div className="mb-1.5 flex flex-wrap items-center justify-between gap-2">
                  <h2 className="text-lg">{step.title}</h2>
                  <Badge variant={badge.variant}>{badge.label}</Badge>
                </div>
                <p className="text-sm text-muted-foreground">{step.detail}</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {step.skills.map((s) => (
                    <span
                      key={s}
                      className="rounded-md bg-muted px-2 py-0.5 font-mono text-[11px] text-muted-foreground"
                    >
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            </li>
          );
        })}
      </ol>
    </>
  );
}

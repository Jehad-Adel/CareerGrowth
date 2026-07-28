"use client";

import { Check, Copy, Sparkles } from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScoreRing } from "@/components/ui/score-ring";
import type { ResumeOptimizationResult, ResumeSection } from "@/lib/services";

function SectionCard({ section }: { section: ResumeSection }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(section.content.join("\n"));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // ignore clipboard error
    }
  }

  return (
    <div className="rounded-xl border bg-card p-5 transition-all hover:shadow-sm">
      <div className="flex items-center justify-between gap-3 mb-3">
        <h4 className="font-semibold text-base text-foreground">{section.title}</h4>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={copy}
          className="min-h-9 px-3 text-xs"
          aria-label={`Copy ${section.title} section`}
        >
          {copied ? (
            <Check className="me-1.5 h-3.5 w-3.5 text-primary" />
          ) : (
            <Copy className="me-1.5 h-3.5 w-3.5" />
          )}
          {copied ? "Copied" : "Copy section"}
        </Button>
      </div>
      <div className="space-y-2 text-sm text-foreground/90 leading-relaxed whitespace-pre-wrap rounded-lg bg-muted/40 p-3.5 border border-border/50">
        {section.content.map((line, idx) => (
          <p key={idx}>{line}</p>
        ))}
      </div>
    </div>
  );
}

export function ResumeOptimizationResultsView({
  result,
}: {
  result: ResumeOptimizationResult | null;
}) {
  const [copiedFull, setCopiedFull] = useState(false);

  async function copyFullResume() {
    if (!result?.final_resume_text) return;
    try {
      await navigator.clipboard.writeText(result.final_resume_text);
      setCopiedFull(true);
      setTimeout(() => setCopiedFull(false), 2000);
    } catch {
      // ignore clipboard error
    }
  }

  if (!result) {
    return (
      <div className="rounded-2xl border bg-card p-8 text-center">
        <Sparkles className="mx-auto h-8 w-8 text-muted-foreground/40" />
        <h3 className="mt-3 font-heading text-lg font-medium">
          No optimization yet
        </h3>
        <p className="mt-1 text-sm text-muted-foreground">
          Paste a job posting on the left to see how your CV can be tailored to match it.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <section className="flex flex-col items-center gap-6 rounded-2xl border bg-card p-6 sm:flex-row sm:justify-between">
        <div className="flex flex-wrap items-center gap-6">
          <ScoreRing value={result.ats_score_before} label="Before" size={96} />
          <ScoreRing value={result.ats_score_after} label="After ATS Match" size={96} />
          <div>
            <h3 className="font-heading text-lg font-semibold">
              Resume Tailored for ATS
            </h3>
            <p className="text-sm text-muted-foreground mt-0.5">
              Optimized for keyword match and readability based on your verified CV
            </p>
          </div>
        </div>
        {result.final_resume_text ? (
          <Button
            type="button"
            variant="outline"
            onClick={copyFullResume}
            className="min-h-11 shrink-0"
          >
            {copiedFull ? (
              <Check className="me-2 h-4 w-4 text-primary" />
            ) : (
              <Copy className="me-2 h-4 w-4" />
            )}
            {copiedFull ? "Copied Full CV" : "Copy Full Resume"}
          </Button>
        ) : null}
      </section>

      {result.summary_of_changes && result.summary_of_changes.length > 0 ? (
        <section className="rounded-2xl border border-primary/20 bg-primary/5 p-6">
          <h4 className="flex items-center gap-2 font-heading text-sm font-semibold text-primary">
            <Sparkles className="h-4 w-4" />
            Summary of Tailored Changes
          </h4>
          <ul className="mt-3 space-y-1.5 text-sm leading-relaxed text-foreground list-disc list-inside">
            {result.summary_of_changes.map((change, idx) => (
              <li key={idx}>{change}</li>
            ))}
          </ul>
        </section>
      ) : null}

      {result.missing_information && result.missing_information.length > 0 ? (
        <section className="rounded-2xl border bg-card p-6">
          <h4 className="font-heading text-sm font-semibold mb-2">
            Missing Information / Suggestions to Add
          </h4>
          <div className="flex flex-wrap gap-1.5">
            {result.missing_information.map((info, idx) => (
              <Badge
                key={idx}
                variant="outline"
                className="border-amber-500/30 text-amber-600 dark:text-amber-400 py-1 whitespace-normal text-left h-auto max-w-full leading-relaxed break-words"
              >
                {info}
              </Badge>
            ))}
          </div>
        </section>
      ) : null}

      {result.optimized_sections && result.optimized_sections.length > 0 ? (
        <section className="space-y-4">
          <h4 className="font-heading text-sm font-semibold">
            Optimized Resume Sections ({result.optimized_sections.length})
          </h4>
          <div className="space-y-4">
            {result.optimized_sections.map((sec, idx) => (
              <SectionCard key={idx} section={sec} />
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}

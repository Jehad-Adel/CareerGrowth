"use client";

import { FileUp, Loader2 } from "lucide-react";
import { useActionState, useState } from "react";
import { useFormStatus } from "react-dom";

import { analyzeCv, type CvUploadState } from "@/app/(app)/cv/actions";
import { PendingFieldset, SubmitButton } from "@/components/ui/submit-button";
import { cn } from "@/lib/utils";

/**
 * The drop zone doubles as the progress indicator: a CV analysis is a slow LLM
 * call, and a button spinner alone leaves the largest thing on screen looking
 * idle while it runs.
 */
function DropZone({ filename }: { filename: string | null }) {
  const { pending } = useFormStatus();

  return (
    <label
      className={cn(
        "flex flex-col items-center gap-3 rounded-xl border border-dashed border-border px-6 py-10 text-center transition-colors",
        pending
          ? "cursor-progress border-primary/40 bg-accent/30"
          : "cursor-pointer hover:border-primary/50 hover:bg-accent/40",
      )}
    >
      {pending ? (
        <Loader2 className="h-7 w-7 animate-spin text-primary" />
      ) : (
        <FileUp className="h-7 w-7 text-primary" />
      )}
      <span className="text-sm font-medium">
        {pending ? "Reading your CV…" : (filename ?? "Drop your CV here")}
      </span>
      <span className="text-xs text-muted-foreground">
        {pending ? "Extracting skills. This takes a moment." : "PDF, up to 5 MB"}
      </span>
      <input
        type="file"
        name="file"
        accept="application/pdf"
        className="hidden"
      />
    </label>
  );
}

export function CvUpload({ remaining }: { remaining: number }) {
  const [state, formAction] = useActionState<CvUploadState, FormData>(
    analyzeCv,
    {},
  );
  const [filename, setFilename] = useState<string | null>(null);
  const outOfQuota = remaining <= 0;

  return (
    <form
      action={formAction}
      // Delegated so the file input stays uncontrolled and needs no ref.
      onChange={(e) => {
        const input = e.target as unknown as HTMLInputElement;
        if (input.type === "file") {
          setFilename(input.files?.[0]?.name ?? null);
        }
      }}
    >
      <PendingFieldset>
        <DropZone filename={filename} />
      </PendingFieldset>

      <SubmitButton
        idle="Analyze CV"
        busy="Reading your CV…"
        disabled={outOfQuota}
        className="mt-4 w-full"
      />

      {state.error ? (
        <div role="alert" className="mt-3 flex items-center justify-center gap-2 rounded-lg bg-destructive/10 px-3 py-2 text-xs text-destructive">
          {state.error}
        </div>
      ) : null}

      <p className="mt-3 text-center text-xs text-muted-foreground">
        {outOfQuota
          ? "You've used today's analyses. More tomorrow."
          : `${remaining} ${remaining === 1 ? "analysis" : "analyses"} left today`}
      </p>
    </form>
  );
}

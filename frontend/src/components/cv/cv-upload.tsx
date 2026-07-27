"use client";

import { FileUp } from "lucide-react";
import { useActionState, useRef, useState } from "react";
import { useFormStatus } from "react-dom";

import { analyzeCv, type CvUploadState } from "@/app/(app)/cv/actions";
import { Button } from "@/components/ui/button";

function SubmitButton({ disabled }: { disabled: boolean }) {
  const { pending } = useFormStatus();
  return (
    <Button type="submit" className="mt-4 w-full" disabled={pending || disabled}>
      {pending ? "Reading your CV…" : "Analyze CV"}
    </Button>
  );
}

export function CvUpload({ remaining }: { remaining: number }) {
  const [state, formAction] = useActionState<CvUploadState, FormData>(
    analyzeCv,
    {},
  );
  const [filename, setFilename] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const outOfQuota = remaining <= 0;

  return (
    <form action={formAction}>
      <label className="flex cursor-pointer flex-col items-center gap-3 rounded-xl border border-dashed border-border px-6 py-10 text-center transition-colors hover:border-primary/50 hover:bg-accent/40">
        <FileUp className="h-7 w-7 text-primary" />
        <span className="text-sm font-medium">
          {filename ?? "Drop your CV here"}
        </span>
        <span className="text-xs text-muted-foreground">PDF, up to 5 MB</span>
        <input
          ref={inputRef}
          type="file"
          name="file"
          accept="application/pdf"
          className="hidden"
          onChange={(e) => setFilename(e.target.files?.[0]?.name ?? null)}
        />
      </label>

      <SubmitButton disabled={outOfQuota} />

      {state.error ? (
        <p role="alert" className="mt-3 text-center text-xs text-destructive">
          {state.error}
        </p>
      ) : null}

      <p className="mt-3 text-center text-xs text-muted-foreground">
        {outOfQuota
          ? "You've used today's analyses. More tomorrow."
          : `${remaining} ${remaining === 1 ? "analysis" : "analyses"} left today`}
      </p>
    </form>
  );
}

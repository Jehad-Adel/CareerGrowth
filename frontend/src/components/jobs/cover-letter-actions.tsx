"use client";

import { Check, Copy, Download } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";

/**
 * Copy and download for a finished letter.
 *
 * Client-side only: the text was assembled server-side and is already on the
 * page, so exporting it needs no round trip and no new endpoint. A Blob and an
 * object URL are enough — a "download" route would only re-serve bytes the
 * browser is holding.
 */
export function CoverLetterActions({
  text,
  jobTitle,
}: {
  text: string;
  jobTitle: string | null;
}) {
  const [copied, setCopied] = useState(false);

  const filename =
    `cover-letter-${jobTitle ?? "role"}`
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-|-$/g, "") + ".txt";

  async function copy() {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard access can be denied outright. The textarea below is
      // selectable, so failing quietly leaves a working manual path.
    }
  }

  function download() {
    const url = URL.createObjectURL(
      new Blob([text], { type: "text/plain;charset=utf-8" }),
    );
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.click();
    // Without this the blob is held for the lifetime of the document.
    URL.revokeObjectURL(url);
  }

  return (
    <div className="flex gap-2">
      <Button type="button" variant="outline" size="sm" onClick={copy}>
        {copied ? (
          <Check className="me-1.5 h-3.5 w-3.5" />
        ) : (
          <Copy className="me-1.5 h-3.5 w-3.5" />
        )}
        {copied ? "Copied" : "Copy"}
      </Button>
      <Button type="button" variant="outline" size="sm" onClick={download}>
        <Download className="me-1.5 h-3.5 w-3.5" />
        Download
      </Button>
    </div>
  );
}

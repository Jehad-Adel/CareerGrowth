"use client";

import { AlertCircle, Loader2, Sprout } from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectItem } from "@/components/ui/select";

import { processVideo } from "./actions";

type VideoResult = {
  title: string;
  summary: string;
  keyTakeaways: string[];
  transcript: string;
  mode: string;
};

export function VideoBody() {
  const [result, setResult] = useState<VideoResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const form = new FormData(e.currentTarget);
    try {
      const res = await processVideo({}, form);
      if (res.error) {
        setError(res.error);
        return;
      }
      if (res.video) {
        setResult(res.video);
      }
    } finally {
      setLoading(false);
    }
  }

  if (result) {
    return (
      <div className="space-y-6 rounded-2xl border bg-card p-4 sm:p-6">
        <div className="flex flex-wrap items-start justify-between gap-3 border-b pb-4">
          <div className="min-w-0">
            <h2 className="text-lg font-semibold text-balance">
              {result.title || "Your video"}
            </h2>
            <p className="mt-1 text-sm text-muted-foreground">
              {result.mode === "summary"
                ? "Summary and key takeaways"
                : "Full transcript"}
            </p>
          </div>
          <Badge variant="secondary" className="shrink-0 capitalize">
            {result.mode}
          </Badge>
        </div>

        {result.mode === "summary" && (
          <>
            <div>
              <h3 className="mb-2 font-medium">Summary</h3>
              <p className="whitespace-pre-wrap text-sm leading-relaxed text-muted-foreground">
                {result.summary}
              </p>
            </div>
            {result.keyTakeaways.length > 0 && (
              <div>
                <h3 className="mb-2 font-medium">Key takeaways</h3>
                <ul className="space-y-2">
                  {result.keyTakeaways.map((t, i) => (
                    <li key={i} className="flex gap-2.5 text-sm">
                      <Sprout
                        className="mt-0.5 h-4 w-4 shrink-0 text-primary"
                        aria-hidden
                      />
                      <span className="text-muted-foreground">{t}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </>
        )}

        {result.mode === "transcript" && (
          <div>
            <h3 className="mb-2 font-medium">Transcript</h3>
            {/* Boxed and tinted so the clipped edge reads as a scroll pane
                rather than text that just stops. `scroll-area` is the
                project's thin scrollbar, same as the chat. */}
            <div className="scroll-area max-h-96 overflow-y-auto rounded-xl border bg-muted/30 p-4">
              <p className="whitespace-pre-wrap text-sm leading-relaxed text-muted-foreground">
                {result.transcript}
              </p>
            </div>
          </div>
        )}

        {/* Secondary action, sized to its label and aligned right — a
            full-width outline bar read as the page's primary control. */}
        <div className="flex justify-end border-t pt-4">
          <Button variant="outline" size="sm" onClick={() => setResult(null)}>
            Process another video
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border bg-card p-4 sm:p-6">
      <div className="mb-6">
        <h2 className="text-lg font-semibold">Process a Video</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Enter a YouTube URL to get an AI summary or full transcript.
        </p>
      </div>
      {/* `flex flex-col gap-4`, not `space-y-4`. The fieldset below is
          `display: contents` so it can carry `disabled` down without adding a
          box — but that also means `space-y`'s `margin-block-end` lands on an
          element that generates no box and is discarded, while the fields
          inside are grandchildren the selector never matches. Everything
          collapsed flush. A flex container hoists the fieldset's children into
          its own layout, so `gap` spaces the fields and the button alike. */}
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <fieldset disabled={loading} className="contents">
          <div className="space-y-2">
            <Label htmlFor="url">Video URL</Label>
            <Input
              id="url"
              name="url"
              type="url"
              inputMode="url"
              placeholder="https://youtube.com/watch?v=..."
              required
              aria-required="true"
              aria-describedby="url-hint"
            />
            <p id="url-hint" className="text-xs text-muted-foreground">
              YouTube links only, and the video needs captions available.
            </p>
          </div>
          <div className="space-y-2">
            <Label htmlFor="mode">Mode</Label>
            <Select id="mode" name="mode" defaultValue="summary">
              <SelectItem value="summary">AI Summary</SelectItem>
              <SelectItem value="transcript">Full Transcript</SelectItem>
            </Select>
          </div>
        </fieldset>
        {error ? (
          <div
            role="alert"
            className="flex items-start gap-2.5 rounded-lg bg-destructive/10 px-3.5 py-2.5 text-xs text-destructive"
          >
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        ) : null}
        <Button type="submit" disabled={loading} aria-busy={loading} className="w-full">
          {loading ? (
            <>
              <Loader2 className="animate-spin" />
              Watching the video…
            </>
          ) : (
            "Process Video"
          )}
        </Button>
      </form>
    </div>
  );
}

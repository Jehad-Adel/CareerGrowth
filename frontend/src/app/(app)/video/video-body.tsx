"use client";

import { AlertCircle, Loader2 } from "lucide-react";
import { useState } from "react";

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
      <div className="rounded-2xl border bg-card p-4 sm:p-6 space-y-6">
        <div>
          <h2 className="text-lg font-semibold">{result.title || "Video Result"}</h2>
          <p className="text-sm text-muted-foreground mt-1">
            {result.mode === "summary" ? "AI-Generated Summary" : "Full Transcript"}
          </p>
        </div>
        {result.mode === "summary" && (
          <>
            <div>
              <h3 className="font-medium mb-2">Summary</h3>
              <p className="text-sm text-muted-foreground whitespace-pre-wrap">{result.summary}</p>
            </div>
            {result.keyTakeaways.length > 0 && (
              <div>
                <h3 className="font-medium mb-2">Key Takeaways</h3>
                <ul className="list-disc pl-5 space-y-1">
                  {result.keyTakeaways.map((t, i) => (
                    <li key={i} className="text-sm text-muted-foreground">{t}</li>
                  ))}
                </ul>
              </div>
            )}
          </>
        )}
        {result.mode === "transcript" && (
          <div>
            <h3 className="font-medium mb-2">Transcript</h3>
            <p className="text-sm text-muted-foreground whitespace-pre-wrap max-h-96 overflow-y-auto">
              {result.transcript}
            </p>
          </div>
        )}
        <Button variant="outline" onClick={() => setResult(null)} className="w-full">
          Process Another Video
        </Button>
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
      <form onSubmit={handleSubmit} className="space-y-4">
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

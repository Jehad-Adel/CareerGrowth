"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

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
    const res = await processVideo({}, form);
    if (res.error) {
      setError(res.error);
      setLoading(false);
      return;
    }
    if (res.videoId) {
      try {
        const { getVideoSummary } = await import("@/lib/services");
        const video = await getVideoSummary(res.videoId);
        setResult({
          title: video.title,
          summary: video.summary,
          keyTakeaways: video.key_takeaways,
          transcript: video.transcript,
          mode: video.mode,
        });
      } catch {
        window.location.reload();
      }
    }
    setLoading(false);
  }

  if (result) {
    return (
      <div className="rounded-2xl border bg-card p-6 space-y-6">
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
    <div className="rounded-2xl border bg-card p-6">
      <div className="mb-6">
        <h2 className="text-lg font-semibold">Process a Video</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Enter a YouTube URL to get an AI summary or full transcript.
        </p>
      </div>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="url">Video URL</Label>
          <Input id="url" name="url" type="url" placeholder="https://youtube.com/watch?v=..." required />
        </div>
        <div className="space-y-2">
          <Label htmlFor="mode">Mode</Label>
          <select
            id="mode"
            name="mode"
            defaultValue="summary"
            className="flex h-11 w-full rounded-lg border border-input bg-transparent px-3 py-2 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
          >
            <option value="summary">AI Summary</option>
            <option value="transcript">Full Transcript</option>
          </select>
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <Button type="submit" disabled={loading} className="w-full">
          {loading ? "Processing..." : "Process Video"}
        </Button>
      </form>
    </div>
  );
}

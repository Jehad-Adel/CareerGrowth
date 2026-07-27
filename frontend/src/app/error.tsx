"use client";

import { useEffect } from "react";

import { Button } from "@/components/ui/button";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Next strips the message in production and leaves a digest that matches
    // a server log line. Log the digest so support can correlate; never
    // render error.message, which can carry internals.
    console.error("Render error", error.digest ?? error);
  }, [error]);

  return (
    <div className="mx-auto flex max-w-md flex-col items-center gap-4 px-6 py-24 text-center">
      <h1 className="text-2xl">Something went wrong</h1>
      <p className="text-sm text-muted-foreground">
        That page failed to load. This is on us, not you.
      </p>
      {error.digest ? (
        <p className="font-mono text-xs text-muted-foreground">
          Reference: {error.digest}
        </p>
      ) : null}
      <Button onClick={reset}>Try again</Button>
    </div>
  );
}

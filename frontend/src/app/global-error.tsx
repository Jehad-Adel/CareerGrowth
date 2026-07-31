"use client";

/**
 * Last resort: catches errors thrown by the root layout itself, where
 * error.tsx cannot help. It replaces the whole document, so it must render
 * its own <html> and <body> and cannot rely on app styles being present.
 */
export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="en">
      <body
        style={{
          fontFamily: "system-ui, sans-serif",
          display: "flex",
          minHeight: "100dvh",
          alignItems: "center",
          justifyContent: "center",
          margin: 0,
          padding: "2rem",
          textAlign: "center",
        }}
      >
        <div>
          <h1 style={{ fontSize: "1.5rem", marginBottom: "0.5rem" }}>
            CareerGrowth is having a problem
          </h1>
          <p style={{ color: "#666", marginBottom: "1rem" }}>
            Reload in a moment. If it keeps happening, let us know
            {error.digest ? ` and quote ${error.digest}` : ""}.
          </p>
          <button
            onClick={reset}
            style={{
              padding: "0.5rem 1rem",
              borderRadius: "0.5rem",
              border: "1px solid #ccc",
              cursor: "pointer",
              background: "transparent",
            }}
          >
            Try again
          </button>
        </div>
      </body>
    </html>
  );
}

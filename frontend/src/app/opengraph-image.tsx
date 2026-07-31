import { ImageResponse } from "next/og";

export const alt = "CareerGrowth — grow your career like a farm";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

/**
 * Generated rather than a static asset so it stays in sync with the copy and
 * needs no design tooling. Uses only system fonts: loading a webfont here
 * costs a network round trip on every crawl.
 */
export default function OpengraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          height: "100%",
          width: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          padding: "80px",
          background: "linear-gradient(135deg, #0f1a12 0%, #1c2b1f 100%)",
          color: "#f4f1e8",
          fontFamily: "sans-serif",
        }}
      >
        {/* Satori requires an explicit `display` on any element with more
            than one child, so each line is its own single-child div. */}
        <div style={{ fontSize: 28, letterSpacing: 4, color: "#8fbf7f" }}>
          CAREERGROWTH
        </div>
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            fontSize: 68,
            lineHeight: 1.1,
            marginTop: 24,
          }}
        >
          <div>Grow your career</div>
          <div>like a farm</div>
        </div>
        <div
          style={{
            fontSize: 28,
            marginTop: 28,
            color: "#b9c4b2",
            maxWidth: 820,
          }}
        >
          Upload your CV once. Every plant is something you actually did.
        </div>
      </div>
    ),
    size,
  );
}

import { ImageResponse } from "next/og";

export const size = { width: 32, height: 32 };
export const contentType = "image/png";

/**
 * The browser-tab icon: the sprout mark from `components/brand/logo.tsx` on
 * the brand green. Replaces the scaffold's `favicon.ico`, which was still the
 * default Next.js logo — shipping a framework's mark as your own is the kind
 * of thing nobody notices until it is in someone else's bookmark bar.
 *
 * Generated rather than a checked-in binary so the mark stays in one place.
 * Paths are the logo's own, scaled from its 24x24 viewBox.
 */
export default function Icon() {
  return new ImageResponse(
    (
      <div
        style={{
          height: "100%",
          width: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "#4c7a4f",
          borderRadius: 7,
        }}
      >
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
          <path
            d="M12 21.5V12"
            stroke="#f2f7ef"
            strokeWidth="2"
            strokeLinecap="round"
          />
          <path
            d="M11.8 12.4C11.8 8.7 9.1 6 5 6c-.4 4.1 2.4 6.4 6.8 6.4Z"
            fill="#f2f7ef"
          />
          <path
            d="M12.3 11.6c0-3.2 2.4-5.6 6-5.2.3 3.6-2.3 5.6-6 5.2Z"
            fill="#f2f7ef"
            opacity="0.82"
          />
          <circle cx="12" cy="21.2" r="1.3" fill="#f2f7ef" />
        </svg>
      </div>
    ),
    size,
  );
}

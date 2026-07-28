import type { NextConfig } from "next";

const isProd = process.env.NODE_ENV === "production";

// The CSP is deliberately NOT here — it needs a per-request nonce, so it is
// built in `src/lib/csp.ts` and set by `src/proxy.ts`. Adding one back to this
// list does not override that header, it adds a second policy: both are
// enforced, and a static `script-src 'self'` would block the nonced scripts
// the proxy just allowed. That failure looks like a page that renders and
// then never hydrates.
const securityHeaders = [
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  {
    // `microphone=(self)`, not `()`. Chrome gates the Web Speech API behind the
    // *microphone* policy, so a blanket denial kills dictation on every route
    // with a `not-allowed` error that reads exactly like the user refusing the
    // permission prompt — the prompt never appears at all. Same-origin only;
    // no third-party frame inherits it.
    key: "Permissions-Policy",
    value: "camera=(), microphone=(self), geolocation=(), interest-cohort=()",
  },
  ...(isProd
    ? [
        {
          key: "Strict-Transport-Security",
          value: "max-age=31536000; includeSubDomains",
        },
      ]
    : []),
];

const nextConfig: NextConfig = {
  async headers() {
    return [{ source: "/:path*", headers: securityHeaders }];
  },
};

export default nextConfig;

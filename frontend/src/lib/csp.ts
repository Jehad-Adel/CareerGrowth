/**
 * Content-Security-Policy, built per request.
 *
 * This cannot live in `next.config.ts` like the other security headers. The
 * App Router emits inline bootstrap scripts (`self.__next_f.push(...)`) on
 * every page, so a static `script-src 'self'` blocks them all and the page
 * ships as dead HTML that never hydrates. Next injects a nonce into its own
 * scripts only when it finds one in the *request's* CSP header, which means
 * the policy has to be generated in `proxy.ts`. Do not add a second CSP in
 * `next.config.ts`: two headers are both enforced, and the static one would
 * block the very scripts the nonce just allowed.
 */

const isProd = process.env.NODE_ENV === "production";
const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL ?? "";

/** A fresh nonce per request. Predictable values defeat the whole mechanism. */
export function generateNonce(): string {
  return Buffer.from(crypto.randomUUID()).toString("base64");
}

export function buildCsp(nonce: string): string {
  return [
    "default-src 'self'",
    // 'strict-dynamic' lets the nonced bootstrap load the chunk scripts it
    // needs without naming each one; browsers that honour it ignore 'self'
    // here, which is kept only for older ones. 'unsafe-eval' is React's
    // dev-only error reconstruction and is dropped in production.
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'${isProd ? "" : " 'unsafe-eval'"}`,
    // Still 'unsafe-inline' rather than the nonce: Tailwind injects styles at
    // runtime. An injected stylesheet is a far smaller problem than injected
    // script, and nonce-ing this breaks the styling outright.
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: blob:",
    "font-src 'self' data:",
    `connect-src 'self' ${apiUrl} ${supabaseUrl}`.trim(),
    "frame-ancestors 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "object-src 'none'",
    ...(isProd ? ["upgrade-insecure-requests"] : []),
  ].join("; ");
}

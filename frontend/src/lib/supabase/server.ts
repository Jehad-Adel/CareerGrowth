import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";

/**
 * Server-side Supabase client for Server Components, Server Actions, and
 * Route Handlers. Reads and writes the session cookies.
 *
 * `cookies()` is async in Next 16, so this must be awaited.
 */
export async function createClient() {
  const cookieStore = await cookies();

  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll();
        },
        setAll(cookiesToSet) {
          try {
            for (const { name, value, options } of cookiesToSet) {
              cookieStore.set(name, value, options);
            }
          } catch {
            // Server Components cannot set cookies. That is fine and expected:
            // proxy.ts refreshes the session on every request, so the write
            // this call would have made has already happened there.
            // Swallowing here is the documented pattern, not a lost error.
          }
        },
      },
    },
  );
}

/**
 * Verified claims for the current user, or null.
 *
 * Uses `getClaims()` rather than `getSession()`. This project signs tokens
 * with an asymmetric ES256 key, and `getClaims()` verifies the signature
 * locally against the JWKS endpoint. `getSession()` returns whatever is in
 * the cookie without verifying it — the library's own docs say that value
 * must not be trusted.
 */
export async function getVerifiedClaims() {
  const supabase = await createClient();
  const { data, error } = await supabase.auth.getClaims();
  if (error || !data?.claims) return null;
  return data.claims;
}

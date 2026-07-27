import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";

/**
 * Refresh the Supabase session for this request and report who the caller is.
 *
 * Returns the response that carries any refreshed cookies. Callers must build
 * their redirects by copying cookies off this response, or the refresh is lost
 * and the user is silently logged out on the next hop.
 */
export async function updateSession(request: NextRequest) {
  let response = NextResponse.next({ request });

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll();
        },
        setAll(cookiesToSet, headers) {
          for (const { name, value } of cookiesToSet) {
            request.cookies.set(name, value);
          }
          response = NextResponse.next({ request });
          for (const { name, value, options } of cookiesToSet) {
            response.cookies.set(name, value, options);
          }
          // The second argument carries Cache-Control: private, no-store and
          // friends. Without it a CDN is free to cache a response that sets
          // auth cookies and serve one user's session to another. On Vercel
          // that is a live cross-user session leak, not a theoretical one.
          for (const [key, headerValue] of Object.entries(headers ?? {})) {
            response.headers.set(key, headerValue);
          }
        },
      },
    },
  );

  // Verified locally against the JWKS endpoint. Not getSession(), whose
  // return value the library explicitly documents as untrustworthy.
  const { data, error } = await supabase.auth.getClaims();
  const claims = error ? null : (data?.claims ?? null);

  return { response, claims };
}

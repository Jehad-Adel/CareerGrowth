import { NextResponse, type NextRequest } from "next/server";

import { buildCsp, generateNonce } from "@/lib/csp";
import { AUTH_ROUTES, isProtectedRoute } from "@/lib/routes";
import { updateSession } from "@/lib/supabase/proxy";

/**
 * Route guard and session refresh.
 *
 * In Next 16 this file is `proxy.ts`, not `middleware.ts`. A file named
 * `middleware.ts` is ignored outright — the guard would never run and every
 * app route would stay public.
 *
 * This is an OPTIMISTIC check, per the Next docs: it stops a logged-out
 * visitor seeing an app shell. It is not the authorization boundary. That
 * lives in the FastAPI service, which verifies the token's ES256 signature
 * against Supabase's JWKS on every request.
 *
 * It also mints the CSP nonce — see `lib/csp.ts` for why the policy cannot be
 * a static header.
 */

function copyCookies(from: NextResponse, to: NextResponse) {
  for (const cookie of from.cookies.getAll()) {
    to.cookies.set(cookie);
  }
  // Carry the cache-control headers the Supabase client set alongside the
  // cookies; a redirect that sets auth cookies must not be cacheable either.
  for (const [key, value] of from.headers.entries()) {
    if (key.toLowerCase().startsWith("cache-control") || key.toLowerCase() === "pragma" || key.toLowerCase() === "expires") {
      to.headers.set(key, value);
    }
  }
  return to;
}

export async function proxy(request: NextRequest) {
  const nonce = generateNonce();
  const csp = buildCsp(nonce);

  // Next reads the nonce off the *request* CSP header during render and
  // stamps it onto its own script tags; `x-nonce` is for our own code, should
  // a Server Component ever need to pass it to a <Script>.
  const { response, claims } = await updateSession(request, {
    "x-nonce": nonce,
    "Content-Security-Policy": csp,
  });
  const { pathname } = request.nextUrl;

  const needsAuth = isProtectedRoute(pathname);
  const isAuthRoute = AUTH_ROUTES.some((route) => pathname === route);

  if (needsAuth && !claims) {
    const url = request.nextUrl.clone();
    url.pathname = "/login";
    url.search = "";
    // Round-trip the destination so login can send them where they meant to go.
    url.searchParams.set("next", pathname);
    return copyCookies(response, NextResponse.redirect(url));
  }

  if (isAuthRoute && claims) {
    const url = request.nextUrl.clone();
    url.pathname = "/dashboard";
    url.search = "";
    return copyCookies(response, NextResponse.redirect(url));
  }

  response.headers.set("Content-Security-Policy", csp);
  return response;
}

export const config = {
  matcher: [
    // Everything except Next internals and static assets. Running the guard
    // on every image would add a JWKS verification per asset request.
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico|woff2?)$).*)",
  ],
};

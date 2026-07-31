/**
 * The authenticated surface, in one place.
 *
 * Three things have to agree on this list and used to drift apart silently:
 * `proxy.ts` (redirects anonymous visitors), `robots.ts` (keeps crawlers off),
 * and `nav.ts` (renders the sidebar). Applications, Quiz, Video, Offers, and
 * Alerts all shipped in the sidebar while `proxy.ts` and `robots.ts` still
 * listed only the original seven, so five routes served their app shell to
 * logged-out visitors and were crawlable.
 *
 * `NavItem["href"]` is typed as `ProtectedRoute`, so adding a sidebar entry
 * without adding it here is a compile error rather than a silent hole.
 *
 * This module must stay dependency-free: `proxy.ts` imports it on the request
 * path, and pulling an icon library through there would cost every request.
 */

export const PROTECTED_ROUTES = [
  "/dashboard",
  "/farm",
  "/cv",
  "/jobs",
  "/applications",
  "/interview",
  "/roadmap",
  "/quiz",
  "/video",
  "/offers",
  "/notifications",
  "/chat",
] as const;

export type ProtectedRoute = (typeof PROTECTED_ROUTES)[number];

/** Signed-in users have no business on these. */
export const AUTH_ROUTES = ["/login", "/signup"] as const;

/** True when `pathname` is a protected route or sits underneath one. */
export function isProtectedRoute(pathname: string): boolean {
  return PROTECTED_ROUTES.some(
    (route) => pathname === route || pathname.startsWith(`${route}/`),
  );
}

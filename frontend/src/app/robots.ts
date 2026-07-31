import type { MetadataRoute } from "next";

import { PROTECTED_ROUTES } from "@/lib/routes";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      // Everything behind auth. Crawlers get redirected to /login anyway,
      // but saying so avoids a pile of pointless 307s in the logs. Derived
      // from lib/routes.ts so a new app route cannot be left indexable —
      // five of them were, before that list existed.
      disallow: [...PROTECTED_ROUTES, "/auth/"],
    },
    sitemap: `${SITE_URL}/sitemap.xml`,
  };
}

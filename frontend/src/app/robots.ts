import type { MetadataRoute } from "next";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      // Everything behind auth. Crawlers get redirected to /login anyway,
      // but saying so avoids a pile of pointless 307s in the logs.
      disallow: [
        "/dashboard",
        "/cv",
        "/farm",
        "/jobs",
        "/interview",
        "/roadmap",
        "/chat",
        "/auth/",
      ],
    },
    sitemap: `${SITE_URL}/sitemap.xml`,
  };
}

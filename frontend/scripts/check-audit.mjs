// Gate for `npm audit --omit=dev` in CI.
//
// npm audit exits non-zero on any finding at all, and a few of ours are
// transitive under a pinned next with no upgrade path — `npm audit fix --force`
// "fixes" them by installing next@9. Muting the whole job would hide the next
// real advisory just as effectively, so instead each accepted finding is
// listed here by GHSA id and anything else fails the build.
//
// Usage: node scripts/check-audit.mjs <path to `npm audit --json` output>

import { readFileSync } from "node:fs";

// Every entry needs a reason and a way out. Delete one the moment it stops
// appearing — a stale allow is how a real advisory sneaks through later.
const ACCEPTED = {
  // postcss, transitive under next@16.2.11. Fixed in a next release that
  // does not exist yet: the advisory range covers through 16.3.0-preview.7
  // and 16.2.12 is the current latest.
  "GHSA-qx2v-qp2m-jg93": "postcss XSS via unescaped </style>",
  "GHSA-6g55-p6wh-862q": "postcss sourceMappingURL arbitrary file read",
  "GHSA-r28c-9q8g-f849": "postcss sourceMappingURL path traversal",
  // sharp/libvips, same story: next pins it and only ships images through it
  // at build time.
  "GHSA-f88m-g3jw-g9cj": "sharp inherited libvips CVEs",
};

const reportPath = process.argv[2];
if (!reportPath) {
  console.error("usage: node scripts/check-audit.mjs <audit.json>");
  process.exit(2);
}

// A parse failure must fail the job. Swallowing it would turn a broken audit
// into a green check, which is the one outcome this script exists to prevent.
let report;
try {
  report = JSON.parse(readFileSync(reportPath, "utf8"));
} catch (error) {
  console.error(`::error::Could not read ${reportPath}: ${error.message}`);
  process.exit(2);
}

if (!report.vulnerabilities || typeof report.vulnerabilities !== "object") {
  console.error("::error::Audit report has no `vulnerabilities` object — npm's --json shape changed");
  process.exit(2);
}

const found = new Map();
for (const vuln of Object.values(report.vulnerabilities)) {
  for (const via of vuln.via ?? []) {
    if (typeof via !== "object" || !via.url) continue;
    const id = via.url.match(/GHSA-[a-z0-9-]+/)?.[0];
    if (id) found.set(id, via.title ?? vuln.name);
  }
}

const unexpected = [...found].filter(([id]) => !(id in ACCEPTED));
if (unexpected.length > 0) {
  console.error("::error::Advisory not on the accepted list — review it, then allow or fix:");
  for (const [id, title] of unexpected) console.error(`  ${id}  ${title}`);
  process.exit(1);
}

const stale = Object.keys(ACCEPTED).filter((id) => !found.has(id));
if (stale.length > 0) {
  // Not a failure: a resolved advisory should not break the build on the way
  // out. But say so loudly, so the list gets pruned.
  console.log(`::warning::Accepted advisories no longer reported, remove them from ${import.meta.url.split("/").pop()}: ${stale.join(", ")}`);
}

console.log(`${found.size} advisory/advisories reported, all accepted:`);
for (const [id, title] of found) console.log(`  ${id}  ${title}`);

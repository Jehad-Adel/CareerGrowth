// Gate for `npm audit --omit=dev` in CI.
//
// Every new advisory fails the gate. Next 16.4.0 and compatible lockfile
// refreshes resolved the historical Next/PostCSS/sharp accepted findings.
//
// Usage: node scripts/check-audit.mjs <path to `npm audit --json` output>

import { readFileSync } from "node:fs";

// Every entry needs a reason and a way out. Delete one the moment it stops
// appearing — a stale allow is how a real advisory sneaks through later.
const ACCEPTED = {};

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

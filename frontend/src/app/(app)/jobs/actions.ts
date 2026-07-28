"use server";

import { revalidatePath } from "next/cache";

import { normalizeApiError } from "@/lib/api/error";
import { serverFetch } from "@/lib/api/server";

export type JobActionState = {
  error?: string;
  ok?: boolean;
};

// Mirrors the API's bounds so an obvious mistake fails without a round trip.
const MIN_JD = 50;
const MAX_JD = 20_000;

function readJob(formData: FormData) {
  const jd = String(formData.get("job_description") ?? "").trim();
  const titleRaw = String(formData.get("job_title") ?? "").trim();
  return { jd, title: titleRaw || null };
}

function validate(jd: string): string | null {
  if (jd.length < MIN_JD) {
    return `Paste the full job description — at least ${MIN_JD} characters.`;
  }
  if (jd.length > MAX_JD) {
    return "That job description is too long. Trim it to the essentials.";
  }
  return null;
}

async function run(
  path: string,
  formData: FormData,
  revalidate: string[],
): Promise<JobActionState> {
  const { jd, title } = readJob(formData);
  const invalid = validate(jd);
  if (invalid) return { error: invalid };

  try {
    await serverFetch(path, {
      method: "POST",
      body: JSON.stringify({ job_description: jd, job_title: title }),
    });
  } catch (error) {
    return {
      error: normalizeApiError(
        error,
        "Could not run that analysis. Try again shortly.",
      ),
    };
  }

  for (const p of revalidate) revalidatePath(p);
  return { ok: true };
}

export async function matchJob(
  _prev: JobActionState,
  formData: FormData,
): Promise<JobActionState> {
  return run("/jobs/match", formData, ["/jobs", "/dashboard", "/farm"]);
}

export async function analyzeGap(
  _prev: JobActionState,
  formData: FormData,
): Promise<JobActionState> {
  return run("/skills/gap", formData, ["/jobs", "/dashboard", "/farm"]);
}

export async function writeCoverLetter(
  _prev: JobActionState,
  formData: FormData,
): Promise<JobActionState> {
  // No farm or dashboard revalidation: a letter presents capability the CV
  // already proved, so nothing grew and no XP was awarded.
  return run("/jobs/cover-letter", formData, ["/jobs"]);
}

export async function optimizeResume(
  _prev: JobActionState,
  formData: FormData,
): Promise<JobActionState> {
  const { jd, title } = readJob(formData);
  if (jd) {
    const invalid = validate(jd);
    if (invalid) return { error: invalid };
  }

  try {
    await serverFetch("/cv/optimize", {
      method: "POST",
      body: JSON.stringify({
        job_description: jd || null,
        job_title: title || null,
      }),
    });
  } catch (error) {
    return {
      error: normalizeApiError(
        error,
        "Could not optimize your resume. Try again shortly.",
      ),
    };
  }

  revalidatePath("/jobs");
  return { ok: true };
}

import { redirect } from "next/navigation";
import { cache } from "react";

import { ApiError } from "@/lib/api/error";
import { createClient } from "@/lib/supabase/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/**
 * Server-side fetch against the FastAPI backend.
 *
 * Reads the session from cookies and forwards the access token as a bearer.
 * The API verifies that token's ES256 signature against Supabase's JWKS, so
 * this is the real authorization boundary — the proxy guard is only UX.
 *
 * Pages must not call this directly. Everything goes through lib/services.ts,
 * so swapping a mock for a real endpoint stays a one-line change.
 */
/**
 * `cache()` scopes this to one request. A page that fetches three endpoints in
 * parallel would otherwise build three Supabase clients and parse the cookie
 * jar three times for the same token.
 */
const bearer = cache(async (): Promise<Record<string, string>> => {
  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  return session?.access_token
    ? { Authorization: `Bearer ${session.access_token}` }
    : {};
});

async function fetchWithTimeout(
  url: string,
  init: RequestInit,
  timeoutMs = 60000,
): Promise<Response> {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, {
      ...init,
      signal: init.signal ?? controller.signal,
    });
  } finally {
    clearTimeout(id);
  }
}

export async function serverFetch<T>(
  path: string,
  init: RequestInit = {},
  timeoutMs = 60000,
): Promise<T> {
  const res = await fetchWithTimeout(
    `${API_URL}${path}`,
    {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(await bearer()),
        ...init.headers,
      },
      // Per-user data. Caching it would serve one user's profile to another.
      cache: "no-store",
    },
    timeoutMs,
  );

  if (res.status === 401) {
    // The session died server-side. Bounce to login rather than rendering a
    // half-empty app shell.
    redirect("/login");
  }

  if (!res.ok) {
    const body = (await res.json().catch(() => null)) as
      | { detail?: string }
      | null;
    throw new ApiError(res.status, body?.detail ?? res.statusText);
  }

  return res.status === 204 ? (undefined as T) : ((await res.json()) as T);
}

/**
 * Multipart variant for file uploads.
 *
 * Deliberately does NOT set Content-Type: fetch must generate it so the
 * multipart boundary matches the body. Setting it by hand yields a body the
 * server cannot parse.
 */
export async function serverFetchForm<T>(
  path: string,
  body: FormData,
  timeoutMs = 60000,
): Promise<T> {
  const res = await fetchWithTimeout(
    `${API_URL}${path}`,
    {
      method: "POST",
      headers: await bearer(),
      body,
      cache: "no-store",
    },
    timeoutMs,
  );

  if (res.status === 401) {
    redirect("/login");
  }

  if (!res.ok) {
    const parsed = (await res.json().catch(() => null)) as
      | { detail?: string }
      | null;
    throw new ApiError(res.status, parsed?.detail ?? res.statusText);
  }

  return res.status === 204 ? (undefined as T) : ((await res.json()) as T);
}


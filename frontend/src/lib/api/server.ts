import { redirect } from "next/navigation";

import { ApiError } from "@/lib/api/client";
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
export async function serverFetch<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(session?.access_token
        ? { Authorization: `Bearer ${session.access_token}` }
        : {}),
      ...init.headers,
    },
    // Per-user data. Caching it would serve one user's profile to another.
    cache: "no-store",
  });

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

import { createBrowserClient } from "@supabase/ssr";

/**
 * Browser-side Supabase client. Handles auth (signup/login/session).
 * The access token it holds is sent to the FastAPI backend by `apiFetch`.
 */
export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
  );
}

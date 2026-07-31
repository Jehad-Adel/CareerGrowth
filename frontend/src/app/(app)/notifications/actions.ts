"use server";

import { revalidatePath } from "next/cache";

import { normalizeApiError } from "@/lib/api/error";
import { serverFetch } from "@/lib/api/server";

export type NotificationActionState = { ok: boolean; error?: string };

/**
 * These used to `catch {}` with a "silently fail" comment. Two things went
 * wrong with that. The caller optimistically flipped the row to read, so a
 * failed write left the UI disagreeing with the database until the next
 * reload. And `serverFetch` answers a 401 by throwing `redirect("/login")`,
 * which the bare catch swallowed — an expired session made the button do
 * nothing at all instead of bouncing to login. `normalizeApiError` re-throws
 * that control flow and turns everything else into a safe message.
 */
export async function markRead(
  notificationId: string,
): Promise<NotificationActionState> {
  try {
    await serverFetch(`/notifications/${notificationId}/read`, {
      method: "POST",
    });
  } catch (error) {
    return { ok: false, error: normalizeApiError(error, "Could not dismiss that notification.") };
  }
  revalidatePath("/notifications");
  return { ok: true };
}

export async function markAllRead(): Promise<NotificationActionState> {
  try {
    await serverFetch("/notifications/read-all", { method: "POST" });
  } catch (error) {
    return { ok: false, error: normalizeApiError(error, "Could not mark everything read.") };
  }
  revalidatePath("/notifications");
  return { ok: true };
}

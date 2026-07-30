"use server";

import { revalidatePath } from "next/cache";

import { serverFetch } from "@/lib/api/server";

export async function markRead(notificationId: string) {
  try {
    await serverFetch(`/notifications/${notificationId}/read`, { method: "POST" });
  } catch {
    // silently fail
  }
  revalidatePath("/notifications");
}

export async function markAllRead() {
  try {
    await serverFetch("/notifications/read-all", { method: "POST" });
  } catch {
    // silently fail
  }
  revalidatePath("/notifications");
}

"use server";

import { revalidatePath } from "next/cache";

import { normalizeApiError } from "@/lib/api/error";
import { serverFetch } from "@/lib/api/server";

export type VideoActionState = {
  error?: string;
  ok?: boolean;
  videoId?: string;
  submittedAt?: number;
};

export async function processVideo(
  _prev: VideoActionState,
  formData: FormData,
): Promise<VideoActionState> {
  const url = String(formData.get("url") ?? "").trim();
  const mode = String(formData.get("mode") ?? "summary");

  if (!url) return { error: "Video URL is required." };

  try {
    const result = await serverFetch<{ id: string }>("/video/process", {
      method: "POST",
      body: JSON.stringify({ url, mode }),
    });
    revalidatePath("/video");
    revalidatePath("/dashboard");
    revalidatePath("/farm");
    return { ok: true, videoId: result.id, submittedAt: Date.now() };
  } catch (error) {
    return {
      error: normalizeApiError(error, "Could not process that video. Try again shortly."),
    };
  }
}

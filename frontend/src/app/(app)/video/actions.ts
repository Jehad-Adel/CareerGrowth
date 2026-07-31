"use server";

import { revalidatePath } from "next/cache";

import { normalizeApiError } from "@/lib/api/error";
import { serverFetch } from "@/lib/api/server";

export type VideoResultState = {
  title: string;
  summary: string;
  keyTakeaways: string[];
  transcript: string;
  mode: string;
};

export type VideoActionState = {
  error?: string;
  ok?: boolean;
  videoId?: string;
  video?: VideoResultState;
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
    const result = await serverFetch<{
      id: string;
      title: string;
      summary: string;
      key_takeaways: string[];
      transcript: string;
      mode: string;
    }>("/video/process", {
      method: "POST",
      body: JSON.stringify({ url, mode }),
    });
    revalidatePath("/video");
    revalidatePath("/dashboard");
    revalidatePath("/farm");
    const video = {
      title: result.title,
      summary: result.summary,
      keyTakeaways: result.key_takeaways,
      transcript: result.transcript,
      mode: result.mode,
    };
    return { ok: true, videoId: result.id, video, submittedAt: Date.now() };
  } catch (error) {
    return {
      error: normalizeApiError(error, "Could not process that video. Try again shortly."),
    };
  }
}

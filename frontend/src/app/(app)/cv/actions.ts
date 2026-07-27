"use server";

import { revalidatePath } from "next/cache";

import { ApiError } from "@/lib/api/client";
import { serverFetchForm } from "@/lib/api/server";

export type CvUploadState = {
  error?: string;
  ok?: boolean;
};

const MAX_BYTES = 5 * 1024 * 1024;

export async function analyzeCv(
  _prev: CvUploadState,
  formData: FormData,
): Promise<CvUploadState> {
  const file = formData.get("file");

  if (!(file instanceof File) || file.size === 0) {
    return { error: "Choose a PDF to analyze." };
  }
  // Mirrors the server's cap so an oversized file fails instantly instead of
  // being uploaded first. The API enforces this again; this is only courtesy.
  if (file.size > MAX_BYTES) {
    return { error: "That file is larger than 5 MB." };
  }

  const body = new FormData();
  body.append("file", file);

  try {
    await serverFetchForm("/cv/analyze", body);
  } catch (error) {
    if (error instanceof ApiError) {
      // The API's messages are written for humans and carry no internals.
      return { error: error.message };
    }
    return { error: "Could not analyze that CV. Try again shortly." };
  }

  revalidatePath("/cv");
  revalidatePath("/dashboard");
  return { ok: true };
}

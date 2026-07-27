"use server";

import { revalidatePath } from "next/cache";

import { ApiError } from "@/lib/api/error";
import { serverFetch } from "@/lib/api/server";

export type RoadmapActionState = {
  error?: string;
  ok?: boolean;
};

const TOUCHED = ["/roadmap", "/farm", "/dashboard"];

export async function generateRoadmap(
  _prev: RoadmapActionState,
  formData: FormData,
): Promise<RoadmapActionState> {
  const raw = String(formData.get("target_role") ?? "").trim();

  try {
    await serverFetch("/roadmap", {
      method: "POST",
      body: JSON.stringify({ target_role: raw || null }),
    });
  } catch (error) {
    if (error instanceof ApiError) return { error: error.message };
    return { error: "Could not build a roadmap. Try again shortly." };
  }

  for (const p of TOUCHED) revalidatePath(p);
  return { ok: true };
}

export async function completeStep(
  _prev: RoadmapActionState,
  formData: FormData,
): Promise<RoadmapActionState> {
  const stepId = String(formData.get("step_id") ?? "");
  if (!stepId) return { error: "Missing step." };

  try {
    await serverFetch(`/roadmap/steps/${stepId}/complete`, { method: "POST" });
  } catch (error) {
    if (error instanceof ApiError) return { error: error.message };
    return { error: "Could not mark that step done." };
  }

  // The farm grows off this event, so it must be revalidated too.
  for (const p of TOUCHED) revalidatePath(p);
  return { ok: true };
}

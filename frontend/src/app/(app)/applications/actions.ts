"use server";

import { revalidatePath } from "next/cache";

import { ApiError } from "@/lib/api/error";
import { serverFetch } from "@/lib/api/server";

export type ApplicationActionState = {
  error?: string;
  ok?: boolean;
  submittedAt?: number;
};

const PATH = "/applications";

function fail(error: unknown, fallback: string): ApplicationActionState {
  if (error instanceof ApiError) return { error: error.message };
  return { error: fallback };
}

export async function addApplication(
  _prev: ApplicationActionState,
  formData: FormData,
): Promise<ApplicationActionState> {
  const company = String(formData.get("company") ?? "").trim();
  const role = String(formData.get("role") ?? "").trim();
  const url = String(formData.get("url") ?? "").trim();

  if (!company || !role) return { error: "Company and role are both needed." };

  try {
    await serverFetch(PATH, {
      method: "POST",
      body: JSON.stringify({
        company,
        role,
        url,
        status: String(formData.get("status") ?? "saved"),
      }),
    });
  } catch (error) {
    return fail(error, "Could not save that application.");
  }

  revalidatePath(PATH);
  return { ok: true, submittedAt: Date.now() };
}

export async function moveApplication(formData: FormData): Promise<void> {
  const id = String(formData.get("id") ?? "");
  const status = String(formData.get("status") ?? "");
  if (!id || !status) return;

  try {
    await serverFetch(`${PATH}/${id}/status`, {
      method: "POST",
      body: JSON.stringify({ status }),
    });
  } catch {
    // A failed move leaves the card where it was, which the revalidate below
    // makes visible. Nothing is lost, so there is no error state to thread
    // through a button that has none.
  }
  revalidatePath(PATH);
}

export async function deleteApplication(formData: FormData): Promise<void> {
  const id = String(formData.get("id") ?? "");
  if (!id) return;

  try {
    await serverFetch(`${PATH}/${id}`, { method: "DELETE" });
  } catch {
    // As above.
  }
  revalidatePath(PATH);
}

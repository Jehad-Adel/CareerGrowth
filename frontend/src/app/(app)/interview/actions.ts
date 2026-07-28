"use server";

import { revalidatePath } from "next/cache";

import { normalizeApiError } from "@/lib/api/error";
import { serverFetch } from "@/lib/api/server";

export type InterviewActionState = {
  error?: string;
  ok?: boolean;
  /**
   * When a submission was accepted. A controlled input needs to know that
   * *this* submit succeeded, and `ok` cannot say that — once true it stays
   * true, so the second answer would never clear the field.
   */
  submittedAt?: number;
};

const MIN_JD = 50;
const MAX_JD = 20_000;
const MAX_ANSWER = 8_000;

export async function startInterview(
  _prev: InterviewActionState,
  formData: FormData,
): Promise<InterviewActionState> {
  const level = String(formData.get("level") ?? "");
  const jd = String(formData.get("job_description") ?? "").trim();

  if (jd.length < MIN_JD) {
    return { error: `Paste the full job description — at least ${MIN_JD} characters.` };
  }
  if (jd.length > MAX_JD) {
    return { error: "That job description is too long." };
  }

  try {
    await serverFetch("/interview/sessions", {
      method: "POST",
      body: JSON.stringify({ level, job_description: jd }),
    });
  } catch (error) {
    return {
      error: normalizeApiError(
        error,
        "Could not start the interview. Try again shortly.",
      ),
    };
  }

  revalidatePath("/interview");
  return { ok: true, submittedAt: Date.now() };
}

export async function submitAnswer(
  _prev: InterviewActionState,
  formData: FormData,
): Promise<InterviewActionState> {
  const sessionId = String(formData.get("session_id") ?? "");
  const answer = String(formData.get("answer") ?? "").trim();

  if (!sessionId) return { error: "Missing session." };
  if (!answer) return { error: "Write an answer first." };
  if (answer.length > MAX_ANSWER) {
    return { error: "That answer is too long." };
  }

  try {
    // Only the answer text is sent. History, persona, and the interviewer's
    // name are rebuilt server-side from the database — a client that could
    // supply those could rewrite what the model thinks already happened.
    await serverFetch(`/interview/sessions/${sessionId}/answer`, {
      method: "POST",
      body: JSON.stringify({ answer }),
    });
  } catch (error) {
    return {
      error: normalizeApiError(
        error,
        "Could not submit that answer. Try again shortly.",
      ),
    };
  }

  // A finished interview awards XP, so the farm changes too.
  revalidatePath("/interview");
  revalidatePath("/dashboard");
  revalidatePath("/farm");
  return { ok: true, submittedAt: Date.now() };
}

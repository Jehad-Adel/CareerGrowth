"use server";

import { revalidatePath } from "next/cache";

import { normalizeApiError } from "@/lib/api/error";
import { serverFetch } from "@/lib/api/server";

export type QuizActionState = {
  error?: string;
  ok?: boolean;
  attemptId?: string;
  submittedAt?: number;
};

export async function generateQuiz(
  _prev: QuizActionState,
  formData: FormData,
): Promise<QuizActionState> {
  const sourceText = String(formData.get("source_text") ?? "").trim();
  const masteryLevel = Number(formData.get("mastery_level") ?? 1);
  const numQuestions = Number(formData.get("num_questions") ?? 5);
  const sourceTitle = String(formData.get("source_title") ?? "").trim();

  if (!sourceText || sourceText.length < 10) {
    return { error: "Source text must be at least 10 characters." };
  }

  try {
    const result = await serverFetch<{ id: string }>("/quiz/generate", {
      method: "POST",
      body: JSON.stringify({
        source_text: sourceText,
        mastery_level: Math.max(1, Math.min(5, masteryLevel)),
        num_questions: Math.max(1, Math.min(20, numQuestions)),
        source_title: sourceTitle,
      }),
    });
    revalidatePath("/quiz");
    return { ok: true, attemptId: result.id, submittedAt: Date.now() };
  } catch (error) {
    return {
      error: normalizeApiError(error, "Could not generate quiz. Try again shortly."),
    };
  }
}

export async function submitQuizAnswers(
  _prev: QuizActionState,
  formData: FormData,
): Promise<QuizActionState> {
  const attemptId = String(formData.get("attempt_id") ?? "");
  const answersRaw = String(formData.get("answers") ?? "[]");

  if (!attemptId) return { error: "Missing attempt ID." };

  try {
    const answers: number[] = JSON.parse(answersRaw);
    await serverFetch(`/quiz/attempts/${attemptId}/submit`, {
      method: "POST",
      body: JSON.stringify({ answers }),
    });
    revalidatePath("/quiz");
    revalidatePath("/dashboard");
    revalidatePath("/farm");
    return { ok: true, submittedAt: Date.now() };
  } catch (error) {
    return {
      error: normalizeApiError(error, "Could not submit answers. Try again shortly."),
    };
  }
}

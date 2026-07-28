"use server";

import { revalidatePath } from "next/cache";

import { normalizeApiError } from "@/lib/api/error";
import { serverFetch } from "@/lib/api/server";

export type ChatActionState = {
  error?: string;
  ok?: boolean;
};

const MAX_MESSAGE = 4_000;

export async function askQuestion(
  _prev: ChatActionState,
  formData: FormData,
): Promise<ChatActionState> {
  const message = String(formData.get("message") ?? "").trim();

  if (!message) return { error: "Type a question first." };
  if (message.length > MAX_MESSAGE) {
    return { error: "That message is too long." };
  }

  try {
    await serverFetch("/chat", {
      method: "POST",
      body: JSON.stringify({ message }),
    });
  } catch (error) {
    return {
      error: normalizeApiError(
        error,
        "The assistant is unavailable. Try again shortly.",
      ),
    };
  }

  revalidatePath("/chat");
  return { ok: true };
}

export async function clearChat(): Promise<ChatActionState> {
  try {
    await serverFetch("/chat", {
      method: "DELETE",
    });
  } catch (error) {
    return {
      error: normalizeApiError(error, "Could not clear chat history."),
    };
  }

  revalidatePath("/chat");
  return { ok: true };
}

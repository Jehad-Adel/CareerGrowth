"use server";

import { revalidatePath } from "next/cache";

import { normalizeApiError } from "@/lib/api/error";
import { serverFetch } from "@/lib/api/server";

export type OfferResultState = {
  company: string;
  roleTitle: string;
  overallScore: number;
  recommendation: string;
  result: Record<string, unknown>;
};

export type OfferActionState = {
  error?: string;
  ok?: boolean;
  offerId?: string;
  offer?: OfferResultState;
  submittedAt?: number;
};

export async function evaluateOffer(
  _prev: OfferActionState,
  formData: FormData,
): Promise<OfferActionState> {
  const company = String(formData.get("company") ?? "").trim();
  const roleTitle = String(formData.get("role_title") ?? "").trim();
  const offerDetails = String(formData.get("offer_details") ?? "").trim();

  if (!company) return { error: "Company name is required." };
  if (!roleTitle) return { error: "Role title is required." };
  if (!offerDetails || offerDetails.length < 20) {
    return { error: "Please provide detailed offer information (at least 20 characters)." };
  }

  try {
    const result = await serverFetch<{
      id: string;
      company: string;
      role_title: string;
      overall_score?: number | null;
      recommendation: string;
      result: Record<string, unknown>;
    }>("/offers/evaluate", {
      method: "POST",
      body: JSON.stringify({ company, role_title: roleTitle, offer_details: offerDetails }),
    });
    revalidatePath("/offers");
    revalidatePath("/dashboard");
    revalidatePath("/farm");
    const offer = {
      company: result.company,
      roleTitle: result.role_title,
      overallScore: result.overall_score ?? 0,
      recommendation: result.recommendation,
      result: result.result,
    };
    return { ok: true, offerId: result.id, offer, submittedAt: Date.now() };
  } catch (error) {
    return {
      error: normalizeApiError(error, "Could not evaluate that offer. Try again shortly."),
    };
  }
}

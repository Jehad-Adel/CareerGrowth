"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

import { evaluateOffer } from "./actions";

type OfferResult = {
  company: string;
  roleTitle: string;
  overallScore: number;
  recommendation: string;
  result: Record<string, unknown>;
};

export function OffersBody() {
  const [result, setResult] = useState<OfferResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const form = new FormData(e.currentTarget);
    const res = await evaluateOffer({}, form);
    if (res.error) {
      setError(res.error);
      setLoading(false);
      return;
    }
    if (res.offerId) {
      try {
        const { getOfferEval } = await import("@/lib/services");
        const offer = await getOfferEval(res.offerId);
        setResult({
          company: offer.company,
          roleTitle: offer.role_title,
          overallScore: offer.overall_score ?? 0,
          recommendation: offer.recommendation,
          result: offer.result,
        });
      } catch {
        window.location.reload();
      }
    }
    setLoading(false);
  }

  if (result) {
    const scores = result.result?.scores as Record<string, number> | undefined;
    const pros = result.result?.pros as string[] | undefined;
    const cons = result.result?.cons as string[] | undefined;
    const tips = result.result?.negotiation_tips as string[] | undefined;
    const rationale = result.result?.recommendation_rationale as string | undefined;

    return (
      <div className="rounded-2xl border bg-card p-6 space-y-6">
        <div>
          <h2 className="text-lg font-semibold">{result.roleTitle} @ {result.company}</h2>
          <p className="text-sm text-muted-foreground mt-1 flex items-center gap-2">
            Score: <span className={`text-xl font-bold ${
              result.overallScore >= 7 ? "text-green-600" :
              result.overallScore >= 5 ? "text-amber-600" : "text-red-600"
            }`}>{result.overallScore}/10</span>
            <span className="text-xs capitalize bg-muted px-2 py-0.5 rounded-full">
              {result.recommendation.replace(/_/g, " ")}
            </span>
          </p>
        </div>

        {rationale && (
          <div className="rounded-lg bg-muted/50 p-4">
            <p className="text-sm">{rationale}</p>
          </div>
        )}

        {scores && (
          <div>
            <h3 className="text-sm font-medium mb-3">Scores Breakdown</h3>
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
              {Object.entries(scores).map(([key, val]) => (
                <div key={key} className="rounded-xl border p-3 text-center">
                  <p className="text-xs text-muted-foreground capitalize">{key.replace(/_/g, " ")}</p>
                  <p className="text-xl font-bold">{val}/10</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {pros && pros.length > 0 && (
          <div>
            <h3 className="text-sm font-medium mb-2 text-green-700">Pros</h3>
            <ul className="list-disc pl-5 space-y-1">
              {pros.map((p, i) => <li key={i} className="text-sm">{p}</li>)}
            </ul>
          </div>
        )}

        {cons && cons.length > 0 && (
          <div>
            <h3 className="text-sm font-medium mb-2 text-red-700">Cons</h3>
            <ul className="list-disc pl-5 space-y-1">
              {cons.map((c, i) => <li key={i} className="text-sm">{c}</li>)}
            </ul>
          </div>
        )}

        {tips && tips.length > 0 && (
          <div>
            <h3 className="text-sm font-medium mb-2">Negotiation Tips</h3>
            <ul className="list-disc pl-5 space-y-1">
              {tips.map((t, i) => <li key={i} className="text-sm text-muted-foreground">{t}</li>)}
            </ul>
          </div>
        )}

        <Button variant="outline" onClick={() => setResult(null)} className="w-full">
          Evaluate Another Offer
        </Button>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border bg-card p-6">
      <div className="mb-6">
        <h2 className="text-lg font-semibold">Evaluate a Job Offer</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Paste the offer details for an objective, data-driven evaluation.
        </p>
      </div>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="company">Company</Label>
            <Input id="company" name="company" placeholder="Company name" required />
          </div>
          <div className="space-y-2">
            <Label htmlFor="role_title">Role Title</Label>
            <Input id="role_title" name="role_title" placeholder="e.g. Senior Engineer" required />
          </div>
        </div>
        <div className="space-y-2">
          <Label htmlFor="offer_details">Offer Details</Label>
          <Textarea
            id="offer_details"
            name="offer_details"
            placeholder="Paste the full offer including salary, equity, benefits, work arrangements..."
            rows={10}
            required
            minLength={20}
          />
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <Button type="submit" disabled={loading} className="w-full">
          {loading ? "Evaluating..." : "Evaluate Offer"}
        </Button>
      </form>
    </div>
  );
}

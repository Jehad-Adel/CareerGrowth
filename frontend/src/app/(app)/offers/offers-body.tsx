"use client";

import { AlertCircle, Loader2 } from "lucide-react";
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
    try {
      const res = await evaluateOffer({}, form);
      if (res.error) {
        setError(res.error);
        return;
      }
      if (res.offer) {
        setResult(res.offer);
      }
    } finally {
      setLoading(false);
    }
  }

  if (result) {
    const scores = result.result?.scores as Record<string, number> | undefined;
    const pros = result.result?.pros as string[] | undefined;
    const cons = result.result?.cons as string[] | undefined;
    const tips = result.result?.negotiation_tips as string[] | undefined;
    const rationale = result.result?.recommendation_rationale as string | undefined;

    return (
      <div className="rounded-2xl border bg-card p-4 sm:p-6 space-y-6">
        <div>
          <h2 className="text-lg font-semibold">{result.roleTitle} @ {result.company}</h2>
          <p className="text-sm text-muted-foreground mt-1 flex items-center gap-2">
            Score: <span className={`text-xl font-bold ${
              result.overallScore >= 7 ? "text-sprout" :
              result.overallScore >= 5 ? "text-harvest" : "text-destructive"
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
            <h3 className="text-sm font-medium mb-2 text-sprout">Pros</h3>
            <ul className="list-disc pl-5 space-y-1">
              {pros.map((p, i) => <li key={i} className="text-sm">{p}</li>)}
            </ul>
          </div>
        )}

        {cons && cons.length > 0 && (
          <div>
            <h3 className="text-sm font-medium mb-2 text-destructive">Cons</h3>
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
    <div className="rounded-2xl border bg-card p-4 sm:p-6">
      <div className="mb-6">
        <h2 className="text-lg font-semibold">Evaluate a Job Offer</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Paste the offer details for an objective, data-driven evaluation.
        </p>
      </div>
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Stacked on a phone — two half-width text inputs are unusable
            below ~380px. */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="company">Company</Label>
            <Input id="company" name="company" placeholder="Company name" required aria-required="true" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="role_title">Role Title</Label>
            <Input id="role_title" name="role_title" placeholder="e.g. Senior Engineer" required aria-required="true" />
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
        {error ? (
          <div
            role="alert"
            className="flex items-start gap-2.5 rounded-lg bg-destructive/10 px-3.5 py-2.5 text-xs text-destructive"
          >
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        ) : null}
        <Button type="submit" disabled={loading} aria-busy={loading} className="w-full">
          {loading ? (
            <>
              <Loader2 className="animate-spin" />
              Weighing the offer…
            </>
          ) : (
            "Evaluate Offer"
          )}
        </Button>
      </form>
    </div>
  );
}

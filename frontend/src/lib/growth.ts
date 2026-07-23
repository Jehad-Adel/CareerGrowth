import type { GrowthStage } from "@/types";

/** Map 0–100 skill mastery to a plant growth stage. */
export function masteryToStage(mastery: number): GrowthStage {
  if (mastery >= 80) return "tree";
  if (mastery >= 50) return "growing";
  if (mastery >= 20) return "sprout";
  return "seed";
}

export const stageLabel: Record<GrowthStage, string> = {
  seed: "Seed",
  sprout: "Sprout",
  growing: "Growing",
  tree: "Mastered",
};

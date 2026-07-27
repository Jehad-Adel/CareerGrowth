import type { GrowthStage } from "@/types";

/**
 * Mastery-to-stage mapping lives on the server (`farm_service.stage_for`) and
 * arrives on each plant. It used to be duplicated here with *different*
 * thresholds (80/50/20 vs the server's 75/50/1), so the same skill could
 * render as two different plants depending on which path drew it.
 */
export const stageLabel: Record<GrowthStage, string> = {
  seed: "Seed",
  sprout: "Sprout",
  growing: "Growing",
  tree: "Mastered",
};

// Shared UI types.
//
// Wire shapes live next to the function that fetches them in lib/services.ts.
// Only what more than one module needs belongs here.

/** Mastery bucket a skill renders as on the farm. Computed server-side. */
export type GrowthStage = "seed" | "sprout" | "growing" | "tree";

/** The viewer, shaped for display — the topbar and page greetings read this. */
export interface Profile {
  name: string;
  headline: string;
  targetRole: string;
  hasCv: boolean;
  level: number;
  levelTitle: string;
  xp: number;
  xpForNext: number;
  streakDays: number;
}

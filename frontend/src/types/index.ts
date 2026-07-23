// Domain types — mirror the planned backend Career Profile model.
// The mock service returns these shapes so pages swap to the real API unchanged.

export type GrowthStage = "seed" | "sprout" | "growing" | "tree";

export type SkillCategory =
  | "Languages"
  | "Frontend"
  | "Backend"
  | "Data"
  | "DevOps"
  | "Foundations";

export interface Skill {
  id: string;
  name: string;
  category: SkillCategory;
  /** 0–100 mastery. Drives the plant's growth stage. */
  mastery: number;
  source: "cv" | "manual" | "roadmap";
}

export interface Goal {
  id: string;
  title: string;
  status: "active" | "done";
  /** 0–100 */
  progress: number;
  due?: string;
}

export type GrowthEventType =
  | "skill_discovered"
  | "skill_leveled"
  | "goal_completed"
  | "cert_added"
  | "cv_analyzed";

export interface GrowthEvent {
  id: string;
  type: GrowthEventType;
  label: string;
  at: string; // ISO date
  xp: number;
}

export interface Profile {
  name: string;
  headline: string;
  targetRole: string;
  level: number;
  levelTitle: string;
  xp: number;
  xpForNext: number;
  streakDays: number;
}

export interface CvSection {
  name: string;
  score: number; // 0–100
  note: string;
}

export interface CvAnalysis {
  overall: number; // 0–100
  atsScore: number; // 0–100
  sections: CvSection[];
  strengths: string[];
  missing: string[];
  suggestions: string[];
}

export interface JobMatch {
  title: string;
  company: string;
  fit: number; // 0–100
  matched: string[];
  gaps: string[];
  actions: string[];
}

export interface InterviewQuestion {
  id: string;
  kind: "technical" | "behavioral";
  prompt: string;
  tip: string;
}

export interface RoadmapStep {
  id: string;
  order: number;
  title: string;
  detail: string;
  status: "done" | "current" | "todo";
  skills: string[];
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
}

export interface DashboardData {
  profile: Profile;
  skills: Skill[];
  goals: Goal[];
  events: GrowthEvent[];
  recommended: { id: string; title: string; href: string; cta: string }[];
}

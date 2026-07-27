// Data access for the app.
//
// Each function maps 1:1 to a backend endpoint. Live functions call
// `serverFetch`; the rest still return mock data and are labelled with the
// phase that replaces them. Pages never import serverFetch directly, so
// going live stays a change here and nowhere else.

import { serverFetch } from "@/lib/api/server";
import * as mock from "@/lib/mock/data";
import type { ChatMessage, InterviewQuestion, Profile } from "@/types";

/** Simulate network latency so loading states are real. Remove when live. */
const wait = <T>(value: T, ms = 0): Promise<T> =>
  new Promise((resolve) => setTimeout(() => resolve(value), ms));

/** Wire shape of GET /profile — snake_case, straight from FastAPI. */
type ApiProfile = {
  id: string;
  email: string | null;
  full_name: string | null;
  current_role: string | null;
  target_role: string | null;
  seniority_level: string | null;
  summary: string | null;
  has_cv: boolean;
  level: number;
  level_title: string;
  xp: number;
  xp_for_next: number;
  streak_days: number;
  created_at: string;
};

/** A new profile has almost nothing on it. Give the UI something to render. */
function toProfile(api: ApiProfile): Profile {
  return {
    name: api.full_name?.trim() || api.email?.split("@")[0] || "Farmer",
    headline: api.current_role?.trim() || "Just getting started",
    targetRole: api.target_role?.trim() || "Not set yet",
    level: api.level,
    levelTitle: api.level_title,
    xp: api.xp,
    xpForNext: api.xp_for_next,
    streakDays: api.streak_days,
  };
}

// --- Live ---

export const getProfile = async (): Promise<Profile> =>
  toProfile(await serverFetch<ApiProfile>("/profile"));

// --- Mock until their phase lands ---
//
// Only two remain. The rest were superseded by live endpoints in phases 3-5
// and deleted rather than left around, so nothing can accidentally render
// invented data next to real data.

/** Phase 6. */
export const getInterviewQuestions = (): Promise<InterviewQuestion[]> =>
  wait(mock.interviewQuestions);

/** Phase 7. */
export const getChatHistory = (): Promise<ChatMessage[]> => wait(mock.chatHistory);

// --- CV Studio (Phase 3, live) ---

export type CvProfileResult = {
  full_name: string | null;
  current_role: string | null;
  years_of_experience: number | null;
  seniority_level: string;
  skills: string[];
  strengths: string[];
  weaknesses: string[];
  summary: string;
  improvement_suggestions: string[];
};

export type CvAnalysisRecord = {
  id: string;
  created_at: string;
  skills_found: number;
  result: CvProfileResult;
};

export type CvStatus = {
  has_cv: boolean;
  analyses_today: number;
  daily_limit: number;
};

export const getCvStatus = (): Promise<CvStatus> =>
  serverFetch<CvStatus>("/cv/status");

export const getLatestCvAnalysis = (): Promise<CvAnalysisRecord | null> =>
  serverFetch<CvAnalysisRecord | null>("/cv/latest");

// --- Job Match / Skill Gap / Resume Optimizer (Phase 4, live) ---

export type AnalysisRecord<T> = {
  id: string;
  created_at: string;
  job_title: string | null;
  result: T;
};

export type JobMatchResult = {
  match_score: number;
  matched_skills: string[];
  missing_skills: string[];
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
  summary: string;
};

export type SkillGapItemResult = {
  skill: string;
  priority: "Critical" | "High" | "Medium" | "Low";
  importance_reason: string;
  current_level: "None" | "Beginner" | "Intermediate" | "Advanced";
  estimated_learning_time: string;
  prerequisite_skills: string[];
  recommended_resources: string[];
  project_to_practice: string;
  mandatory: boolean;
};

export type SkillGapResult = {
  overall_gap_score: number;
  strongest_area: string;
  weakest_area: string;
  gap_summary: string;
  missing_skills: SkillGapItemResult[];
};

export type ResumeResult = {
  ats_score_before: number;
  ats_score_after: number;
  summary_of_changes: string[];
  missing_information: string[];
  optimized_sections: { title: string; content: string[] }[];
  final_resume_text: string;
};

export const getLatestJobMatch = (): Promise<AnalysisRecord<JobMatchResult> | null> =>
  serverFetch<AnalysisRecord<JobMatchResult> | null>("/jobs/latest");

export const getLatestSkillGap = (): Promise<AnalysisRecord<SkillGapResult> | null> =>
  serverFetch<AnalysisRecord<SkillGapResult> | null>("/skills/gap/latest");

export const getLatestResume = (): Promise<AnalysisRecord<ResumeResult> | null> =>
  serverFetch<AnalysisRecord<ResumeResult> | null>("/cv/optimize/latest");

// --- Roadmap + Farm + Dashboard (Phase 5, live) ---

export type FarmPlant = {
  id: string;
  name: string;
  category: string | null;
  mastery: number;
  source: string;
  stage: import("@/types").GrowthStage;
};

export type FarmFeedItem = {
  id: number;
  type: string;
  payload: Record<string, unknown>;
  xp: number;
  at: string;
};

export type Farm = {
  level: number;
  level_title: string;
  xp: number;
  xp_for_next: number;
  streak_days: number;
  plants: FarmPlant[];
  counts: { total: number; seeds: number; trees: number };
  roadmap: {
    has_roadmap: boolean;
    target_role: string | null;
    done: number;
    total: number;
  };
  feed: FarmFeedItem[];
};

export type RoadmapStepRecord = {
  id: string;
  position: number;
  title: string;
  description: string;
  skills_to_acquire: string[];
  prerequisite_skills: string[];
  estimated_months: number;
  status: "todo" | "done";
};

export type RoadmapRecord = {
  id: string;
  created_at: string;
  target_role: string;
  summary: string;
  total_estimated_months: number;
  steps: RoadmapStepRecord[];
};

export type Dashboard = {
  profile: Record<string, unknown> & {
    full_name: string | null;
    email: string | null;
    target_role: string | null;
    level: number;
    level_title: string;
    xp: number;
    xp_for_next: number;
    streak_days: number;
  };
  farm: Farm;
  usage: Record<string, number>;
  has_cv: boolean;
};

export const getFarmData = (): Promise<Farm> => serverFetch<Farm>("/farm");

export const getRoadmapData = (): Promise<RoadmapRecord | null> =>
  serverFetch<RoadmapRecord | null>("/roadmap");

/** One round trip. Five separate calls would each pay for auth and a JWKS check. */
export const getDashboardData = (): Promise<Dashboard> =>
  serverFetch<Dashboard>("/dashboard");

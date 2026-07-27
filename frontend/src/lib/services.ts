// Data access for the app.
//
// Each function maps 1:1 to a backend endpoint. Pages never import
// serverFetch directly, so a change of endpoint stays a change here and
// nowhere else.

import { cache } from "react";

import { serverFetch } from "@/lib/api/server";
import type { Profile } from "@/types";

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
    hasCv: api.has_cv,
    level: api.level,
    levelTitle: api.level_title,
    xp: api.xp,
    xpForNext: api.xp_for_next,
    streakDays: api.streak_days,
  };
}

// --- Profile ---

/**
 * `cache()` because the app layout renders this on every page while pages read
 * it too — one request, one round trip, not two.
 */
export const getProfile = cache(
  async (): Promise<Profile> => toProfile(await serverFetch<ApiProfile>("/profile")),
);

// --- CV Studio ---

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

/**
 * Only the CV Studio needs this — every other page answers "has a CV?" from
 * the profile it already has. Cached anyway; the page reads it beside a
 * parallel analysis fetch.
 */
export const getCvStatus = cache(
  (): Promise<CvStatus> => serverFetch<CvStatus>("/cv/status"),
);

export const getLatestCvAnalysis = (): Promise<CvAnalysisRecord | null> =>
  serverFetch<CvAnalysisRecord | null>("/cv/latest");

// --- Job Match / Skill Gap / Resume Optimizer ---

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

export const getLatestJobMatch = (): Promise<AnalysisRecord<JobMatchResult> | null> =>
  serverFetch<AnalysisRecord<JobMatchResult> | null>("/jobs/latest");

export const getLatestSkillGap = (): Promise<AnalysisRecord<SkillGapResult> | null> =>
  serverFetch<AnalysisRecord<SkillGapResult> | null>("/skills/gap/latest");

// --- Roadmap + Farm + Dashboard ---

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

// --- Interview Coach ---

export type InterviewLevel =
  | "friendly_hr"
  | "technical_lead"
  | "stress_interview";

export type InterviewFeedback = {
  strengths: string[];
  weaknesses: string[];
  missing_concepts: string[];
  confidence_level: number;
  technical_accuracy: number;
  communication_score: number;
};

export type InterviewFinal = {
  overall_score: number;
  technical_skills: number;
  communication: number;
  confidence: number;
  problem_solving: number;
  weak_areas: string[];
  strong_areas: string[];
  hiring_recommendation: string;
  summary: string;
};

export type InterviewTurnRecord = {
  id: string;
  position: number;
  question: string;
  difficulty: string | null;
  expected_topics: string[];
  answer: string | null;
  feedback: InterviewFeedback | null;
  score: number | null;
};

export type InterviewSessionRecord = {
  id: string;
  created_at: string;
  level: InterviewLevel;
  interviewer_name: string | null;
  finished: boolean;
  final_evaluation: InterviewFinal | null;
  turns: InterviewTurnRecord[];
};

export const getLatestInterview = (): Promise<InterviewSessionRecord | null> =>
  serverFetch<InterviewSessionRecord | null>("/interview/latest");

// --- Career Chat ---

export type ChatMessageRecord = {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources: { kind: string; chunk: number }[] | null;
  created_at: string;
};

export type ChatState = {
  messages: ChatMessageRecord[];
  corpus_chunks: number;
  messages_today: number;
  daily_limit: number;
};

export const getChatState = (): Promise<ChatState> =>
  serverFetch<ChatState>("/chat");

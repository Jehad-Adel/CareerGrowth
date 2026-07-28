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

export type EmploymentPeriod = {
  title: string | null;
  company: string | null;
  start_date: string | null;
  end_date: string | null;
  is_current: boolean;
};

/**
 * Fields added on 2026-07-28 are optional here, not because the API omits
 * them but because `result` is stored verbatim: a row written before they
 * existed still renders, and typing them as required would be a lie the
 * compiler cannot catch.
 */
export type CvProfileResult = {
  full_name: string | null;
  current_role: string | null;
  years_of_experience: number | null;
  employment_periods?: EmploymentPeriod[];
  seniority_level: string;
  skills: string[];
  strengths: string[];
  weaknesses: string[];
  summary: string;
  improvement_suggestions: string[];
  extraction_confidence?: number;
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

export type SkillMatchResult = {
  job_skill: string;
  requirement_level: "Required" | "Preferred";
  matched: boolean;
  matched_via: string | null;
  is_transferable_match: boolean;
  severity_if_missing: "Blocking" | "Significant" | "Minor" | null;
};

export type JobMatchResult = {
  match_score: number;
  /** A screen-pass estimate, deliberately not the same number as the score. */
  hiring_probability?: number;
  hiring_probability_reasoning?: string;
  skill_matches?: SkillMatchResult[];
  /** Derived from skill_matches server-side, so present on every row, old or new. */
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
  /** Why this step, here, for this person. Empty string on older roadmaps. */
  reason: string;
  difficulty: "Beginner" | "Intermediate" | "Advanced";
  skills_to_acquire: string[];
  prerequisite_skills: string[];
  /** Resource names, never URLs — the model cannot be trusted with links. */
  recommended_resources: string[];
  project_to_practice: string;
  estimated_months: number;
  /** Zero when the generation did not estimate it. */
  estimated_weekly_hours: number;
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

export const getRoadmapHistory = (): Promise<RoadmapRecord[]> =>
  serverFetch<RoadmapRecord[]>("/roadmap/history");

export const getRoadmapById = (id: string): Promise<RoadmapRecord | null> =>
  serverFetch<RoadmapRecord | null>(`/roadmap/${id}`);

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

export const getInterviewSessions = (): Promise<InterviewSessionRecord[]> =>
  serverFetch<InterviewSessionRecord[]>("/interview/sessions");

export const getInterviewSession = (
  id: string,
): Promise<InterviewSessionRecord | null> =>
  serverFetch<InterviewSessionRecord | null>(`/interview/sessions/${id}`);

// --- Career Chat ---

/**
 * What grounded an assistant reply.
 *
 * Everything past `kind` is optional because these rows are stored verbatim:
 * messages written before curated guidance was attributed carry only
 * `{kind, chunk}`, and still have to render.
 */
export type ChatSource = {
  /** "document" is the person's own material; "guide" is CareerFarm's. */
  origin?: "document" | "guide";
  kind: string;
  /** Display name. Falls back to `kind` on older rows. */
  label?: string;
  chunk?: number;
  title?: string;
};

export type ChatMessageRecord = {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources: ChatSource[] | null;
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

// --- Cover letter ---

export type CoverLetterResult = {
  greeting: string;
  opening: string;
  body: string[];
  closing: string;
  sign_off: string;
  tone: "Formal" | "Conversational" | "Enthusiastic";
  /** The CV facts the letter leans on, so the candidate can check them. */
  evidence_used: string[];
  word_count_note: string;
  /** Assembled server-side so copy, download and any future PDF agree. */
  full_text: string;
};

export const getLatestCoverLetter = (): Promise<
  AnalysisRecord<CoverLetterResult> | null
> =>
  serverFetch<AnalysisRecord<CoverLetterResult> | null>(
    "/jobs/cover-letter/latest",
  );

// --- Application tracker ---

export type ApplicationStatus =
  | "saved"
  | "applied"
  | "interviewing"
  | "offer"
  | "rejected";

export type ApplicationRecord = {
  id: string;
  company: string;
  role: string;
  status: ApplicationStatus;
  job_match_id: string | null;
  applied_at: string | null;
  url: string;
  notes: string;
  created_at: string;
};

export type ApplicationBoard = {
  /** Pipeline order, defined server-side so both ends cannot disagree. */
  statuses: ApplicationStatus[];
  counts: Record<ApplicationStatus, number>;
  applications: ApplicationRecord[];
};

/** The whole board in one call — every column renders at once. */
export const getApplications = (): Promise<ApplicationBoard> =>
  serverFetch<ApplicationBoard>("/applications");

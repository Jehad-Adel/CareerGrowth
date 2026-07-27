// Data access for the app.
//
// Each function maps 1:1 to a backend endpoint. Live functions call
// `serverFetch`; the rest still return mock data and are labelled with the
// phase that replaces them. Pages never import serverFetch directly, so
// going live stays a change here and nowhere else.

import { serverFetch } from "@/lib/api/server";
import * as mock from "@/lib/mock/data";
import type {
  ChatMessage,
  CvAnalysis,
  DashboardData,
  InterviewQuestion,
  JobMatch,
  Profile,
  RoadmapStep,
  Skill,
} from "@/types";

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

/** Phase 5. */
export const getDashboard = (): Promise<DashboardData> =>
  wait({
    profile: mock.profile,
    skills: mock.skills,
    goals: mock.goals,
    events: mock.events,
    recommended: mock.recommended,
  });

/** Phase 5. */
export const getSkills = (): Promise<Skill[]> => wait(mock.skills);

/** Phase 5. */
export const getFarm = (): Promise<{ skills: Skill[]; goals: typeof mock.goals }> =>
  wait({ skills: mock.skills, goals: mock.goals });

/** Phase 3. */
export const getCvAnalysis = (): Promise<CvAnalysis> => wait(mock.cvAnalysis);

/** Phase 4. */
export const getJobMatch = (): Promise<JobMatch> => wait(mock.jobMatch);

/** Phase 6. */
export const getInterviewQuestions = (): Promise<InterviewQuestion[]> =>
  wait(mock.interviewQuestions);

/** Phase 5. */
export const getRoadmap = (): Promise<RoadmapStep[]> => wait(mock.roadmap);

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

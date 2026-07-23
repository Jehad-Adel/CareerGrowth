// Data access for the app. Currently returns mock data so the UI is fully
// static. Each function maps 1:1 to a future backend endpoint — to go live,
// replace the mock return with the matching `apiFetch<T>(path)` call and keep
// the signature identical. Pages never change.
//
// Example (later):
//   export const getDashboard = () => apiFetch<DashboardData>("/dashboard");

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

export const getProfile = (): Promise<Profile> => wait(mock.profile);

export const getDashboard = (): Promise<DashboardData> =>
  wait({
    profile: mock.profile,
    skills: mock.skills,
    goals: mock.goals,
    events: mock.events,
    recommended: mock.recommended,
  });

export const getSkills = (): Promise<Skill[]> => wait(mock.skills);

export const getFarm = (): Promise<{ skills: Skill[]; goals: typeof mock.goals }> =>
  wait({ skills: mock.skills, goals: mock.goals });

export const getCvAnalysis = (): Promise<CvAnalysis> => wait(mock.cvAnalysis);

export const getJobMatch = (): Promise<JobMatch> => wait(mock.jobMatch);

export const getInterviewQuestions = (): Promise<InterviewQuestion[]> =>
  wait(mock.interviewQuestions);

export const getRoadmap = (): Promise<RoadmapStep[]> => wait(mock.roadmap);

export const getChatHistory = (): Promise<ChatMessage[]> => wait(mock.chatHistory);

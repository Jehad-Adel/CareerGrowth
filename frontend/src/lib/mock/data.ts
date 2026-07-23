import type {
  CvAnalysis,
  ChatMessage,
  Goal,
  GrowthEvent,
  InterviewQuestion,
  JobMatch,
  Profile,
  RoadmapStep,
  Skill,
} from "@/types";

export const profile: Profile = {
  name: "Nour Hassan",
  headline: "Computer Science graduate · aspiring backend engineer",
  targetRole: "Backend Engineer",
  level: 5,
  levelTitle: "Cultivator",
  xp: 420,
  xpForNext: 500,
  streakDays: 12,
};

export const skills: Skill[] = [
  { id: "s1", name: "Python", category: "Languages", mastery: 88, source: "cv" },
  { id: "s2", name: "SQL", category: "Data", mastery: 72, source: "cv" },
  { id: "s3", name: "FastAPI", category: "Backend", mastery: 61, source: "roadmap" },
  { id: "s4", name: "Git", category: "Foundations", mastery: 80, source: "cv" },
  { id: "s5", name: "React", category: "Frontend", mastery: 45, source: "manual" },
  { id: "s6", name: "Docker", category: "DevOps", mastery: 30, source: "roadmap" },
  { id: "s7", name: "PostgreSQL", category: "Data", mastery: 52, source: "roadmap" },
  { id: "s8", name: "REST APIs", category: "Backend", mastery: 66, source: "cv" },
  { id: "s9", name: "Testing", category: "Foundations", mastery: 24, source: "roadmap" },
  { id: "s10", name: "TypeScript", category: "Languages", mastery: 15, source: "manual" },
  { id: "s11", name: "Linux", category: "DevOps", mastery: 40, source: "cv" },
  { id: "s12", name: "System Design", category: "Backend", mastery: 8, source: "roadmap" },
];

export const goals: Goal[] = [
  { id: "g1", title: "Ship a REST API with tests", status: "active", progress: 65, due: "Aug 2026" },
  { id: "g2", title: "Learn Docker fundamentals", status: "active", progress: 30, due: "Sep 2026" },
  { id: "g3", title: "Complete SQL joins module", status: "done", progress: 100 },
  { id: "g4", title: "Rewrite CV with metrics", status: "active", progress: 40, due: "Aug 2026" },
];

export const events: GrowthEvent[] = [
  { id: "e1", type: "goal_completed", label: "Completed “SQL joins module”", at: "2026-07-21", xp: 40 },
  { id: "e2", type: "skill_leveled", label: "FastAPI grew to 61%", at: "2026-07-20", xp: 25 },
  { id: "e3", type: "cv_analyzed", label: "CV analyzed — score 74", at: "2026-07-18", xp: 15 },
  { id: "e4", type: "skill_discovered", label: "Discovered “REST APIs” from CV", at: "2026-07-18", xp: 10 },
  { id: "e5", type: "cert_added", label: "Added “Python for Everybody” cert", at: "2026-07-15", xp: 30 },
];

export const recommended = [
  { id: "r1", title: "Close your Docker gap", href: "/roadmap", cta: "Open roadmap" },
  { id: "r2", title: "Analyze your latest CV", href: "/cv", cta: "Open CV Studio" },
  { id: "r3", title: "Practice 3 system-design questions", href: "/interview", cta: "Start practice" },
];

export const cvAnalysis: CvAnalysis = {
  overall: 74,
  atsScore: 68,
  sections: [
    { name: "Contact & links", score: 92, note: "Clear. Add a GitHub link." },
    { name: "Summary", score: 61, note: "Too generic — lead with your target role." },
    { name: "Experience", score: 70, note: "Add measurable outcomes (numbers, impact)." },
    { name: "Skills", score: 80, note: "Good coverage; group by category." },
    { name: "Education", score: 88, note: "Solid. Include relevant coursework." },
  ],
  strengths: [
    "Strong Python and data fundamentals",
    "Clear, readable one-page structure",
    "Relevant coursework listed",
  ],
  missing: [
    "Quantified impact in experience bullets",
    "A link to a portfolio or GitHub",
    "A tailored summary for backend roles",
  ],
  suggestions: [
    "Rewrite each experience bullet as: action → tool → measurable result.",
    "Add a 2-line summary naming “Backend Engineer” as your target.",
    "Move a Projects section above Education to show applied skills.",
  ],
};

export const jobMatch: JobMatch = {
  title: "Junior Backend Engineer",
  company: "Northwind Labs",
  fit: 71,
  matched: ["Python", "REST APIs", "SQL", "Git"],
  gaps: ["Docker", "CI/CD", "System design basics"],
  actions: [
    "Build one containerized service and push it to a registry.",
    "Add a GitHub Actions workflow to an existing project.",
    "Read a system-design primer and sketch one architecture.",
  ],
};

export const interviewQuestions: InterviewQuestion[] = [
  {
    id: "q1",
    kind: "technical",
    prompt: "Explain the difference between a SQL JOIN and a subquery. When would you pick each?",
    tip: "Name a concrete case where a JOIN is clearer than a correlated subquery.",
  },
  {
    id: "q2",
    kind: "technical",
    prompt: "How would you design a rate limiter for a public API?",
    tip: "Mention token bucket vs. fixed window and where you'd store counters.",
  },
  {
    id: "q3",
    kind: "behavioral",
    prompt: "Tell me about a project where something broke. What did you do?",
    tip: "Use STAR: Situation, Task, Action, Result — end with what you changed.",
  },
  {
    id: "q4",
    kind: "behavioral",
    prompt: "How do you decide what to learn next when everything feels important?",
    tip: "Tie it to a goal or target role, not just curiosity.",
  },
];

export const roadmap: RoadmapStep[] = [
  {
    id: "rs1",
    order: 1,
    title: "Solidify Python + Git",
    detail: "Comfortable with modules, virtualenvs, branching, and PRs.",
    status: "done",
    skills: ["Python", "Git"],
  },
  {
    id: "rs2",
    order: 2,
    title: "Databases & SQL",
    detail: "Model data, write joins, understand indexes and transactions.",
    status: "done",
    skills: ["SQL", "PostgreSQL"],
  },
  {
    id: "rs3",
    order: 3,
    title: "Build REST APIs with FastAPI",
    detail: "Routing, validation, auth, and tests for a real service.",
    status: "current",
    skills: ["FastAPI", "REST APIs", "Testing"],
  },
  {
    id: "rs4",
    order: 4,
    title: "Containers & deployment",
    detail: "Dockerize a service, run it locally, deploy to a platform.",
    status: "todo",
    skills: ["Docker", "Linux"],
  },
  {
    id: "rs5",
    order: 5,
    title: "System design foundations",
    detail: "Caching, queues, scaling, and trade-off thinking.",
    status: "todo",
    skills: ["System Design"],
  },
];

export const chatHistory: ChatMessage[] = [
  {
    id: "m1",
    role: "assistant",
    content:
      "Hi Nour — I can see your profile. You're 65% through “Ship a REST API with tests.” Want help with the testing part, or something else?",
  },
  {
    id: "m2",
    role: "user",
    content: "What should I learn next to be ready for backend roles?",
  },
  {
    id: "m3",
    role: "assistant",
    content:
      "Your biggest gap for the Junior Backend Engineer role is Docker and deployment. Finish your current FastAPI step, then containerize it — that single project closes two gaps at once.",
  },
];

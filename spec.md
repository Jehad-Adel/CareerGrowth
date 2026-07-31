# CareerGrowth — v2.0 Feature Update Specification

> **Date:** 2026-07-31  
> **This document covers only the 8 features added in v2.0.**  
> For the full project specification, see the codebase and `UPDATE_IMPACT_REPORT.md`.

---

## Table of Contents

1. [Enhanced Granular Roadmaps](#1-enhanced-granular-roadmaps)
2. [Dynamic Quiz Engine](#2-dynamic-quiz-engine)
3. [Video Summarizer / Transcript Tool](#3-video-summarizer--transcript-tool)
4. [Expanded Streak & XP System](#4-expanded-streak--xp-system)
5. [Speech-to-Text for Virtual Interviews](#5-speech-to-text-for-virtual-interviews)
6. [Application Tracking & Smart Notifications](#6-application-tracking--smart-notifications)
7. [Dedicated Job Offer Evaluator Assistant](#7-dedicated-job-offer-evaluator-assistant)
8. [Hybrid RAG Integration](#8-hybrid-rag-integration)

---

## 1. Enhanced Granular Roadmaps

### Schema Changes

**`roadmap_steps` table — 2 new columns:**

| Column | Type | Default | Description |
|--------|------|---------|-------------|
| `micro_points` | JSONB | `[]` | Array of `{title: str, description: str}` objects. 3-7 granular actionable sub-steps per roadmap step. |
| `learning_resources` | JSONB | `[]` | Array of `{title: str, url: str \| null, type: ResourceType}` objects. 2-6 curated resources per step. |

### AI Changes

**`app/ai/schemas/roadmap_schema.py` — new models:**

```python
class ResourceType = Literal["tutorial", "documentation", "course", "video", "book"]

class ResourceLink(BaseModel):
    title: str
    url: str | None = None        # Only if highly confident
    type: ResourceType

class MicroPoint(BaseModel):
    title: str
    description: str

class RoadmapStep(BaseModel):
    # ... existing fields ...
    micro_points: list[MicroPoint] = Field(default_factory=list, min_length=3, max_length=7)
    learning_resources: list[ResourceLink] = Field(default_factory=list, max_length=6)
```

**Prompt update:** `roadmap_prompt.py` now instructs the model to always include micro-points ("Monday morning actions") and curated learning resources with title/type/optional URL.

### Service Changes

**`roadmap_service.py`:**
- Persists `micro_points` and `learning_resources` from chain output onto `RoadmapStep`
- RAG ingest text now includes micro-point titles

### API

No new endpoints. The existing `POST /roadmap`, `GET /roadmap`, etc. return the new fields in `RoadmapStep` data.

---

## 2. Dynamic Quiz Engine

### New Tables

**`quiz_attempts`:**

| Column | Type | Description |
|--------|------|-------------|
| id | UUID PK | |
| profile_id | UUID FK → career_profiles | Owner |
| source_type | VARCHAR(40) | `roadmap_step`, `document`, `video`, `manual` |
| source_id | UUID | Optional reference |
| source_title | VARCHAR(300) | Display title |
| mastery_level | INT | 1 (beginner) – 5 (expert) |
| score | FLOAT | Percentage correct (set on submit) |
| total_questions | INT | |
| correct_count | INT | |
| completed_at | TIMESTAMPTZ | Set on submit |
| created_at | TIMESTAMPTZ | |

**`quiz_questions`:**

| Column | Type | Description |
|--------|------|-------------|
| id | UUID PK | |
| attempt_id | UUID FK → quiz_attempts | Parent |
| position | INT | Index |
| question | TEXT | |
| options | JSONB | 4 answer strings |
| correct_answer | INT | Index 0-3 (hidden until after submission) |
| user_answer | INT | Set on submit |
| is_correct | BOOLEAN | Set on submit |
| explanation | TEXT | |

### AI Components

**Schema** (`app/ai/schemas/quiz_schema.py`):
- `QuizQuestion`: question, options[4], correct_answer, explanation
- `QuizResponse`: questions list, overall_context

**Chain** (`app/ai/chains/quiz_chain.py`):
- Takes `source_text`, `mastery_level`, `num_questions`
- Returns `QuizResponse` (structured)

**Prompt** (`app/ai/prompts/quiz_prompt.py`):
- Generates questions tailored to source text and mastery level
- Mastery level 1 = basic recall, 3 = application, 5 = evaluation/synthesis
- Rules: 4 options, plausible distractors, no questions outside source text

### Service

**`quiz_service.py`:**
- `generate()`: quota check → chain invoke → persist attempt + questions → return
- `submit_answers()`: compare user answers → calculate score → award XP (30) → mark completed
- `history()`, `get_attempt()`: standard profile-scoped reads

### API

| Method | Path | Description | Rate Limit |
|--------|------|-------------|------------|
| POST | `/quiz/generate` | Generate N questions from source text | 10/min |
| POST | `/quiz/attempts/{id}/submit` | Submit answers, get score + feedback | — |
| GET | `/quiz/history` | List past attempts | — |
| GET | `/quiz/attempts/{id}` | Specific attempt (correct answers revealed) | — |

### RAG Integration

Quiz questions + explanations are ingested into the personal document corpus for future retrieval.

---

## 3. Video Summarizer / Transcript Tool

### New Table

**`video_summaries`:**

| Column | Type | Description |
|--------|------|-------------|
| id | UUID PK | |
| profile_id | UUID FK → career_profiles | Owner |
| url | VARCHAR(2000) | Video URL |
| title | VARCHAR(500) | Extracted title |
| source_type | VARCHAR(20) | `youtube`, `vimeo`, `other` |
| mode | VARCHAR(20) | `summary` or `transcript` |
| transcript | TEXT | Full transcript |
| summary | TEXT | AI-generated summary |
| key_takeaways | JSONB | Array of bullet-point strings |

### AI Components

**Schema** (`app/ai/schemas/video_schema.py`):
- `VideoSummaryResult`: title, summary, summary_points[], key_takeaways[]

**Chain** (`app/ai/chains/video_summary_chain.py`):
- Takes `transcript` → returns structured `VideoSummaryResult`

**Prompt** (`app/ai/prompts/video_summary_prompt.py`):
- Concise but comprehensive summary extraction

### Service

**`video_service.py`:**
- `_extract_youtube_id()`: regex-based YouTube URL parsing (watch, short, embed, youtu.be)
- `_detect_source()`: classify URL as youtube/vimeo/other
- `_fetch_transcript()`: uses `youtube-transcript-api` to fetch YouTube transcripts
- `process()`: 
  - `mode=transcript`: fetch + store transcript only, award 5 XP
  - `mode=summary`: fetch transcript → quota check → chain invoke → store + award 15 XP + RAG ingest

### API

| Method | Path | Description | Rate Limit |
|--------|------|-------------|------------|
| POST | `/video/process` | Fetch transcript + optionally summarize | 10/min |
| GET | `/video/history` | List processed videos | — |
| GET | `/video/{id}` | Specific video summary | — |

### Dependency

`uv add youtube-transcript-api`

---

## 4. Expanded Streak & XP System

### New XP Awards

| Event Type | XP | Description |
|-----------|-----|-------------|
| `quiz_completed` | 30 | Finished a quiz attempt |
| `video_summarized` | 15 | Video summarized |
| `video_transcribed` | 5 | Transcript only |
| `applied_job` | 25 | Changed status to "applied" |
| `cv_optimized` | 20 | Resume optimized |
| `offer_evaluated` | 35 | Job offer evaluated |
| `daily_login` | 5 | Streak maintenance (implicit) |

Updated in `xp_service.py` `XP_AWARDS` dict.

### Streak System

**New file:** `app/services/streak_service.py`

**Function:** `record_activity(db, profile_id)`
- If `last_active_on == yesterday`: increment `streak_days`
- If `last_active_on == today`: no change (idempotent)
- If older or null: reset `streak_days = 1`
- Sets `last_active_on = today`

**Integration:** Auto-called inside `xp_service.record_event()` — any XP-earning engagement updates the streak automatically. No manual calls needed.

**Function:** `get_streak_info(db, profile_id)` → `{streak_days, last_active_on}`

### New Event Types

Updated `GrowthEvent.type` docstring to include all 14 event types.

### Impact

- `streak_days` and `last_active_on` columns already existed on `career_profiles` — no migration needed for fields
- Streak now actually works (previously fields were never written to)

---

## 5. Speech-to-Text for Virtual Interviews

### New File

**`app/services/audio_service.py`:**

Uses Google Gemini's multimodal capability (no separate STT API key needed):

```python
def transcribe_audio(audio_data: bytes, mime_type: str = "audio/webm") -> str:
    # Sends audio to Gemini as multimodal content
    # Returns transcribed text
```

### Updated Service

**`interview_service.py` — `answer()` function updated:**

```python
def answer(
    db, profile_id, session_id,
    text: str | None = None,
    audio_data: bytes | None = None,
) -> InterviewSession:
```

- If `audio_data` provided without `text`: transcribe via Gemini, use transcription as answer
- If `text` provided: use as before
- Error handling: if STT fails, returns 502 with message to try typing

### Updated API

**`POST /interview/sessions/{id}/answer`** now accepts `multipart/form-data`:

| Field | Type | Description |
|-------|------|-------------|
| `answer` | Form field (str) | Text answer (optional if audio provided) |
| `audio` | File upload | Audio blob (optional if text provided) |

The route is now `async def` because of `await audio.read()`.

### No Schema Changes

Audio is transcribed to text and stored as text in `InterviewTurn.answer`. Audio data is never persisted.

---

## 6. Application Tracking & Smart Notifications

### Schema Changes

**`job_applications` — 4 new columns:**

| Column | Type | Default | Description |
|--------|------|---------|-------------|
| `deadline_at` | DATE | null | Application deadline |
| `next_step` | VARCHAR(300) | `''` | Next action to take |
| `next_step_date` | DATE | null | When to do next step |
| `notified_deadline` | BOOLEAN | `false` | Whether deadline notification sent |

**New table — `notifications`:**

| Column | Type | Description |
|--------|------|-------------|
| id | UUID PK | |
| profile_id | UUID FK → career_profiles | Owner |
| type | VARCHAR(40) | `deadline_approaching`, `status_update`, `streak_reminder`, `custom` |
| title | VARCHAR(300) | |
| body | TEXT | |
| data | JSONB | Optional payload |
| read | BOOLEAN | Default `false` |

Index: `(profile_id, read)` for efficient unread queries.

### Service Changes

**`application_service.py`:**
- `create()` now accepts `deadline_at`, `next_step`, `next_step_date`
- `update()` now accepts `deadline_at`, `next_step`, `next_step_date`
- `create()` awards 25 XP when status is `"applied"` via `xp_service.record_event()`
- New import: `from app.services import xp_service`

**New file — `notification_service.py`:**
- `create()`: Insert notification row
- `list_unread()`: Profile-scoped unread list (newest first)
- `list_all()`: All notifications
- `mark_read()`: Set `read=true` by id + profile_id
- `mark_all_read()`: Set all unread for profile to true
- `count_unread()`: COUNT query
- `check_deadlines()`: Finds applications with `deadline_at` within 3 days where `notified_deadline=false`, creates notifications, marks applications

### API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/notifications` | Unread list + auto-checks deadlines |
| GET | `/notifications/all` | All notifications |
| POST | `/notifications/{id}/read` | Mark one read |
| POST | `/notifications/read-all` | Mark all read |
| GET | `/notifications/count` | Unread count |

### Frontend Types

```typescript
type NotificationRecord = {
  id: string;
  type: string;
  title: string;
  body: string;
  data: Record<string, unknown>;
  read: boolean;
  created_at: string;
};
```

---

## 7. Dedicated Job Offer Evaluator Assistant

### New Table

**`offer_evaluations`:**

| Column | Type | Description |
|--------|------|-------------|
| id | UUID PK | |
| profile_id | UUID FK → career_profiles | Owner |
| company | VARCHAR(200) | Company name |
| role_title | VARCHAR(200) | Role title |
| offer_details | TEXT | Raw offer input |
| result | JSONB | Structured evaluation from chain |
| overall_score | FLOAT | 0-10 overall score |
| recommendation | VARCHAR(50) | `strongly_recommend`, `recommend`, `neutral`, `caution`, `avoid` |

### AI Components

**Schema** (`app/ai/schemas/offer_eval_schema.py`):
```python
class CompensationAnalysis:
    base_salary_range, equity_range, bonus_range, total_comp_range, market_percentile

class GrowthPotential:
    promotion_track, skill_development, mentorship

class WorkLifeBalance:
    remote_policy, hours_expectation, travel_requirement

class OfferScore:
    overall, compensation, growth, work_life, culture  (all 0-10)

class OfferEvaluationResult:
    compensation: CompensationAnalysis
    growth: GrowthPotential
    work_life: WorkLifeBalance
    scores: OfferScore
    pros: list[str]
    cons: list[str]
    recommendation: str
    recommendation_rationale: str
    market_benchmarks: str
    negotiation_tips: list[str]
```

**Chain** (`app/ai/chains/offer_eval_chain.py`):
- Takes `offer_details`, `profile_summary`, `market_context` → returns `OfferEvaluationResult`

**Prompt** (`app/ai/prompts/offer_eval_prompt.py`):
- Expert compensation analyst persona
- Rules: data-driven, consider experience/location/industry, honest scoring

### Service

**`offer_service.py`:**
- `_profile_summary()`: Builds candidate profile string from CareerProfile + Skills
- `evaluate()`: 
  1. Retrieve RAG context for market benchmarks via `knowledge_service.retrieve()`
  2. Quota check
  3. Chain invoke
  4. Persist evaluation
  5. Ingest to RAG corpus
  6. Award 35 XP for `offer_evaluated`
- `latest()`, `list_history()`, `get()`: Standard profile-scoped reads

### API

| Method | Path | Description | Rate Limit |
|--------|------|-------------|------------|
| POST | `/offers/evaluate` | Evaluate a job offer | 5/min |
| GET | `/offers/latest` | Latest evaluation | — |
| GET | `/offers/history` | All evaluations | — |
| GET | `/offers/{id}` | Specific evaluation | — |

### RAG Integration

- Before chain invoke: queries `knowledge_service.retrieve()` for market compensation data
- After persist: ingests offer evaluation into personal corpus for future reference

---

## 8. Hybrid RAG Integration

### New Utility

**`app/services/hybrid_rag.py`:**

```python
def retrieve_context(
    db, profile_id, query, *, max_chars=6000
) -> str:
```

- Embeds the query once
- Retrieves top-3 from personal corpus (profile_id-filtered)
- Retrieves top-3 from curated corpus (no filter)
- Builds a formatted context string: `[Your Documents]\n...\n\n[CareerGrowth Guidance]\n...`
- Returns empty string if nothing found
- Graceful degradation: per-corpus failures are logged but don't crash the feature

### Updated Features

| Feature | File | Change |
|---------|------|--------|
| CV Analysis | `cv_service.py` | Retrieves "CV writing best practices" context before chain |
| Job Match | `matching_service.py` | Retrieves context from job description; passes `rag_context` to prompt |
| Skill Gap | `matching_service.py` | Retrieves context; passes `rag_context` to prompt |
| Roadmap | `roadmap_service.py` | Retrieves career path context via `knowledge_service.retrieve()` |
| Offer Eval | `offer_service.py` | Retrieves market compensation context (separate impl) |

### Prompt Updates

**`job_match_prompt.py`**: Added `rag_context` input variable with section:
```
Reference context (market data, industry standards, guidance):
---
{rag_context}
---
```

**`skill_gap_prompt.py`**: Added `rag_context` input variable with section:
```
Reference context (industry skill frameworks, market trends, guidance):
---
{rag_context}
---
```

### Performance Notes

- Each embedding call adds ~200ms latency
- Mitigated by: reduced `k=3` for features vs `k=5` for chat; MAX_CONTEXT_CHARS bounds prompt size
- Embedding is shared across corpora (one embed, two retrievals)

---

## Migration Summary

**File:** `migrations/versions/0013_enhanced_features.py`

### Upgrade

1. `ALTER TABLE roadmap_steps ADD COLUMN micro_points JSON NOT NULL DEFAULT '[]'`
2. `ALTER TABLE roadmap_steps ADD COLUMN learning_resources JSON NOT NULL DEFAULT '[]'`
3. `ALTER TABLE job_applications ADD COLUMN deadline_at DATE`
4. `ALTER TABLE job_applications ADD COLUMN next_step VARCHAR(300) NOT NULL DEFAULT ''`
5. `ALTER TABLE job_applications ADD COLUMN next_step_date DATE`
6. `ALTER TABLE job_applications ADD COLUMN notified_deadline BOOLEAN NOT NULL DEFAULT false`
7. `CREATE TABLE quiz_attempts (...)` — 5 new indexes
8. `CREATE TABLE quiz_questions (...)` — 2 new indexes
9. `CREATE TABLE video_summaries (...)` — 2 new indexes
10. `CREATE TABLE notifications (...)` — 2 new indexes
11. `CREATE TABLE offer_evaluations (...)` — 2 new indexes
12. RLS and REVOKE for all 5 new tables

### Downgrade

Reverse of all above. See migration file for full `downgrade()`.

---

## New Files Created (26)

```
CareerGrowth/UPDATE_IMPACT_REPORT.md
CareerGrowth/spec.md

CareerGrowth/backend/app/models/quiz.py
CareerGrowth/backend/app/models/video.py
CareerGrowth/backend/app/models/notification.py
CareerGrowth/backend/app/models/offer.py
CareerGrowth/backend/app/ai/schemas/quiz_schema.py
CareerGrowth/backend/app/ai/schemas/video_schema.py
CareerGrowth/backend/app/ai/schemas/offer_eval_schema.py
CareerGrowth/backend/app/ai/prompts/quiz_prompt.py
CareerGrowth/backend/app/ai/prompts/video_summary_prompt.py
CareerGrowth/backend/app/ai/prompts/offer_eval_prompt.py
CareerGrowth/backend/app/ai/chains/quiz_chain.py
CareerGrowth/backend/app/ai/chains/video_summary_chain.py
CareerGrowth/backend/app/ai/chains/offer_eval_chain.py
CareerGrowth/backend/app/services/quiz_service.py
CareerGrowth/backend/app/services/video_service.py
CareerGrowth/backend/app/services/streak_service.py
CareerGrowth/backend/app/services/audio_service.py
CareerGrowth/backend/app/services/notification_service.py
CareerGrowth/backend/app/services/offer_service.py
CareerGrowth/backend/app/services/hybrid_rag.py
CareerGrowth/backend/app/api/quiz.py
CareerGrowth/backend/app/api/video.py
CareerGrowth/backend/app/api/notifications.py
CareerGrowth/backend/app/api/offers.py
CareerGrowth/backend/migrations/versions/0013_enhanced_features.py
```

## Files Modified (12)

```
backend/app/models/roadmap.py         # Added micro_points, learning_resources columns
backend/app/models/application.py     # Added deadline tracking columns
backend/app/models/growth_event.py    # New event type documentation
backend/app/models/__init__.py        # New model exports
backend/app/ai/schemas/roadmap_schema.py  # MicroPoint, ResourceLink, updated RoadmapStep
backend/app/ai/prompts/roadmap_prompt.py  # Micro-point + resource instructions
backend/app/ai/prompts/job_match_prompt.py   # rag_context input
backend/app/ai/prompts/skill_gap_prompt.py   # rag_context input
backend/app/services/xp_service.py           # New XP events + streak integration
backend/app/services/roadmap_service.py      # Persist new fields + RAG context
backend/app/services/matching_service.py     # Hybrid RAG for job match + skill gap
backend/app/services/cv_service.py           # Hybrid RAG for CV analysis
backend/app/services/application_service.py  # Deadline fields + XP on apply
backend/app/services/interview_service.py    # Audio transcription support
backend/app/api/interview.py                 # Multipart file upload for audio
backend/app/main.py                          # 4 new routers registered
frontend/src/lib/services.ts                 # Types + API functions for all features
```

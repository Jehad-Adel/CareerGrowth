# UPDATE IMPACT REPORT — CareerFarm Architectural Changes

## Overview

This report analyzes the impact of 8 major feature additions on CareerFarm's database schemas, LLM chains, RAG integration, and performance. Each section documents pre-change state, proposed changes, and migration strategy.

---

## 1. Enhanced Granular Roadmaps

### Current State
- `RoadmapStep` model stores broad topics with `title`, `description`, `reason`, `difficulty`, `skills_to_acquire`, `recommended_resources` (list of platform names), `project_to_practice`
- `roadmap_schema.py`: `RoadmapStep` Pydantic model with same fields
- `roadmap_prompt.py`: instruction to output 2-4 resource names (no URLs)
- `roadmap_chain.py`: `ROADMAP_PROMPT | structured_llm`
- `roadmap_service.py`: generates steps, persists, awards XP, ingests to RAG

### Changes Required
**Database:**
- Add `micro_points: JSON` column to `roadmap_steps` — array of fine-grained actionable sub-steps
- Add `learning_resources: JSON` column to `roadmap_steps` — array of `{title, url, type}` objects for curated tutorials/docs
- No new tables needed

**AI Schemas:**
- Update `RoadmapStep` in `roadmap_schema.py`:
  - Add `micro_points: list[str]` — 3-7 granular action items per step
  - Change `recommended_resources` from `list[str]` (names only) to `list[ResourceLink]` with `title: str`, `url: str | None`, `type: Literal["tutorial", "documentation", "course", "video", "book"]`
  - Add `ResourceLink` model

**Prompt:**
- Update `roadmap_prompt.py` to instruct AI to output micro-points and concrete resource links
- Note: URL hallucination risk is managed by instructing the model to only include URLs it is confident are real, and always provide `title` + `type`

**Service:**
- Update `roadmap_service.py` to persist `micro_points` and `learning_resources` from chain output
- Update RAG ingest text to include micro-points

**Migration:**
```sql
ALTER TABLE roadmap_steps ADD COLUMN micro_points JSON NOT NULL DEFAULT '[]';
ALTER TABLE roadmap_steps ADD COLUMN learning_resources JSON NOT NULL DEFAULT '[]';
```

---

## 2. Dynamic Quiz Engine

### Current State
- No quiz feature exists anywhere in the codebase

### Changes Required
**Database — New Tables:**
- `quiz_attempts`: `id UUID PK`, `profile_id UUID FK`, `source_type` (roadmap_step/document/video), `source_id UUID`, `mastery_level INT`, `score FLOAT`, `total_questions INT`, `completed_at TIMESTAMP`, `created_at TIMESTAMP`
- `quiz_questions`: `id UUID PK`, `attempt_id UUID FK`, `question TEXT`, `options JSON` (array of strings), `correct_answer INT` (index), `user_answer INT`, `is_correct BOOL`, `explanation TEXT`, `created_at TIMESTAMP`

**New Models:**
- `QuizAttempt`, `QuizQuestion` SQLAlchemy models in `app/models/quiz.py`

**AI Schema:**
- `QuizQuestion` Pydantic model: `question`, `options: list[str]`, `correct_answer: int`, `explanation: str`
- `QuizResponse` Pydantic model: `questions: list[QuizQuestion]`, `overall_explanation: str`

**New Chain:**
- `build_quiz_chain()` — takes source text + mastery level, generates N questions
- `build_quiz_eval_chain()` — evaluates user answers, provides feedback

**New Prompt:**
- `quiz_prompt.py` — instructs model to generate questions tailored to source material and user mastery level

**New Service:**
- `quiz_service.py` — `generate_quiz()`, `submit_answers()`, `history()`
- Follows existing patterns: quota check, chain invoke, persist, XP award

**New API Routes:**
- `POST /quiz/generate` — body: `source_type`, `source_id`, `num_questions`
- `POST /quiz/submit` — body: `attempt_id`, `answers: list[int]`
- `GET /quiz/history`
- `GET /quiz/attempts/{id}`

**New Growth Event Types:**
- Add `quiz_completed` to `XP_AWARDS` (30 XP)
- Add `quiz_completed` to `GrowthEvent` type documentation

**RAG Integration:**
- Ingest quiz questions + explanations into personal document corpus

---

## 3. Video Summarizer / Transcript Tool

### Current State
- No video processing exists
- Frontend has `use-dictation.ts` (client-side speech recognition hooks, likely for future use)

### Changes Required
**Database — New Table:**
- `video_summaries`: `id UUID PK`, `profile_id UUID FK`, `url TEXT`, `title TEXT`, `transcript TEXT`, `summary TEXT`, `source_type TEXT` (youtube/vimeo/etc), `created_at TIMESTAMP`

**New Model:**
- `VideoSummary` SQLAlchemy model in `app/models/video.py`

**External Dependency:**
- Use `youtube-transcript-api` (Python library) to fetch YouTube transcripts
- For other platforms, use LangChain's document loaders or a generic approach

**New Service:**
- `video_service.py` — `fetch_transcript(url)`, `summarize(db, profile_id, url)`
- `fetch_transcript`: extract video ID from URL, fetch transcript via youtube-transcript-api
- `summarize`: if transcript exists, call summarization chain; else return raw transcript

**New Chain:**
- `build_video_summary_chain()` — takes transcript text, returns structured summary
- `VideoSummarySchema` Pydantic model: `title`, `summary_points: list[str]`, `key_takeaways: list[str]`, `full_transcript: str`

**New Prompt:**
- `video_summary_prompt.py` — instructs model to create concise breakdown

**New API Routes:**
- `POST /video/process` — body: `url`, `mode: Literal["summary", "transcript"]`
- `GET /video/history`
- `GET /video/{id}`

**New Growth Event Type:**
- Add `video_processed` to `XP_AWARDS` (15 XP for summary, 5 for transcript)

**Dependencies:**
- `uv add youtube-transcript-api`
- Update `pyproject.toml`

---

## 4. Expanded Streak & XP System

### Current State
- `CareerProfile` has `streak_days` (int) and `last_active_on` (date) fields defined but **never updated**
- XP awarded only for: `cv_analyzed`, `skill_discovered`, `skill_leveled`, `job_matched`, `gap_analyzed`, `roadmap_created`, `goal_completed`, `interview_completed`
- `xp_service.record_event()` updates XP and level but NOT streak

### Changes Required
**Streak Logic (new `streak_service.py`):**
- On any meaningful engagement, call `record_activity(db, profile_id)`:
  - If `last_active_on` is yesterday: increment `streak_days` by 1
  - If `last_active_on` is today: no change (idempotent)
  - If `last_active_on` is older: reset `streak_days` to 1
  - Set `last_active_on` to today
- Expose `get_streak_info(db, profile_id)` returning `{streak_days, last_active_on}`

**New XP Event Types:**
- Add to `XP_AWARDS`:
  - `quiz_completed`: 30
  - `video_summarized`: 15
  - `video_transcribed`: 5
  - `interview_stt`: 10 (using speech-to-text)
  - `applied_job`: 25
  - `cv_optimized`: 20
  - `offer_evaluated`: 35
  - `daily_login`: 5 (streak maintenance bonus)

**Integration Points (where to trigger activity):**
- `roadmap_service.complete_step()` → already has XP, add `record_activity()`
- `interview_service.answer()` → already has XP on finish, add `record_activity()`
- `matching_service.match_job()` → already has XP, add `record_activity()`
- `matching_service.analyze_gap()` → already has XP, add `record_activity()`
- `application_service.create()` → new XP event, `record_activity()`
- `profile_service.update()` (CV update) → new XP event, `record_activity()`
- New quiz service → new XP event, `record_activity()`
- New video service → new XP event, `record_activity()`
- New offer evaluator → new XP event, `record_activity()`

**Migration:**
No schema changes needed — `streak_days` and `last_active_on` already exist on `CareerProfile`.

---

## 5. Speech-to-Text for Virtual Interviews

### Current State
- `InterviewSession` model has `cv_text`, `level`, `job_description`, `interviewer_name`, `finished`, `final_evaluation`
- `InterviewTurn` model has `question`, `answer` (text), `feedback`, `score`
- `interview_service.answer()` takes `text: str` as the answer
- Frontend has `use-dictation.ts` and `use-dictation-language.ts` (unused/placeholder)

### Changes Required
**Backend:**
- No new database tables — audio is transcribed, never stored
- Add optional `audio_data: bytes | None` field to answer input
- NEW: `audio_service.py` — `transcribe_audio(audio_data: bytes) -> str` using Google's Speech-to-Text API (Gemini has multimodal, or use `google-cloud-speech`)
- Alternative: Use Gemini's multimodal capability directly — pass audio alongside prompt

**Updated Interview Chain:**
- The existing `build_interview_chain()` already works with text
- Audio is transcribed on the backend and fed as text into the existing chain
- No changes to the chain itself

**Updated Service:**
- `interview_service.answer()` updated to accept optional `audio: bytes`
- If audio provided, transcribe first, then proceed with existing logic

**New API Route:**
- Update `POST /interview/sessions/{id}/answer` to accept both `text` and `audio` (multipart form or base64)

**Frontend:**
- Use `use-dictation.ts` to capture microphone input
- Send audio blob to backend alongside or instead of text
- Display transcribed text in UI before sending

**Dependencies:**
- `uv add google-cloud-speech` OR use Gemini's multimodal (no extra dependency)
- With Gemini: send audio + prompt directly — `ChatGoogleGenerativeAI` supports multimodal content

**Migration:**
No schema changes.

---

## 6. Application Tracking & Smart Notifications

### Current State
- `JobApplication` model has: `company`, `role`, `status`, `job_match_id`, `applied_at`, `notes`, `url`
- Statuses: `saved → applied → interviewing → offer → rejected`
- `CLOSED_STATUSES`: `offer`, `rejected`
- `application_service.py`: full CRUD + pipeline management
- No notification system exists

### Changes Required
**Database — Add Deadline Tracking:**
- Add to `JobApplication`:
  - `deadline_at: Date | None` — application deadline
  - `next_step: str` — e.g. "Follow up", "Prepare for interview"
  - `next_step_date: Date | None` — when to do the next step
  - `notified_deadline: bool` — whether user was already notified about deadline

**Database — New Notification Table:**
- `notifications`: `id UUID PK`, `profile_id UUID FK`, `type` (deadline_approaching/status_update/streak_reminder/custom), `title TEXT`, `body TEXT`, `data JSON` (optional payload), `read BOOL DEFAULT false`, `created_at TIMESTAMP`

**New Models:**
- Update `JobApplication` with new fields
- New `Notification` SQLAlchemy model

**New Service:**
- `notification_service.py` — `create()`, `list_unread()`, `mark_read()`, `mark_all_read()`, `count_unread()`
- `check_deadlines(db, profile_id)` — cron-like check: finds applications with deadlines within 3 days

**Updated Application Service:**
- Add `deadline_at` and `next_step` to create/update
- Auto-create notification when status changes or deadline approaches
- XP award for applying to jobs (25 XP)

**New API Routes:**
- `GET /notifications` — unread list
- `POST /notifications/{id}/read`
- `POST /notifications/read-all`
- `GET /notifications/count`
- `PATCH /applications/{id}` — updated to include deadline/next_step fields

**Frontend:**
- Notification bell icon in nav bar
- Dropdown showing unread notifications
- Badge count

**Migration:**
```sql
ALTER TABLE job_applications ADD COLUMN deadline_at DATE;
ALTER TABLE job_applications ADD COLUMN next_step VARCHAR(300) NOT NULL DEFAULT '';
ALTER TABLE job_applications ADD COLUMN next_step_date DATE;
ALTER TABLE job_applications ADD COLUMN notified_deadline BOOLEAN NOT NULL DEFAULT false;

CREATE TABLE notifications (
    id UUID PRIMARY KEY,
    profile_id UUID NOT NULL REFERENCES career_profiles(id) ON DELETE CASCADE,
    type VARCHAR(40) NOT NULL,
    title VARCHAR(300) NOT NULL,
    body TEXT NOT NULL DEFAULT '',
    data JSON NOT NULL DEFAULT '{}',
    read BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_notifications_profile_read ON notifications(profile_id, read);
```

---

## 7. Dedicated Job Offer Evaluator Assistant

### Current State
- `JobMatch` model evaluates how well a candidate matches a job
- No offer evaluation exists

### Changes Required
**Database — New Table:**
- `offer_evaluations`: `id UUID PK`, `profile_id UUID FK`, `company TEXT`, `role_title TEXT`, `offer_details TEXT` (raw input), `result JSON` (structured evaluation), `overall_score FLOAT`, `recommendation TEXT`, `created_at TIMESTAMP`

**New Model:**
- `OfferEvaluation` SQLAlchemy model in `app/models/offer.py`

**AI Schema:**
- `CompensationAnalysis`: `base_salary: range`, `equity: range`, `bonus: range`, `total_comp: range`, `market_percentile: str`
- `GrowthPotential`: `promotion_track: str`, `skill_development: str`, `mentorship: str`
- `WorkLifeBalance`: `remote_policy: str`, `hours_expectation: str`, `travel_requirement: str`
- `OfferScore`: `overall: float`, `compensation: float`, `growth: float`, `work_life: float`, `culture: float`
- `OfferEvaluationResult`: all above fields plus `pros: list[str]`, `cons: list[str]`, `recommendation: str`, `market_benchmarks: str`

**New Chain:**
- `build_offer_eval_chain()` — takes offer details + user's profile/experience
- Uses RAG context for market benchmarks

**New Prompt:**
- `offer_eval_prompt.py` — instructs model to score objectively against market data

**New Service:**
- `offer_service.py` — `evaluate(db, profile_id, company, role_title, offer_details)`, `latest()`, `list_history()`, `get()`
- Follows existing patterns: quota check, RAG retrieve for market data, chain invoke, persist, XP award

**New API Routes:**
- `POST /offers/evaluate` — body: `company`, `role_title`, `offer_details`
- `GET /offers/latest`
- `GET /offers/history`
- `GET /offers/{id}`

**New Growth Event Type:**
- Add `offer_evaluated` to `XP_AWARDS` (35 XP)

**RAG Integration:**
- Before evaluation, query RAG for market salary data and industry benchmarks
- Ingest evaluation result into personal corpus

---

## 8. Hybrid RAG Integration across Core Features

### Current State
- RAG retrieval currently happens ONLY in `chat_service.send()` — dual corpus (personal + curated)
- Other features (CV analysis, job matching, roadmap, skill gap) do NOT use RAG

### Changes Required
**Refactor `rag_service.py`:**
- Add `retrieve_hybrid(db, profile_id, query) -> tuple[list[DocumentChunk], list[KnowledgeChunk]]` — unified dual retrieval
- Add `retrieve_for_feature(db, profile_id, query, feature)` — feature-tagged retrieval

**Update Each Feature:**

1. **CV Analysis** (`cv_service.py`):
   - Before CV analysis, retrieve relevant knowledge_base entries about CV writing best practices
   - Inject into prompt context

2. **Job Matching** (`matching_service.py`):
   - Before job match, retrieve relevant market data and industry standards
   - Inject into prompt context

3. **Skill Gap Analysis** (`matching_service.py`):
   - Retrieve relevant skill framework data from knowledge_base
   - Inject into prompt context

4. **Roadmap Generation** (`roadmap_service.py`):
   - Retrieve relevant career path data and learning resources
   - Inject into prompt context

5. **Chat & Advisory** (`chat_service.py`) — already does this

6. **Quiz Generation** (new):
   - Retrieve relevant knowledge chunks for the source material
   - Inject to ground quiz questions

7. **Offer Evaluation** (new):
   - Retrieve market compensation benchmarks
   - Inject into prompt context

**Changes to Existing Chains:**
- Add `context` and/or `guidance` input variables to prompts that don't have them
- Modify chain factory to accept additional context parameters

**Performance Impact:**
- Each AI call will now do 1-2 additional embedding lookups + context building
- Embedding is the bottleneck (~200ms per query)
- Mitigation: cache embeddings for identical queries within a session, reduce TOP_K for feature retrieval vs chat

**Prompt Template Updates:**
- Each prompt that receives RAG context must have clear instructions about prioritizing retrieved context over general knowledge

---

## Migration Strategy

### Phase 1: Schema Migrations
1. Add columns to `roadmap_steps` (micro_points, learning_resources)
2. Create `quiz_attempts`, `quiz_questions` tables
3. Create `video_summaries` table
4. Add columns to `job_applications` (deadline, next_step)
5. Create `notifications` table
6. Create `offer_evaluations` table
7. Add growth event types documentation

### Phase 2: AI Chains & Prompts
1. Update roadmap schema + prompt + chain
2. Create quiz chain + prompt + schema
3. Create video summary chain + prompt + schema
4. Create offer evaluation chain + prompt + schema
5. Update all 5 core feature chains for RAG context injection

### Phase 3: Services
1. Update roadmap_service
2. Create quiz_service + streak_service + notification_service + video_service + offer_service + audio_service
3. Update xp_service with new event types
4. Update application_service with deadline fields
5. Update chat_service (already has dual RAG)
6. Update cv_service, matching_service, roadmap_service for hybrid RAG

### Phase 4: API Routes
1. New routes for quiz, video, notifications, offers
2. Updated routes for applications, interviews

### Phase 5: Frontend (summary — detailed in separate FE impact report)
1. Granular roadmap UI with micro-points and resource links
2. Quiz interface
3. Video URL input + summary/transcript display
4. Streak display in profile header
5. Audio recording in interview
6. Notification bell component
7. Offer evaluation form + result display
8. Deadline fields in application tracker

---

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|-----------|------------|
| URL hallucination in roadmap resources | Medium | High | Add strict prompt instruction; validate URLs client-side; allow manual correction |
| Quiz question quality | Medium | Medium | Evaluate with test suite; adjust prompt temperature |
| STT transcription errors | Low | Low | Use Google's mature STT API; allow manual text correction |
| Embedding quota exhaustion | High | Medium | Add pacer for bulk operations; monitor usage |
| Prompt context overflow | Medium | Low | Enforce MAX_CONTEXT_CHARS limits |
| Notification spam | Low | Low | Deduplicate by type+profile; rate-limit creation |
| Deadline notification latency | Low | Medium | Check on relevant API calls (not a background worker) |

---

## Rollback Strategy

Each feature is independently revertible:
1. **Schema changes**: Use `alembic downgrade` for each migration
2. **AI chains**: Remove new import references; old chains unchanged
3. **Services**: Remove new service files; revert modified existing services
4. **API routes**: Remove new routers; revert modified routes
5. **Frontend**: Revert component additions (git checkout)

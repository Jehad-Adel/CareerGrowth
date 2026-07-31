# 🚀 [Tips Hindawi](https://www.tipshindawi.com/) Challenge (June–July) 2026

> 🏆 This repository is my official submission for the [ **Tips Hindawi** ](https://www.tipshindawi.com/) **Challenge (June–July) 2026**.

## 👤 Participant

| Field            | Value                                |
| ---------------- | ------------------------------------ |
| Full Name        |    Jehad Adel Al-Basyouni                                  |
| Project Name     |         CareerGrowth                             |
| GitHub Username  |                Jehad-Adel                      |
| Challenge Batch  | June–July 2026                       |
| Training Program | Large Language Models (LLMs) Program |
| Organization     | [**Edrak for Ai**](https://edrak4ai.com/en)                         |

---

# 📖 Project Overview

CareerGrowth is an advanced AI-powered career assistant platform that combines Hybrid RAG (Retrieval-Augmented Generation), LLM-driven analysis, and gamification to help professionals accelerate their career growth. Users upload their CV for deep analysis, match against job descriptions, generate personalized roadmaps, practice mock interviews with speech-to-text, test knowledge with dynamic quizzes, summarize videos, evaluate job offers, and track applications — all grounded in a curated knowledge base and personal document corpus via vector search.

---

# ✨ Features

* **CV Analysis** — Upload a PDF; AI extracts skills, experience, seniority, and improvement suggestions.
* **Job Matching** — Compare your CV against any job description with structured skill-by-skill matching.
* **Skill Gap Analysis** — Identify exactly what to learn next, ranked by importance and prerequisites.
* **Resume Optimizer** — Rewrite your CV for ATS compatibility with before/after scores.
* **Cover Letter Generator** — Personalized cover letters tailored to each job.
* **Granular Micro-Roadmaps** — Multi-step career roadmaps with 3–7 micro-points per step and curated learning resources (tutorials, docs, courses).
* **Dynamic Quiz Engine** — AI generates multiple-choice questions from any source text, tailored to your mastery level (1–5).
* **Video Summarizer / Transcript** — Paste a YouTube link; get an AI summary or full transcript.
* **Mock Interviews** — Practice with 3 personas (friendly HR, technical lead, stress interview); optional speech-to-text voice answers.
* **Career Chat** — AI assistant grounded in your CV, job matches, and curated career guidance via dual-corpus RAG.
* **Application Tracker** — Track jobs through the pipeline (saved → applied → interviewing → offer → rejected) with deadline notifications.
* **Smart Notifications** — Automatic alerts for approaching application deadlines, status changes, and reminders.
* **Job Offer Evaluator** — Paste a job offer; get objective scores on compensation, growth, work-life balance, and negotiation tips.
* **XP & Streak System** — Earn XP for every engagement (14 event types); level up from Seedling to Homesteader with daily streak tracking.
* **Hybrid RAG** — Deep retrieval-augmented generation across Chat, CV Analysis, Job Matching, Roadmap, Skill Gap, and Offer Evaluation using both personal documents and a curated knowledge base.

---

# 🛠️ Technologies Used

| Category | Technology |
|----------|-----------|
| **Backend** | Python 3.11+, FastAPI, SQLAlchemy 2, Alembic |
| **LLM** | Google Gemini (gemini-flash-lite-latest), LangChain Core |
| **Embeddings** | gemini-embedding-001 (768-d, pgvector) |
| **Vector DB** | pgvector (PostgreSQL extension) |
| **Database** | PostgreSQL (Supabase), SQLite (tests) |
| **Auth** | Supabase Auth (ES256 JWTs) |
| **Validation** | Pydantic v2 (backend), Zod v4 (frontend) |
| **Frontend** | Next.js 16, React 19, Tailwind CSS v4, shadcn/ui |
| **Audio STT** | Google Gemini multimodal (no separate STT API) |
| **Video Transcripts** | youtube-transcript-api |
| **PDF Parsing** | pypdf |
| **Config** | pydantic-settings |
| **Logging** | structlog |
| **Rate Limiting** | slowapi / limits |
| **Package Manager** | uv (Python), npm (JS) |
| **Deployment** | Railway (backend), Vercel (frontend) |

---

# ⚙️ Installation

```bash
# Clone the repository
git clone https://github.com/<your-username>/careergrowth.git
cd careergrowth/CareerGrowth

# Backend setup
cd backend
uv sync                          # Install Python dependencies
cp ../.env.example ../.env       # Configure environment variables
uv run alembic upgrade head      # Run database migrations
uv run python -m app.cli.ingest_knowledge  # Ingest curated knowledge base

# Frontend setup
cd ../frontend
npm install                      # Install Node dependencies
```

---

# 🚀 Usage

```bash
# Start the backend (from backend/)
uv run uvicorn app.main:app --port 8000

# Start the frontend (from frontend/)
npm run dev                      # Opens http://localhost:3000

# Run tests
cd backend && uv run pytest -q   # Backend test suite
cd frontend && npm run build     # Frontend type check + build
```

**Key environment variables** (`.env`):
- `DATABASE_URL` — PostgreSQL connection string
- `SUPABASE_URL` — Supabase project URL
- `GOOGLE_API_KEY` — Gemini API key
- `NEXT_PUBLIC_API_URL` — Backend URL (default: http://localhost:8000)

---

# website

(https://careergrowth-production.vercel.app)

---

# 📈 Results

- **Hybrid RAG pipeline** across 6 core features reduces hallucination by grounding every AI response in retrieved context from the user's own documents and a curated knowledge base of 291 entries across 19 career categories.
- **14 XP event types** drive the gamification system with 10 level tiers (Seedling → Homesteader), auto-tracked daily streaks, and real-time profile updates.
- **Structured LLM output** for all 11 chains via Pydantic schemas ensures parseable, type-safe AI responses without regex parsing or fragile text extraction.
- **SQLAlchemy 2 sync + pgvector** enables sub-second vector similarity search across both personal and shared corpora with profile-scoped access control.
- **Comprehensive test suite** with 20+ backend tests running against SQLite in-memory, including middleware ordering, authorization scoping, and cascade deletion.

---

# 🔮 Future Improvements

* **Real-time streaming** — Stream LLM responses token-by-token via Server-Sent Events for instant chat and interview feedback.
* **Multi-language support** — Expand CV analysis and interviews to support Arabic, French, and other languages using Gemini's multilingual capabilities.
* **Browser push notifications** — Integrate Web Push API for deadline alerts even when the tab is closed.
* **Social features** — Peer mentoring, public roadmaps, and community career insights.
* **Mobile app** — React Native or PWA for on-the-go interview practice and application tracking.
* **Advanced analytics** — Career trajectory predictions, market trend analysis, and personalized learning recommendations powered by usage patterns.

---

# 📚 About the Challenge

This project was developed as part of the [**Tips Hindawi**](https://www.tipshindawi.com/) **Challenge (June–July) 2026**.

[Tips Hindawi](https://www.tipshindawi.com/) is the internships department of [**Edrak for Ai**](https://edrak4ai.com/en), and the challenge encourages participants to build real-world projects, apply practical skills, and showcase their work through GitHub.

For more information about the challenge, training programs, and upcoming batches, visit the official [Tips Hindawi](https://www.tipshindawi.com/) website.

---

# 📄 License

This project is shared for educational and portfolio purposes.

# CareerGrowth portfolio screenshots

37 viewport screenshots captured on 2026-10-12 with the Playwright CLI. Every PNG is 1920×1080, device scale factor 1, CSS scale 1, and `fullPage:false`.

Coverage: all 15 normal pages, the designed 404, completed interview history, all four job-analysis tabs, generated quiz questions and scored feedback, video summary/transcript, offer evaluation, and important lower page sections. Filenames describe each captured section; numbering gaps mean no extra lower section was needed.

`manifest.json` lists every screenshot, route, state, scroll position, and fixture provenance. Mock data belongs to fictional Maya Chen; no live backend, Supabase, or Gemini calls ran. Browser requests were confined to loopback, with zero console/page errors.

Reproduce from `frontend/`: `npm ci`, `npx playwright install chromium`, then `npm run portfolio:capture`. See `../docs/portfolio-captures.md` for harness details. The copied harness is ignored and production authentication stays intact.

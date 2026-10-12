# Portfolio viewport captures

Run from a fresh checkout:

```powershell
cd frontend
npm ci
npx playwright install chromium
npm run portfolio:capture
```

The Playwright CLI executes `portfolio/capture.spec.ts`, after `portfolio/prepare.mjs` makes an ignored `.portfolio-harness/frontend` copy and installs its own locked dependencies on first use. Only that copy replaces authentication with a fictional session and disables auth submission/callbacks. Production authentication and production components remain intact. It never reads the repository `.env`.

The harness binds Next to `127.0.0.1:3102` and the fixture HTTP service to `127.0.0.1:4102`. No real backend starts. No Supabase, Gemini, or private database requests run. The browser intercepts and rejects every non-loopback request. Google font downloads during Next compilation are build assets, not API calls. Fixture data describes Maya Chen, a fictional frontend engineer, and realistic career activity.

Images are saved in repository-root `screenshots/`. Each is a 1920×1080 PNG at device scale factor 1 with `fullPage:false` and CSS screenshot scale 1. `screenshots/manifest.json` records the route, UI state, section, scroll position, dimensions, and fixture provenance. Lower sections are captured by scrolling the same viewport. Capture readiness requires populated HTML, finished skeletons, settled fonts, and no busy forms; browser console/page errors fail the run.

Coverage includes the landing hero/features/workflow/how-it-works/closing, login, signup, dashboard, farm, CV analysis, learning roadmap, active/completed interview, application pipeline, grounded chat, notifications, all four job tools, quiz setup/questions/feedback, video setup/summary/transcript, offer setup/evaluation/negotiation, and the designed 404. Lower captures are emitted only if a page extends beyond the viewport, so filenames can contain numbering gaps.

These artifacts prove portfolio rendering against fixtures. They do not prove production authentication, AI quality, migrations, or real backend availability. Local capture code stays outside production runtime imports and the temporary harness stays ignored.

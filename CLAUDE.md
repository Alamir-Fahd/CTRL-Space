# CTRL+SPACE — project memory for Claude Code

NASA Space Apps Challenge 2026, challenge “Flame in Freefall”. Team: Susanah Elkess Dawoud, Judy Melouk, Al Amir Fahd.
An evidence-first research app for NASA microgravity combustion: search NASA Technical Reports Server (NTRS) reports, read verified passages, ask an AI that may only answer from cited passages, compare experiments, learn, discuss. Website (`/`) + dedicated mobile app (`/app`, English + Arabic RTL), one Python backend.

## Owner decisions (do not reverse without asking)
- Keep **Flask + SQLite + vanilla JavaScript** (no Angular/React/Node/MongoDB rewrite). No build step.
- Keep Learning Studio, Challenges and Community.
- Native phone apps = **Capacitor shell** around `/app` (`mobile/capacitor/`), built in GitHub Actions. A React Native/Expo client was requested but never built.
- Do not claim NASA endorsement. The original logo has the NASA insignia; the app uses a crop without it.

## Non-negotiable rules
1. **Never fabricate** scientific values, citations, NASA data, AI answers or test results. Missing data stays “Not reported / Not extracted”, never zero.
2. The assistant answers only from **verified passages** that pass the evidence gate; citations must match retrieved passages; numbers in generated text must appear in cited passages (flagged otherwise). Without an AI provider it must say “retrieval-only”.
3. NASA titles, passages, experiment values and lesson content stay **English verbatim**, also in Arabic mode.
4. **CSP is strict** (`script-src 'self'`): no inline `<script>`, no inline `style="…"` attributes, no `eval`/`new Function`. Size bars with `data-w` (applied in `main.js after()`), not inline styles.
5. API keys stay **server-side** (`.env`). Never commit `.env` or `data/*.db`.
6. After any change: run the backend tests and the suite for the area you touched (below). Report real pass/fail counts only.

## Layout
```
run.py                     CLI: serve | create-admin | ingest | reset-db | check-ai | preflight (loads .env itself)
backend/ctrlspace/         Flask app factory, db.py (schema v4 + in-place migrations), api/ (routes), services/ (search BM25, assistant, intelligence, experiments, auth, ingest)
  api/mobile_routes.py     conversations, notifications, password resets, NASA Image Library proxy, public profiles, AI comparison, feedback
frontend/                  desktop website (index.html, js/, css/), sw.js (offline), manifest.webmanifest
frontend/app/              mobile app: index.html, app.css, js/core.js, main.js, i18n.js (Arabic), screens-a..d.js (28 screens)
data/seed/corpus.json      6 NTRS reports, 36 verified passages, 8 experiments, lessons, challenges
tests/test_backend.py      backend unit/integration tests
e2e/                       Playwright: test_e2e.py (desktop), mobile_app_test.py, mobile_ar_test.py, pwa_test.py, mobile_devices.py
eval/, scripts/            retrieval evaluation + benchmark; run_e2e.sh
mobile/capacitor/ + .github/workflows/   Android APK / iOS build kit (cloud builds)
docs/                      MASTER_CHECKLIST.md (status of every requirement), CONVERSATION_LOG.md, API.md, ARCHITECTURE.md, TESTING.md, NATIVE_BUILDS.md, MOBILE_ARCHITECTURE.md …
```

## Commands
Windows PowerShell uses `.venv\Scripts\python`; macOS/Linux use `.venv/bin/python`.
```bash
python -m venv .venv && <venv-python> -m pip install -r requirements.txt
<venv-python> -m playwright install chromium          # only for browser tests
copy .env.example .env    (or: cp .env.example .env)
<venv-python> run.py create-admin you@example.com "Your Name"
<venv-python> run.py preflight                         # demo readiness
<venv-python> run.py serve                             # http://127.0.0.1:8000  and  /app
<venv-python> -m unittest discover -s tests            # backend: 88 tests
bash scripts/run_e2e.sh                                # desktop E2E: 19 (bash: macOS/Linux/Git Bash/WSL)
<venv-python> e2e/mobile_app_test.py http://127.0.0.1:8000 "iPhone 14"   # needs server running: 20
<venv-python> e2e/mobile_ar_test.py http://127.0.0.1:8000                # Arabic: 5
<venv-python> e2e/pwa_test.py http://127.0.0.1:8000                      # installable app: 9
<venv-python> run.py check-ai                          # after setting CTRLSPACE_AI_PROVIDER/MODEL/API_KEY
```
Last verified run (Linux sandbox, Chromium emulation): backend 88/88, desktop 19/19, mobile app 20/20 (iPhone 14 and Pixel 7), Arabic 5/5, PWA 9/9, website on phones passing, no overflow at 320–1280 px.
Re-verified 2026-11-13 on Windows 11 (VS Code, Python 3.11.9, fresh `.venv`): same counts, via the actual documented commands (`scripts/run_e2e.sh`, the `Test: *` VS Code tasks). That run found and fixed two Windows-only bugs: (1) `e2e/*.py` crashed on Windows' default cp1252 console when printing Unicode (e.g. “→”) — fixed with `sys.stdout.reconfigure(encoding='utf-8')` in each script; (2) `scripts/run_e2e.sh` called bare `python3`, which on Windows resolves to a Python with none of this project's dependencies installed, not the project's own `.venv` — fixed to prefer `.venv/Scripts/python.exe` / `.venv/bin/python`. If you hit either symptom again, that's the fix.

## Conventions
- New DB columns/tables: add to `SCHEMA` and the `add(...)` migrations in `db.py`; bump `SCHEMA_VERSION`; keep old databases upgradable.
- New mobile UI text: add the Arabic translation to `frontend/app/js/i18n.js` (exact string or a pattern). Interface text is translated after render; data is not.
- New mobile screen: add the route in `main.js ROUTES`, the view in a `screens-*.js`, cache the file in `frontend/sw.js` and bump its `VERSION`.
- Buttons use `data-act`, forms use `data-form`; handlers live in `main.js`.
- Touch targets ≥ 44 px; no horizontal overflow at 320 px.

## Auth, demo account, categories, nav redesign (2026-11-13)
- `users` table gained `category` (student/researcher/educator/other), `institution`, `is_demo` columns — `SCHEMA_VERSION` is now 6.
- A real, idempotent demo account (`demo.student@ctrlspace.local` / `Demo@12345`, seeded via `auth.ensure_demo_account()`) exists on every non-test, non-production-unless-`CTRLSPACE_SEED_DEMO=true` startup — visible with copy buttons on the mobile login screen. Full detail: `docs/fixes/DEMO_ACCOUNT_SETUP.md`.
- The mobile bottom nav was redesigned: all 5 tabs (including Ask AI) are now visually identical, with a full rounded blue→purple pill covering icon+label on the active tab — the old raised/floating Ask AI treatment is gone. `docs/fixes/MOBILE_NAVIGATION_FIX.md`.
- Report/experiment cards (`cover()` in `core.js`) now show real, verified NASA Image Library photos per research program (BASS-II / Saffire), with an honest gradient fallback if offline — same doc, §3.
- See `docs/fixes/` for the full writeup, including one claim that was checked and found not to reproduce before anything was changed (`PROGRESS_TRACKING_FIX.md`).

## Real AI provider, already available on this machine
Ollama is installed (`winget install Ollama.Ollama`) with `llama3.1` already pulled (`ollama list` → `llama3.1:latest`, 4.9 GB) — don't re-download it. `.env` defaults to `CTRLSPACE_AI_PROVIDER=none` (the documented, regression-tested baseline every E2E/backend test suite assumes) — to actually use real AI answers, set `CTRLSPACE_AI_PROVIDER=ollama` and `CTRLSPACE_AI_MODEL=llama3.1` and restart the server. A real 30-question benchmark was run this way on 2026-11-13 (`docs/qa/AI_TEST_REPORT.md`): 0 fabricated citations, all out-of-scope questions correctly refused pre-LLM by the evidence gate. Two things to know before re-enabling it: (1) the *first* call after Ollama's own service restarts takes 60–120s while the model cold-loads into memory — this looks like a hang but isn't, `run.py check-ai` will just time out on that one call and succeed on retry; (2) the fast E2E/mobile suites are tuned for the `none` baseline's near-instant responses and will show false failures (hardcoded "Retrieval-only" text, short timeouts) against a real ~50s-per-answer local model — that's expected, not a regression; revert to `none` before running the full suite again.

## Android emulator (this machine only)
This Windows machine has Android Studio, SDK, emulator and a `Pixel_8` AVD already installed (`ANDROID_HOME=D:\Android\Sdk`) — don't assume they're unavailable without checking. `mobile/capacitor/` built and ran successfully on 2026-11-13: `npm install --ignore-scripts` (plain `npm install` fails — `@capacitor/cli`'s `sharp` dependency tries to download its native binary from a GitHub release that's throttled to ~36 KB/s in this sandbox; `--ignore-scripts` skips that and isn't needed just to build/run), then `npx cap add android`, then `JAVA_HOME="C:/Program Files/Android/Android Studio/jbr" ./gradlew assembleDebug` from `mobile/capacitor/android` (first run ≈26 min, mostly dependency resolution — don't assume it's stuck). Install with `adb install -r app/build/outputs/apk/debug/app-debug.apk`, launch with `adb shell am start -n com.ctrlspace.app/.MainActivity`. `capacitor.config.json`'s `server.url` is currently set to `http://10.0.2.2:8000/app` with `cleartext: true` for local emulator testing (`10.0.2.2` is the emulator's alias for the host machine) — change this back to a real HTTPS URL before any release build or physical-device test; it will not work on a real device.

## Strategic audit (2026-11-14)
- Official challenge title is "Flame in Freefall: **SI**-Powered Fire Safety Insights..." — "SI" = the challenge's own term "super intelligence," not "AI." Verified by rendering the live official challenge page with Playwright (static fetch only returns a loading skeleton). `README.md` corrected; dated historical reports (`docs/audit/`, `docs/final-audit/`, `CTRL_SPACE_FINAL_REPORT.md`) deliberately left as-is — they're point-in-time snapshots, not living docs.
- The challenge itself frames NASA fire safety as 3 pillars: **Prevention** (BASS/BASS-II, Saffire — the corpus's entire current coverage), **Detection** (SAME/SAME-R — zero coverage), **Suppression** (FLEX — zero coverage). This is a real, material scope gap against the actual brief, independent of anything else flagged this session. Expansion plan: `docs/strategic-audit/STRATEGIC_AUDIT.md` §3.
- `docs/DATA_SOURCES.md` had a stale passage count (34, should be 36 — one report, `20160000593`, gained 2 verified passages since the doc was last written and only the summary line had been checked before, not the per-report table). Fixed both the per-row count and the summary line; confirmed against live `/api/stats` and `/api/reports`.
- Architecture stays Flask + SQLite + vanilla JS — the Flutter/FastAPI+Supabase+Firebase rewrite proposals raised earlier this session were not pursued (never got an explicit confirm after being flagged as contradicting this project's own documented decision). Full reasoning: `docs/strategic-audit/STRATEGIC_AUDIT.md` §1.

## Wordmark & splash branding (2026-11-14)
- The mobile app splash (`frontend/app/index.html`/`app.css`) now uses the full `frontend/assets/hero.jpg` (flame-hand/Earth/starfield poster, already in the repo since 2026-11-12) as a full-bleed background, with a CSS-recreated two-tone wordmark (`.wm`/`.wmcorner`/`.wmplus`: red top-left bracket fading to white, blue bottom-right bracket + floating blue plus) over a bottom gradient. Two reference images were pasted into chat but never available as files in this session (no mechanism to export a pasted image to disk) — the wordmark was faithfully recreated in CSS since it's simple geometry; the poster art reused the project's own existing, matching `hero.jpg` rather than inventing a substitute. sw.js `VERSION` bumped to `v5.7.0`. Full writeup: `docs/qa/CTRL_SPACE_BRANDING_IMPLEMENTATION.md`.
- Bug found and fixed in passing: `.wm` had no `direction:ltr`, so the wordmark mirrored to "space + ctrl" under Arabic RTL — brand lockups should never mirror reading order regardless of page direction.
- Onboarding → Skip → guest browsing without login ("add onboarding then skip to see the app without login or sign up") was checked live and already worked end-to-end before any change — `finishOnboarding()` already routes to home with no auth gate, and `vHome()` already has a full guest state. No code change was needed for that part.

## Real NASA data expansion: Detection + Suppression pillars (2026-11-14)
- Corpus grew from 6→**10 reports**, 36→**87 verified passages**, 8→**10 experiments**, 5→**6 lessons**, 2→**4 programs** (added SAME, FLEX) — all real NTRS content, ingested through the existing unmodified pipeline (`services/ingest.py`, `POST /api/admin/ingest`), hand-verified passage by passage (`POST /api/admin/passages/<id>/review`), never fabricated. Full detail and rationale: `docs/DATA_SOURCES.md` §"Why these 4 reports".
- This closes the gap `docs/strategic-audit/STRATEGIC_AUDIT.md` §3 flagged: the challenge's 3 pillars (Prevention/Detection/Suppression) were Prevention-only before this pass. New reports: 20130000422 + 20150010172 (SAME, Detection), 20090014812 + 20150023456 (FLEX, Suppression) — found via NTRS's search API, not guessed IDs.
- New experiments `same2-smoke` and `flex-mdca` follow the exact same `experiment_fields` rules as every existing one (reported ⇒ must cite a verified passage; no clean single value ⇒ honestly `not_extracted`/`not_reported`/`not_applicable`, never guessed).
- New lesson `detection-and-suppression` (Learning Studio, position 5) — the first lesson that isn't Prevention-only, 5 sections citing 9 of the newly verified passages.
- Real NASA Image Library photos added for SAME/FLEX in `PROGRAM_PHOTOS` (`core.js`), same verification rigor as BASS-II/Saffire (read the real description, confirm genuine match, confirm the URL returns `200 image/jpeg`). Experiment detail pages also got a "Related NASA images" rail (`#relmedia`) matching the one report detail pages already had — reused main.js's existing generic hook, no new JS needed.
- Process note: every passage/field citation was cross-checked against the verified set after the fact (`SELECT ... LEFT JOIN passages ... WHERE NOT verified`) and caught 2 real gaps — a field citation and a lesson citation that referenced real, good passages I'd forgotten to verify — fixed before shipping. Worth repeating this check after any future manual citation work.
- One E2e test had a hardcoded search-result count (`'carbon monoxide'` → 2 reports) that's now legitimately 4, since the FLEX reports mention "carbon dioxide" as a suppressant. Updated the assertion, not the app — confirmed live first that the new matches are real, relevant results. Backend unit tests (93/93) were unaffected since they run against their own seeded test DB, not `data/ctrlspace.db`.
- A second admin account, `research.admin@ctrlspace.local`, was created for this work (`python run.py create-admin`) since the existing `qa.admin@ctrlspace.local`'s password from earlier E2E testing wasn't known/recorded.

## Status and next steps
Full requirement-by-requirement status: `docs/MASTER_CHECKLIST.md`. Note: on 2026-11-13 several items that checklist had marked ❌ (stop-generation, swipeable comparison cards, pull-to-refresh, page transitions, the “My Research” 5th tab, search suggestions, distinct AI tab, dedicated AI follow-up buttons) turned out to already be implemented and working — re-verify against the actual code before assuming something listed as missing truly is. Highest-value next steps:
1. Configure a real AI provider, run `check-ai`, then evaluate answers (`docs/MODEL_EVALUATION.md`).
2. Deploy over HTTPS (`docs/DEPLOYMENT.md`) and build the APK/iOS app with GitHub Actions (`docs/NATIVE_BUILDS.md`); test on physical phones.
3. Remaining real gaps: a per-result relevance indicator on search results, a formal Lighthouse + WCAG 2.2 AA audit, WebKit/iOS Safari tests.
(2026-11-13: added Scientific Visualization Lab — `/app/viz`, `vViz` in `screens-d.js`, linked from Experiments. Corpus-wide charts from real data only: reports/experiments by program, verified passages per report, evidence completeness, report timeline, oxygen/temperature/flow/pressure distributions. No backend changes — reuses `/api/experiments`, `/api/experiments/{id}`, `/api/reports`. 20/20 mobile E2E still pass.)
(2026-11-13: added Research Impact Dashboard — `/app/impact`, `GET /api/impact` (`api/__init__.py`) — real counts from this running DB (questions processed, evidence-grounded answers, active sessions) plus the retrieval benchmark read live from `eval/results.json`; and Judge Mode — `/app/judge`, no login needed, links to the dashboard and the existing `/app/demo` live-demo script. Full honest self-assessment against the 5 NASA Space Apps judging criteria, including what was deliberately NOT built and why (no fabricated usability study, no knowledge graph/contradiction detector at this corpus size): `docs/JUDGING_CRITERIA.md`.)
(2026-11-13: added a Combustion Research Hub — `/app/combustion` (`screens-e.js`), linked from Profile. Real NASA Physical Sciences Informatics (PSI) data: `GET /api/psi/search` (`mobile_routes.py`) proxies and 7-day-caches `https://psi.nasa.gov/geode-py/ws/repo/search` — a genuine public JSON API discovered by rendering PSI's search page with Playwright and capturing its own XHR calls, not a scrape of rendered HTML. New `psi_cache` SQLite table; `psi_opener` test seam mirrors `media_opener`. CSP extended: `img-src` now allows `psi.nasa.gov` (investigation thumbnails), `frame-src` now allows `www.youtube.com` (one embedded NASA ScienceCasts video). Historical fire-safety case studies (Apollo 1, Apollo 13, Mir) and 3 NASA Spinoff tech-transfer summaries are hand-written from the official NASA pages, each with its source link — not AI-invented. All 5 suites re-verified after this change: backend 89/89, desktop 19/19, mobile 20/20, Arabic 5/5, PWA 9/9.)
4. Extract more experiment values from figures (with human verification); import more NTRS reports.

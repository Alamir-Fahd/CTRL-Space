# CTRL+SPACE — final setup report

Written against what is actually installed and running on this machine on 2026-11-13, not a hypothetical stack. See `CLAUDE.md` for the owner's standing decisions this report follows.

## 1. Final technology stack

**Unchanged from the owner's existing decision — preserved, not replaced:**

| Layer | Choice | Why it stays |
|---|---|---|
| Backend | Python 3.11 + Flask | Modular app factory, 31 REST endpoints, already built and tested (90 backend tests) |
| Database | SQLite (`data/ctrlspace.db`) | Schema with in-place migrations in `db.py`; handles this corpus size (6 reports, 36 passages, 8 experiments) with no measurable latency (p95 < 1 ms locally) |
| Auth | Custom, hand-rolled | Password hashing, session cookies, rate limiting — already built, tested, and the subject of several passing security tests |
| Frontend (web + mobile web) | Vanilla HTML/CSS/JS, no build step | 28-screen mobile client + desktop site, i18n (Arabic RTL), PWA/offline, all tested |
| Native shell | Capacitor (Android built and run this session; iOS prepared, unbuilt — no Mac here) | Wraps the same web app; see `mobile/capacitor/` |
| AI | Provider-agnostic: Anthropic / OpenAI / Ollama, selected via `.env` | Works with none configured (retrieval-only mode) |
| Retrieval | BM25 (`services/search.py`) | Measured recall@6 = 0.958, MRR = 0.854 on a 16-question frozen benchmark; dense/embedding models are documented as not downloadable in the original build environment and were never silently claimed to work |

**Explicitly not adopted, and why:** FastAPI, Supabase (Postgres/Auth/Storage), Firebase, a vector database, Lucide/Framer Motion/D3.js/Three.js. Each was evaluated against the standing rule in `CLAUDE.md` — *"Keep Flask + SQLite + vanilla JavaScript... do not reverse without asking"* — and none has a documented technical requirement forcing a change: the current stack already passes every test, already runs natively on Android, and the data volume here (tens of reports, not millions) doesn't need a hosted Postgres cluster. This is the third prompt this session proposing a full-stack replacement (from-scratch rebuild, then Flutter/Dart, now FastAPI/Supabase/Firebase); each was flagged rather than silently done or silently ignored. If a real reason to switch exists, say so directly and I'll act on it — otherwise this report treats the question as settled.

## 2. Development environment — already verified working, this session

| Tool | Mandatory? | Verified version | Notes |
|---|---|---|---|
| Python | Mandatory | 3.11.9 | venv at `.venv/`, all deps installed via `pip install -r requirements.txt` |
| Node.js / npm | Mandatory only for the Android/iOS native shell | v24.16.0 / 11.13.0 | Not needed to run the web app itself |
| Git | Mandatory for version control | present (Git Bash) | No GitHub remote is configured for this local copy |
| VS Code | Recommended, not mandatory | `.vscode/tasks.json` + `launch.json` already configured | See `docs/VSCODE_CLAUDE_SETUP.md` |
| Android Studio + SDK + emulator | Mandatory only for native Android builds | SDK at `D:\Android\Sdk`, a `Pixel_8` AVD already exists | Already used this session to build and run the real debug APK |
| JDK | Mandatory for the Gradle Android build | 21 (Android Studio's bundled JBR) | Set `JAVA_HOME` to it before running `gradlew` |
| Xcode / macOS | Mandatory only for an iOS build | Not available (Windows machine) | iOS project files are prepared but unbuilt |
| Playwright + Chromium | Mandatory for the E2E test suites | installed | `python -m playwright install chromium` |

Installation commands for a machine that doesn't have these yet are in `README.md` (Python/venv) and `docs/NATIVE_BUILDS.md` (Android/iOS); this machine already has everything, so none of that needed to be re-run.

## 3. Firebase vs. Supabase decision

**Neither is adopted.** Reasoning, as requested:

- **Supabase** would replace a database and auth system that already exist, are already tested, and have no scaling problem at this data volume. Adopting it would mean migrating schema, rewriting every query in `db.py`/`services/`, and re-doing all 90 backend tests, for a platform-hosting benefit this project doesn't currently need (it isn't deployed yet at all — see `docs/DEPLOYMENT.md`).
- **Firebase** was already evaluated in a prior session (`docs/MASTER_CHECKLIST.md` §10) for Cloud Messaging and declined because there's no push-notification requirement yet; the app's own first-party notification system (in-app, DB-backed) already covers the current feature set.
- If a specific need appears later — e.g. real push notifications, or the database genuinely outgrowing SQLite after deployment — that's a concrete, scoped reason to revisit, not a wholesale swap today.

## 4. Complete API inventory

| API | Docs | Purpose | Required? | Auth | Key needed? | Integration point |
|---|---|---|---|---|---|---|
| NASA NTRS | ntrs.nasa.gov/api | Report metadata + PDF text (ingestion) | Mandatory (primary corpus) | None | No | `services/ingest.py` |
| NASA PSI Data Repository | psi.nasa.gov | Combustion investigation metadata | Mandatory for the Combustion Hub | None | No | `GET /api/psi/search` (`api/mobile_routes.py`), server-side proxy + 7-day cache |
| NASA Image and Video Library | images-api.nasa.gov | Illustrative imagery, cited | Optional (graceful offline fallback) | None | No | `GET /api/media/search` |
| Anthropic / OpenAI / Ollama | docs.anthropic.com / platform.openai.com/docs / docs.ollama.com | Generates answers from retrieved evidence | Optional — app runs retrieval-only without one | API key (Anthropic/OpenAI) or none (Ollama, local) | Yes for cloud providers, server-side only (`CTRLSPACE_AI_API_KEY`), never sent to the browser | `services/assistant.py` |
| Embeddings / vector search | — | Would support semantic retrieval | Not adopted | — | — | BM25 is the measured, working retrieval method; dense models were evaluated and found infeasible to download in the original offline build environment |
| Sentry | sentry.io | Server-side error monitoring | Optional | DSN | Yes, server-side only (`SENTRY_DSN`), silently skipped if absent | `backend/ctrlspace/__init__.py` |
| PostHog | posthog.com | Product analytics | Not adopted | — | — | Declined; the app has its own first-party, aggregate-only analytics (`/api/admin/analytics`) |
| Supabase / Firebase | — | Hosted DB/auth/storage/push | Not adopted | — | — | See §3 |

All AI and monitoring credentials are read server-side only, from `.env`, via `os.environ`. None is ever embedded in frontend JS, consistent with the CSP (`script-src 'self'`) and the project's non-negotiable rule against exposing keys.

## 5. Environment variables

`.env.example` (repo root) already lists every variable the code actually reads, each commented with purpose and mandatory/optional status: Flask env, database/storage paths, session lifetime, cookie security, the AI provider block (`CTRLSPACE_AI_*`), NTRS base URL. Added this round: `SENTRY_DSN` (was read by the code but undocumented in the file) and a one-line note that PSI/NASA Images need no key. No new variables were invented for services that aren't actually integrated (no `SUPABASE_*`, no `FIREBASE_*` — adding placeholders for unused services would misrepresent what the app does).

## 6. UI/UX

Design system is custom (CSS variables for color/spacing/radius/shadow, hand-rolled SVG icon set, CSS/SVG charts), deliberately not Lucide/Chart.js/ECharts/GSAP/Lottie/Framer Motion/D3/Three.js — each evaluated in an earlier session (`docs/MASTER_CHECKLIST.md` §10) and kept out in favor of the already-built, already-tested equivalents, per the same "don't replace working components" rule. Every screen has loading/empty/error/offline/retry states (verified by the E2E suites, not just claimed).

## 7. Screen validation

Not a manual one-off checklist — an automated one that actually runs: 90 backend tests, 19 desktop E2E journeys, 20 mobile app journeys (iPhone 14 + Pixel 7), 5 Arabic RTL journeys, 9 PWA installability checks. All green as of the last run today. `docs/TESTING.md` has the full breakdown.

## 8. Security

Password hashing, session cookies (`HttpOnly`, `SameSite`), rate limiting on auth and AI endpoints, strict CSP (`script-src 'self'`, no inline scripts/styles, no `eval`), input validation on every endpoint, audit logging for admin actions, no secrets in frontend code or Git history. Covered in `docs/SECURITY.md`.

## 9. Costs

**$0 mandatory.** SQLite, vanilla JS and BM25 retrieval have no hosting or usage cost. The only costs are opt-in: a cloud AI provider (Anthropic/OpenAI charge per token; Ollama is free but local) and, later, whatever hosting is chosen for deployment (`docs/DEPLOYMENT.md` — not yet deployed).

## 10. What's actually left to decide (owner input needed)

1. Confirm the architecture decision in §1 stands — or say what's actually wrong with the current stack that justifies a rewrite.
2. Pick and fund an AI provider if generated (not retrieval-only) answers matter for the demo.
3. Pick a deployment target when ready to go live.

Everything else in this report reflects what's already built, already tested, and already verified working — including on a real Android emulator this session.

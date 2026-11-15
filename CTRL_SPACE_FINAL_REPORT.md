# CTRL+SPACE — Final report

Date: 2026-11-12 · Version 5.2.0 — competition release + dedicated mobile application + Arabic + native build kit (stack: Flask, per owner decision) · Status: **working web application, ready for owner review. Not submitted anywhere.**

## 1. Overview
CTRL+SPACE (formerly FlameLab) is a web application that helps students and researchers search, understand and compare NASA research on combustion in microgravity. It answers only from verified passages of NASA reports, shows the report and page for every claim, and marks missing data instead of guessing. Challenge: NASA Space Apps 2026, *Flame in Freefall*. Not affiliated with or endorsed by NASA.

## 2. Technology stack
Python 3.10+ · Flask 3 · SQLite · BM25 search · pluggable AI provider (Anthropic / OpenAI / Ollama / none) · pdfplumber · plain ES-module frontend with CSS, no build step · Playwright for browser tests. Reasons and deviations from the phase documents: `docs/ARCHITECTURE.md`.

## 3. Architecture
Modular monolith: routes (`api/`) → services (search, assistant, experiments, auth, ingest) → SQLite. One process serves the API and the frontend. Diagram and ask sequence: `docs/ARCHITECTURE.md`.

## 4. Database
25 tables (schema v3, with in-place upgrades from v1 and v2). Scientific rules are SQL constraints: a reported value must cite a passage, numbers need units, missing values can't be stored as zero, field states are a fixed list. `backend/ctrlspace/db.py`.

## 5. API integrations
NASA NTRS (`/api/citations/{id}`, `/downloads`, PDF), rate-limited and retrying. AI providers over HTTPS from the server only. 58 API routes: `docs/API.md`.

## 6. AI capabilities
Evidence-grounded Q&A: retrieval of verified passages, hard evidence gate before any model call, 10 scientific prompt rules, JSON output, citation validation against retrieved IDs, insufficient-evidence responses, honest degradation when the provider fails. **No answer-quality evaluation with a real model has been run.**

## 7. Implemented features
Ask · Library (ranked search, filter, sort, pagination, details, NTRS/PDF links) · Experiments (8, sourced) · Compare (2–4, warnings, charts) · Accounts · Private notes · Collections with Markdown export · Admin: NTRS import, passage review, report approval, audit log, ingestion log, users · Light/dark themes · Responsive layout · PWA manifest.

**v2 added all 14 product screens:** splash, sidebar navigation, dashboard with recent research, research discovery with topics, evidence library, report pages tab, temperature field, research workspace (collections, saved items, notes, history), Learning Studio (5 lessons), Challenges (3, server-graded), Community (rooms, posts, replies, sharing, reporting, moderation), profile and settings, admin user management, experiment approval and analytics.

**Still not built:** email verification and password-reset emails, semantic/vector search, OCR, automatic experiment extraction, public API keys, real-time collaboration.

**v3** matched the screen-by-screen spec: real routes (`/research`, `/library/:id`…), launch with backend check, spec hero and home search, Discovery filters, Evidence Library, abstracts and keywords, oxygen basis and apparatus, measurements table with verification status, separate condition/measurement comparison with export, saved reports and experiments, experiment notes, sessions, privacy controls, data export, system health, extraction flagging, experiment rejection, failed-import reprocessing, richer lessons and challenges, post editing. Screen inventory and deliberate omissions: `docs/SCREENS.md`.

**Competition release (v4)** followed `docs/PRIORITIZATION.md`: structured evidence-first assistant (question analysis, evidence evaluation, coverage, sections, citation and numeric validation, retrieval-only structured fallback), three-level comparison, unit normalization that preserves originals, corpus-scoped research gaps, research brief, Demo mode with preflight, AI provider check, landing explanation. Model selection: `docs/MODEL_EVALUATION.md` (no unmeasured claims).

**Mobile app (v4.1):** installable PWA (service worker, offline reading of public research data, maskable icons, shortcuts, iPhone home-screen support, bottom tab bar, install button); Chromium installability check passes. Android APK paths (PWABuilder, Capacitor scaffold in `mobile/android/`) documented in `docs/MOBILE_APP.md` but not built here.

**Mobile application (v5):** dedicated mobile-first client at `/app` with 28 screens matching the mobile specification, on the same backend (schema v4: AI conversations, notifications, password resets, NASA image cache, feedback). Not a React Native app: npm is unavailable here, so a native client could not be built or tested (`docs/MOBILE_ARCHITECTURE.md`).

**v5.2:** Arabic interface with right-to-left layout (tested). Android APK and iOS packaging prepared as a Capacitor project with one-click GitHub Actions cloud builds (`docs/NATIVE_BUILDS.md`); no native package was built in this environment.

## 8. Phase status
| # | Phase | Status | Main open item |
|---|---|---|---|
| 01 | Audit and requirements | Complete | — |
| 02 | Architecture | Complete (with documented deviations) | Rendered diagrams |
| 03 | Database | Complete | Migration tool, PostgreSQL |
| 04 | NASA ingestion | Partially complete | Live NTRS run blocked by build environment |
| 05 | Backend API | Complete | OpenAPI file |
| 06 | Search | Complete | Larger corpus |
| 07 | RAG assistant | Partially complete | Choose provider; real-model evaluation |
| 08 | Experiments and comparison | Complete | Values only in figures not extracted |
| 09 | Frontend | Complete | Accessibility audit |
| 10 | Integration | Complete | Backend-down E2E case |
| 11 | QA | Complete for code; partial for science | Answer-quality evaluation |
| 12 | Performance and security | Partially complete | Load test, multi-instance |
| 13 | Deployment and docs | Partially complete | Not deployed |
| 14 | Demo and submission | Partially complete | Slides, video, official rules, owner approval |

Each phase has a requirement-by-requirement report in `docs/phases/`.

## 9. Testing
Backend 73/73 · Browser E2E 19/19 on consecutive runs, 0 console errors · Mobile device emulation (Pixel 7, Galaxy S9+) all passing · Retrieval: BM25 recall@6 0.958, MRR 0.854 (dense models and reranker not measured: unavailable offline) · Retrieval evaluation recall@6 0.958, MRR 0.854, 4/4 refusals · Legacy Phase 8 55/55. Details and defects fixed: `docs/TESTING.md`; raw output in `reports/`.

## 10. Security
Hashed passwords and session tokens, HttpOnly SameSite=Strict cookies, role checks, owner-scoped data, rate limits, strict CSP and headers, validated input, safe PDF storage, no admin data in public responses. Limitations: single process, no email verification, no virus scanning, HTTPS via reverse proxy. `docs/SECURITY.md`.

## 11. Performance
In-process latency (40 samples): search p50 0.42 ms, compare 0.69 ms, ask without provider 0.42 ms, index rebuild 1.3 ms for 34 passages. No load test; AI provider latency not measured.

## 12. Known limitations
Small corpus (6 reports, 4 with verified text, 34 passages). Live NTRS import and real AI answers never exercised in the build environment. Two Saffire records carry partial-copyright notices; only short excerpts are stored. The original logo contains the NASA insignia; the app uses a crop without it.

## 13. Installation · 14. How to run
See `README.md`: `pip install -r requirements.txt` → `cp .env.example .env` → `python run.py create-admin EMAIL "NAME"` → `python run.py serve` → open **http://127.0.0.1:8000** (API at `/api`, health at `/api/health`).

## 15. Browser testing evidence
Mobile: Chromium device emulation on Pixel 7 and Galaxy S9+ profiles, all steps passing (`reports/mobile_devices.txt`); no Android emulator was available in the build environment. Instructions for a real Android emulator: `docs/TESTING.md`.

Headless Chromium, desktop 1366×900 and mobile 390×844. Screenshots: `e2e/screenshots/01…11`. Android emulator: not used, and not applicable — this is a responsive web app/PWA, not an Android app.

## 16. ZIP contents
`backend/`, `frontend/` (incl. original logo and derived assets), `data/seed/corpus.json`, `tests/`, `e2e/` (with screenshots), `eval/`, `scripts/`, `docs/` (architecture, API, data, security, testing, deployment, user guide, demo, 14 phase reports, initial audit), `reports/` (raw test output), `README.md`, `.env.example`, `.gitignore`, `requirements.txt`, `run.py`, `wsgi.py`, this report, `CTRL_SPACE_PROGRESS.md`. Excluded: databases, imported PDFs, caches, secrets.

## 17. Remaining tasks (in priority order)
1. Run on your machine and walk through `docs/DEMO_SCRIPT.md`.
2. Choose an AI provider; ask the 12 evaluation questions and have a teammate check every citation.
3. Import the BASS-II Summary Report (`20210011385`) and verify its passages.
4. Check the official Space Apps rules, then make slides and the video.
5. Submit only after the team lead's explicit approval.

# CTRL+SPACE — master checklist of everything requested

Every requirement from every request in the project chat (website and app), with its real status, checked against the code and a fresh test run on 2026-11-13.

> **Correction (2026-11-13, Windows/VS Code verification pass):** several rows below previously said a feature was missing when the code already had it, fully wired and covered by the passing E2E suite. Re-verified by reading the actual frontend source and re-running the test suites on a real Windows machine (not just re-reading prior notes). Corrected rows are marked *(corrected)*. Two real Windows-only bugs were found and fixed in the process: Unicode console crashes in `e2e/*.py` on Windows' default cp1252 stdout (fixed with `sys.stdout.reconfigure(encoding='utf-8')`), and `scripts/run_e2e.sh` / the "Test: desktop E2E" VS Code task calling bare `python3` instead of the project's own `.venv`, which on Windows resolved to a Python with no dependencies installed (fixed to prefer `.venv/Scripts/python.exe` or `.venv/bin/python`). A real (if minor) UI bug was also found and fixed: the comparison screen's swipe-dot indicator never updated when swiping between experiment cards (`main.js` only wired the scroll listener for the onboarding carousel, not `#swipe`).

**Legend:** ✅ done and tested · 🟡 partly done (what’s missing is stated) · ❌ not done · 🔑 needs your credentials, server or device · ⛔ impossible in the build environment (no internet, no Android SDK, no Mac)

## 0. Verified run (2026-11-13, Linux, Chromium emulation, no screenshots)

| Check | Result |
|---|---|
| Server start, `/api/health` | ✅ ok, v5.2.0, 36 indexed passages |
| Live API probe (30 calls: research, search, ask, compare, gaps, auth, saved, collections, conversations, notifications, pages, manifest, service worker) | ✅ all expected; admin API correctly refuses non-admin (403); NASA Image Library 503 “requires internet” (expected offline) |
| Demo preflight | ✅ WARN only because no AI provider is configured |
| Backend tests | ✅ 88 / 88 |
| Desktop website journeys | ✅ 19 / 19, 0 console errors |
| Mobile app journeys | ✅ 20 / 20 on iPhone 14 and 20 / 20 on Pixel 7, 0 page errors |
| Arabic (RTL) journeys | ✅ 5 / 5 |
| Installable app (PWA) checks | ✅ 9 / 9 (Chromium installability: no errors) |
| Website on phone profiles (Pixel 7, Galaxy S9+) | ✅ all pass |
| Screen-width sweep 320, 360, 375, 390, 412, 430, 768, 1280 px (8 mobile screens each) | ✅ no horizontal overflow |
| iOS Safari engine (WebKit) | ⛔ not installed here: not tested |
| Physical phones, Android emulator | ⛔ not tested |

**Re-verified 2026-11-13 on Windows 11 (the documented dev machine, Python 3.11.9, fresh `.venv`):** backend 88/88, desktop E2E 19/19 (0 console errors), mobile app 20/20 on iPhone 14 (0 page errors), Arabic 5/5, PWA 9/9, demo preflight WARN-only (no AI provider). This also exercised the actual VS Code task/`run_e2e.sh` path, not just a direct Playwright invocation, and surfaced the two Windows bugs described above.

## 1. First requests: audit the NASA.zip and make the app

| Requirement | Status |
|---|---|
| Analyze the uploaded project archive (62 files, 14 phase folders, nested ZIPs) | ✅ audit in `docs/audit/` |
| Find conflicts (two stacks, four data models, missing code, no real NASA content, logo with NASA insignia) | ✅ documented |
| Run the archive’s own tests (Phase 8 engine 55/55) | ✅ |
| Build a working app with real NASA content | ✅ 6 NTRS reports, 36 verified passages, 8 experiments |
| Remove NASA insignia from the logo used in the app | ✅ cropped; 🔑 owner review of branding still advised |

## 2. Original 14 phases

| Phase | Status |
|---|---|
| 01 Requirements | ✅ |
| 02 Architecture | ✅ (diagrams as text, not rendered images) |
| 03 Database | ✅ SQLite schema v4 with in-place upgrades (no Alembic) |
| 04 NASA data ingestion | 🟡 code + scripted tests ✅; live NTRS import ⛔ untested; OCR ❌ |
| 05 Backend API | ✅ (no OpenAPI file; `docs/API.md` instead) |
| 06 Search | ✅ BM25 with synonyms; recall@6 0.958, MRR 0.854 |
| 07 AI assistant | 🟡 pipeline ✅; real AI provider 🔑 never run |
| 08 Experiments / comparison | ✅ (many values only in figures: “Not extracted”) |
| 09 Frontend | ✅ vanilla JS (not React, by decision) |
| 10 Testing | ✅ |
| 11 Scientific validation | 🟡 code ✅; expert review of science 🔑 |
| 12 Security / performance | 🟡 secure sessions, CSP, rate limits ✅; load and penetration tests ❌ |
| 13 Deployment | ❌ 🔑 not deployed (guide in `docs/DEPLOYMENT.md`) |
| 14 Submission (slides, video, rules check) | ❌ 🔑 needs the team; nothing submitted |

## 3. Screen-by-screen website spec (Angular/Node/MongoDB named)

| Requirement | Status |
|---|---|
| Angular + Node + MongoDB stack | ❌ by owner decision (Flask kept) |
| Launch/splash with health check and retry | ✅ |
| Dashboard, Research discovery, Evidence library, Report details | ✅ |
| Research assistant with evidence and insufficient-evidence state | ✅ |
| Experiments, Experiment details, Compare (2–4) with warnings and export | ✅ |
| My Research (saved, collections, notes, history) | ✅ |
| Learning Studio, Challenges, Community (rooms, posts, replies, reports) | ✅ |
| Accounts, profile, settings, sessions, data export, delete account | ✅ |
| Admin (overview, imports, evidence review, experiments, moderation, users, analytics, audit log) | ✅ (desktop web console) |
| Email verification and password-reset emails | ❌ no email service (admin-issued reset links instead ✅) |
| Search suggestions and search history | ✅ *(corrected)* recent searches + topic/program/material autocomplete (`main.js` `suggestions()`/`#sugbox`), covered by a passing E2E check |
| Simple/scientific answer modes | ❌ |
| Creating/joining rooms | ❌ (4 fixed rooms) |

## 4. Competition release (“final quality” instructions)

| Requirement | Status |
|---|---|
| Prioritization matrix (must/should/nice) | ✅ `docs/PRIORITIZATION.md` |
| AI provider configuration (Anthropic, OpenAI, Ollama) | ✅ code; 🔑 live check never run |
| Provider verification command (`check-ai`, admin button) | ✅ |
| Question analysis → retrieval → evidence evaluation → structured answer | ✅ |
| Answer sections: direct answer, explanation, evidence, conditions, sources, limitations, coverage | ✅ (AI sections 🔑 need provider) |
| Citation validation + numeric grounding | ✅ |
| Insufficient-evidence handling | ✅ |
| Retrieval-only fallback, clearly labelled | ✅ |
| Variable normalization keeping original units, value types | ✅ |
| Comparison levels 1–3, statement types, no causal claims, context warnings | ✅ |
| Research gap detector (corpus-scoped, typed gaps) | ✅ |
| Research brief generator | ✅ |
| Demo mode + preflight | ✅ |
| Landing: problem, solution, innovation, impact, “how it works” | ✅ |
| Semantic search (bge-m3 / MiniLM) | ⛔ models not downloadable; benchmark script ready |
| Hybrid retrieval, cross-encoder reranking | ⛔ same |
| Model evaluation with measurements | 🟡 BM25 measured ✅; dense models ⛔; LLMs 🔑 |
| Automatic experiment extraction from figures | ❌ |
| Advanced visualizations | 🟡 simple bars and completeness charts only |
| Knowledge graph, flame explorer, AI tutor, AI quizzes | ❌ (nice-to-have) |

## 5. “Run the app in the emulator”

| Requirement | Status |
|---|---|
| Android emulator run | 🟡 *(corrected 2026-11-13)* depends on the machine: the original cloud sandbox genuinely had no SDK/KVM (Chromium device emulation was the real substitute there); this Windows dev machine has Android Studio, SDK, emulator and a Pixel_8 AVD, and the real debug APK was built and run on it — see §8 |
| Mobile defects found and fixed (zoom-out overflow, small checkboxes, scroll jumps) | ✅ |

## 6. Mobile app (first mobile spec, 15 screens + mockups)

| Requirement | Status |
|---|---|
| Separate mobile-first app, not a shrunk website | ✅ `/app` |
| Splash, onboarding, auth, home, discovery, details, assistant, library, explorer, comparison, workspace, learning, community, profile/settings, offline | ✅ all |
| Bottom navigation, safe areas, large touch targets, no overflow | ✅ |
| Conversation history, export, citation validation | ✅ |
| NASA Image and Video Library (official API) with source, ID, link, date | ✅ code; 🔑 live needs internet (tested with recorded data) |
| Offline downloads, offline indicator, reconnection, sync | ✅ (IndexedDB downloads; queued saves/notes sync on reconnect) |
| 20 mockups before implementation | 🟡 replaced by a gallery of 28 real screenshots of the built app |
| Physical device testing | ⛔ |

## 7. “Ultimate” mobile spec (28 pages, React Native/Expo)

| Requirement | Status |
|---|---|
| Architecture report with feature classification | ✅ `docs/MOBILE_ARCHITECTURE.md` |
| React Native + Expo + TypeScript client | ❌ ⛔ npm unavailable; not built |
| All 28 pages (incl. search results, AI analysis, collections, notes editor, edit profile, about, help, demo) | ✅ |
| Show/hide password, confirm password, terms, research interests | ✅ |
| Remember me | ❌ (sessions last 12 hours) |
| Google / Microsoft sign-in | ❌ 🔑 not configured |
| Password recovery without account enumeration | ✅ (admin-issued one-time link) |
| AI: copy, share, regenerate, feedback, follow-ups, history, export, report-scoped questions | ✅ |
| Streaming responses | ❌ |
| “AI insight” card on Home | ❌ (would need a provider) |
| Space-wide categories (astronomy, Earth science…) | ❌ no such data in the corpus; not invented |
| Pagination / infinite scroll | 🟡 fixed page sizes |
| Rich-text notes | 🟡 plain text with autosave |
| Profile photo | ❌ (initial avatar) |
| Notification center (real events, read/unread, preferences) | ✅; delete single notification ❌; push ❌ |
| Theme: dark, light, system | ✅ |
| Language setting | ✅ English + Arabic |
| Deep links, Android back, history | ✅ (URL routes); iOS gestures ⛔ untested |
| NASA Earthdata / Open APIs | ❌ not relevant to the corpus |

## 8. APK and iOS app

| Requirement | Status |
|---|---|
| Installable app (PWA) with icon, splash, standalone, shortcuts | ✅ |
| Capacitor Android + iOS project with icons and splash | ✅ prepared; Android *(corrected 2026-11-13)* actually built and run — this machine has Android Studio, SDK, emulator and a Pixel_8 AVD, which earlier sessions assumed were unavailable. `npx cap add android` + `./gradlew assembleDebug` produced a real debug APK, installed and launched on the emulator via `adb`: booted past splash, connected to the Flask backend over the emulator's `10.0.2.2` host alias, showed real seeded stats (6 reports/36 passages/8 experiments/5 lessons), and opened a real NTRS report detail with its honest “abstract not stored” message. iOS still ⛔ not built here (no Mac/Xcode). |
| One-click cloud builds (GitHub Actions: APK, iOS simulator) | ✅ prepared (valid YAML); 🔑 untested until first run |
| Signed iPhone build / App Store / Play Store release | 🔑 needs Apple Developer account / release keystore |

## 9. Arabic

| Requirement | Status |
|---|---|
| Language switch (onboarding + settings) | ✅ |
| Full RTL layout, Arabic font, mirrored icons | ✅ |
| Interface fully translated (measured on every screen) | ✅ |
| NASA sources kept verbatim in English | ✅ |
| Arabic questions to the assistant | ❌ retrieval matches English; app asks for English questions |

## 10. Latest spec: professional mobile upgrade (libraries, services, UX)

| Requirement | Status |
|---|---|
| Keep Flask + vanilla JS | ✅ |
| Lucide icons | ❌ custom consistent SVG icon set instead |
| Chart.js / Apache ECharts | ❌ lightweight CSS/SVG charts instead |
| GSAP animations, Lottie | ❌ |
| Dexie.js | ❌ (IndexedDB used directly ✅) |
| Workbox | ❌ (hand-written service worker ✅) |
| Playwright mobile testing | ✅ |
| Lighthouse audits | ❌ not run |
| Sentry | 🟡 optional server-side hook (`SENTRY_DSN`) 🔑 untested; no frontend Sentry |
| PostHog analytics, Firebase push, Web Push, geolocation | ❌ |
| Web Share API | ✅ |
| Fonts Inter + Space Grotesk/Manrope | 🟡 Inter ✅; Chakra Petch used for headings |
| Design tokens, components, dark/light/system | ✅ |
| Bottom nav with “My Research” as 5th tab | ✅ *(corrected)* 5th tab is `/app/workspace`, labelled “My Research” (`index.html` tabbar); confirmed by the PWA test’s “Bottom tab bar (5 tabs)” check |
| Visually distinct AI tab | ✅ *(corrected)* raised circular icon with a blue/violet gradient and its own glow, floating above the bar (`.tab-ai` in `app.css`) |
| Search suggestions, relevance indicators on results | 🟡 *(corrected)* search suggestions ✅ (see §3); a per-result relevance score/indicator is still ❌ not shown on result cards (results are sorted by relevance, but the sort order isn’t surfaced visually) |
| Report viewer with page navigation | 🟡 Pages tab lists extracted pages |
| AI: stop generation | ✅ *(corrected)* `AbortController` wired end to end (`ask()`/`stopgen` in `main.js`, stop button in `screens-b.js`), covered by the E2E “AI centerpiece … stop generation” check |
| AI follow-up actions (explain finding, show evidence, compare, limitations, research questions, save) | ✅ *(corrected)* all six are dedicated chip buttons (`factions()` in `screens-b.js`: `fexplain`, `fevidence`, `fcompare`, `flimits`, `fquestions`, `saveans`), not just suggested questions |
| AI vs. original evidence clearly distinguished | ✅ |
| Swipeable side-by-side comparison cards | ✅ *(corrected)* scroll-snap card carousel with dot indicator (`.swipe`/`.xcard`/`.sdots`), not a table; the dot indicator had a bug (never updated on swipe) found and fixed in this pass |
| Pull-to-refresh, page transitions | ✅ *(corrected)* pull-to-refresh gesture on list screens (`#ptr`, touch handlers in `main.js`) and a page-enter animation that respects `prefers-reduced-motion` (`#view.enter` in `app.css`); code-verified by reading the implementation, not by an automated gesture test |
| Skeletons, toasts, bottom sheets, progress, reduced motion | ✅ |
| Loading/empty/error/offline/retry states | ✅ |
| Charts: units, missing-data handling, value types | ✅; touch-interactive/expandable charts ❌ |
| Background Sync API | ❌ (sync on reconnect ✅) |
| Internet vs. backend availability distinguished | ✅ |
| WCAG 2.2 AA audit | ❌ no formal audit (labels, focus, contrast tokens, touch targets checked in tests) |
| Viewport tests 320–430 px, tablet, desktop | ✅ |
| Android Chrome / iOS Safari on devices, orientation tests | ⛔ / ❌ |
| Reports: API integration ✅ `docs/API.md`; accessibility ❌; performance 🟡 latency figures only; testing ✅ `docs/TESTING.md`; screenshots ✅ `docs/gallery/` | mixed |

## 11. Still open (shortest path to “complete”)

1. 🔑 Configure an AI provider, run `check-ai`, evaluate answers with a teammate.
2. 🔑 Deploy over HTTPS; build APK/iOS in GitHub Actions; test on physical phones (Android Chrome, iOS Safari).
3. ❌ Remaining latest-spec UX: per-result relevance indicator, dedicated Lighthouse/WCAG audit reports (manual spot-checks exist; no formal audit run).
4. ❌ Lighthouse + accessibility audit reports.
5. 🔑 Slides, demo video, official rules check, submission.

(Items 3 previously also listed stop generation, swipeable comparison, pull-to-refresh, page transitions, the “My Research” tab and search suggestions — all six turned out to already be implemented; see the corrections above.)

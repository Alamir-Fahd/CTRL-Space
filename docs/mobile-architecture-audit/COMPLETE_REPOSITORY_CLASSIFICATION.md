# Complete repository classification

Read-only audit, 2026-11-14. Full file tree below (generated/build artifacts — `node_modules/`, `.venv/`, `__pycache__/`, Android's `.gradle/` and `app/build/`, Android's generated `res/` resource folders — are summarized as counts, not listed file-by-file, per the audit request's instruction to group generated artifacts separately). Every application-owned source file is listed individually.

## Repository tree (application-owned files)

```
ctrl-space/
├── .env, .env.example                          configuration (not committed; .env excluded by .gitignore)
├── .github/workflows/
│   ├── android-apk.yml                         CI: build + upload a debug APK (needs an HTTPS server_url input)
│   └── ios-build.yml                           CI: build + upload an unsigned iOS Simulator build (macOS runner)
├── .gitignore
├── .vscode/                                    editor config (extensions, launch, settings, tasks)
├── CLAUDE.md, README.md, CTRL_SPACE_FINAL_REPORT.md, CTRL_SPACE_PROGRESS.md
├── requirements.txt, run.py, wsgi.py            Python backend entry points
│
├── backend/ctrlspace/                           ── BACKEND (Flask) ──
│   ├── __init__.py                              app factory; serves both clients (see MOBILE_ARCHITECTURE_MAP.md)
│   ├── db.py                                    SQLite schema + migrations
│   ├── api/{__init__,intelligence_routes,mobile_routes,platform}.py
│   └── services/{assistant,auth,experiments,ingest,intelligence,search}.py
│
├── frontend/                                    ── DESKTOP WEB CLIENT + SHARED ASSETS ──
│   ├── index.html, sw.js, manifest.webmanifest   desktop entry + SHARED service worker/manifest (see note below)
│   ├── css/app.css                               desktop-only stylesheet (14 responsive breakpoints)
│   ├── js/{app.js,ui.js,views-research.js,views-platform.js,views-extra.js}   desktop-only screens/logic
│   ├── js/api.js                                 ⚠ SHARED: imported by both frontend/js/app.js AND frontend/app/js/core.js
│   ├── assets/{hero.jpg,ctrl-space-logo-original.jpeg,icon-192.png,icon-512.png,icon-maskable-512.png,apple-touch-icon.png}   SHARED icon/image assets
│   │
│   └── app/                                      ── MOBILE CLIENT (the actual mobile application) ──
│       ├── index.html                            mobile entry point (loaded for any unmatched /app/* path)
│       ├── app.css                                mobile-only stylesheet (1 @media query — prefers-reduced-motion only)
│       └── js/
│           ├── core.js                            state, routes, API import, shared UI primitives, icon set
│           ├── main.js                            boot/splash sequence, router, event delegation, action handlers
│           ├── i18n.js                             English/Arabic strings + RTL
│           └── screens-{a,b,c,d,e}.js              screen view-functions (home, auth, research, assistant, experiments, profile, combustion hub, etc.)
│
├── mobile/capacitor/                             ── NATIVE APP SHELL (Capacitor) ──
│   ├── package.json, package-lock.json            Capacitor 6.2.3 toolchain + npm scripts (android/ios/apk/icons)
│   ├── capacitor.config.json                      ⚠ appId, webDir="www", server.url=http://10.0.2.2:8000/app (emulator-only), cleartext=true
│   ├── www/index.html                              bundled fallback — literally an error page ("server could not be reached"), NOT the app
│   ├── assets/{icon-*.png,splash*.png}             source art for `npx @capacitor/assets generate`
│   └── android/                                    generated native Android project (ANDROID ONLY — see below)
│       ├── app/build.gradle, variables.gradle, settings.gradle, build.gradle, capacitor.settings.gradle, gradlew(.bat)
│       ├── app/src/main/AndroidManifest.xml         applicationId com.ctrlspace.app, 1 permission (INTERNET), 1 activity
│       ├── app/src/main/java/com/ctrlspace/app/MainActivity.java   Capacitor's generated bridge Activity (no custom native code added)
│       ├── app/src/main/assets/capacitor.config.json   config baked into the built APK — confirmed identical to the root config (same emulator-only server.url)
│       ├── app/src/main/assets/public/index.html       the APK's bundled page — confirmed identical 3-line error fallback
│       ├── app/src/androidTest/.../ExampleInstrumentedTest.java, app/src/test/.../ExampleUnitTest.java   Capacitor's stock placeholder tests, never written for this app
│       ├── capacitor-cordova-android-plugins/          Cordova-plugin compatibility shim required by Capacitor 6 (no Cordova plugins actually used)
│       └── app/build/outputs/apk/debug/app-debug.apk    a real, built debug APK (3,747,776 bytes, 2026-11-13 16:30)
│       (no ios/ directory exists anywhere in the repository)
│
├── data/
│   ├── ctrlspace.db(-shm,-wal)                   SQLite database (gitignored)
│   ├── originals/*.pdf                            4 downloaded NTRS source PDFs (gitignored)
│   └── seed/{corpus.json,learning.json}           seed data definitions
│
├── eval/{results.json,benchmark_results.json,retrieval_eval.json}   AI retrieval evaluation output
├── reports/*.txt, *.json                          saved output from past test/benchmark runs (not test code itself)
│
├── tests/test_backend.py                          BACKEND unit tests (unittest, isolated test DB)
├── e2e/
│   ├── test_e2e.py                                 DESKTOP browser E2E (Playwright)
│   ├── mobile_app_test.py, mobile_ar_test.py, mobile_devices.py, mobile_audit.py, pwa_test.py   MOBILE CLIENT E2E (Playwright, device emulation)
│   └── screenshots/                                 E2E-generated screenshots (build artifact, not source)
├── scripts/{run_e2e.sh, evaluate.py, benchmark_retrieval.py}
│
└── docs/                                           64 markdown files: current reference docs (API.md, ARCHITECTURE.md, DATA_SOURCES.md,
                                                     SECURITY.md, DEPLOYMENT.md, MOBILE_APP.md, MOBILE_ARCHITECTURE.md, NATIVE_BUILDS.md, SCREENS.md, …),
                                                     plus dated/point-in-time snapshots in docs/phases/ (14 files), docs/audit/ (6), docs/final-audit/ (1),
                                                     docs/fixes/ (6), docs/qa/ (13), docs/strategic-audit/ (1), and this audit's own folder.
                                                     docs/gallery/ holds 29 screenshot PNGs used by README/docs, not source code.
```

### ⚠ Note: one directory that is NOT application code

`{backend/ctrlspace/services,backend/ctrlspace/api,frontend/js,frontend/css,frontend/assets,data/seed,tests,e2e,docs/phases,scripts}` — a literal, empty directory at the repository root, dated 2026-11-12 17:32 (the project's very first setup timestamp). Its name is the unexpanded text of a brace-expansion `mkdir` command that evidently ran in a shell that didn't support bash-style brace expansion, creating one directory with the whole pattern as its literal name instead of ~10 separate directories. It contains only one empty subdirectory (`ctrlspace/`) and no files. **Not deleted** per this audit's read-only rule — flagged in `ARCHITECTURE_ISSUES_AND_RECOMMENDATIONS.md` as safe, low-priority cleanup for a future (non-audit) pass.

## Generated / build artifacts (grouped, not itemized)

| Path | What it is | Tracked? |
|---|---|---|
| `.venv/` | Python virtual environment (backend dependencies) | gitignored |
| `mobile/capacitor/node_modules/` | npm dependencies for the Capacitor CLI/SDK | **not** in `.gitignore` — see issues doc |
| `mobile/capacitor/android/.gradle/`, `android/app/build/` (except the one APK listed above) | Gradle build cache and intermediate outputs | not committed in practice (standard Android `.gitignore` inside `android/.gitignore` covers this) |
| `mobile/capacitor/android/app/src/main/res/mipmap-*/`, `drawable-*/` | Generated app icons/splash images at each density, produced by `npx @capacitor/assets generate` from `mobile/capacitor/assets/` | generated, source is `mobile/capacitor/assets/` |
| `**/__pycache__/`, `*.pyc` | Python bytecode cache | gitignored |
| `data/ctrlspace.db*`, `data/originals/*.pdf` | Runtime database and downloaded source PDFs | gitignored |
| `e2e/screenshots/`, `docs/gallery/*.png`, `reports/*` | Test/benchmark output artifacts, not hand-written source | not gitignored, but not source code either |

## Classification table

| File / Folder | Purpose | Technology | Category | Used by Mobile App? | Status |
|---|---|---|---|---|---|
| `backend/ctrlspace/**/*.py` | API, auth, search, ingest, AI assistant, DB | Python/Flask | **B. Backend** | Yes — exclusively | Current |
| `run.py`, `wsgi.py` | Process entry points | Python | **B. Backend** | Yes (indirectly) | Current |
| `frontend/app/index.html`, `app.css`, `js/*.js` | The mobile client itself | Vanilla JS/CSS/HTML | **A. Mobile application** | Yes — this *is* the mobile app | Current |
| `frontend/js/api.js` | HTTP client for all `/api/*` calls | Vanilla JS (ES module) | **C. Shared** | Yes — imported directly by `frontend/app/js/core.js:2` | Current |
| `frontend/sw.js` | Service worker: caches both clients' shells, offline reads | Vanilla JS | **E. PWA/offline** (also C. Shared) | Yes — registered by `frontend/app/js/main.js:265` | Current |
| `frontend/manifest.webmanifest` | PWA install manifest | JSON | **E. PWA** (also C. Shared) | Yes — linked from `frontend/app/index.html:11` | Current |
| `frontend/assets/*` | Icons, hero art, logo | Images | **C. Shared** | Yes — referenced by both clients' CSS/HTML | Current |
| `frontend/index.html`, `css/app.css`, `js/{app,ui,views-*}.js` | The desktop browser site | Vanilla JS/CSS/HTML | **D. Web-only** | No | Current, but separate product from the mobile app |
| `mobile/capacitor/capacitor.config.json` | Native shell config (appId, webDir, server URL) | JSON | **A. Mobile application** config | Yes — defines how the native shell loads the app | Current, but `server.url` is an emulator-only address (see issues doc) |
| `mobile/capacitor/android/**` (excl. generated) | Generated native Android project | Gradle/Java/XML | **A. Mobile application** (native wrapper) | Yes | Current, builds successfully |
| `mobile/capacitor/www/index.html` | Bundled fallback page | HTML | **E. PWA/WebView** | Only if the server is unreachable | Current, intentionally minimal |
| `mobile/capacitor/android/.../MainActivity.java` | Capacitor's generated bridge Activity | Java | **A. Mobile application** (native) | Yes | Current, unmodified Capacitor boilerplate |
| `mobile/capacitor/android/.../Example*Test.java` | Capacitor's stock placeholder test templates | Java | **F. Testing** | No — never adapted for this app | Legacy/unused template, harmless |
| `tests/test_backend.py` | Backend unit tests | Python/unittest | **F. Backend tests** | No (tests the backend directly) | Current, 93 tests passing |
| `e2e/test_e2e.py` | Desktop browser E2E | Python/Playwright | **F. Browser E2E tests** | No — targets `frontend/`, not `frontend/app/` | Current |
| `e2e/mobile_app_test.py`, `mobile_ar_test.py`, `mobile_devices.py`, `pwa_test.py`, `mobile_audit.py` | Mobile client E2E (device-emulated, real Android/iPhone/Pixel/Galaxy viewports+UAs) | Python/Playwright | **F. Mobile tests** | Yes — directly tests `frontend/app/` | Current |
| `docs/*.md` (19 top-level) | Current living reference docs | Markdown | **G. Documentation** | N/A | Current |
| `docs/phases/PHASE_*.md` (14) | Dated, point-in-time development-phase snapshots | Markdown | **G. Legacy/historical** | N/A | Intentionally frozen, not updated |
| `docs/audit/*.md`, `docs/final-audit/*.md` | Prior dated audit snapshots (2026-11-12/13) | Markdown | **G. Legacy/historical** | N/A | Intentionally frozen |
| `docs/fixes/*.md`, `docs/qa/*.md` | Prior session work logs | Markdown | **G. Legacy/historical** | N/A | Intentionally frozen |
| `docs/strategic-audit/STRATEGIC_AUDIT.md` | Prior strategic audit (2026-11-14, same day) | Markdown | **G. Documentation** | N/A | Current |
| `{backend/...}` junk directory | Accidental `mkdir` brace-expansion artifact | — | **G. Legacy/unused** | No | Empty, harmless, flagged for cleanup |
| `.github/workflows/android-apk.yml` | CI: cloud Android build | YAML | **A. Build config** | Yes | Current, unexercised in this environment (no git remote — see Android/iOS doc) |
| `.github/workflows/ios-build.yml` | CI: cloud iOS build | YAML | **A. Build config** | Would be, for iOS | Current, unexercised (needs a GitHub remote + macOS runner) |
| `data/`, `eval/`, `reports/`, `scripts/` | Runtime DB, AI eval output, saved test-run logs, dev scripts | Python/JSON/txt | **B. Backend-adjacent** | No | Current |

## File counts (hand-counted, no `.git` in this repo — see `ARCHITECTURE_ISSUES_AND_RECOMMENDATIONS.md`)

| Category | Count |
|---|---|
| Mobile application client (`frontend/app/`) | 10 files |
| Desktop web client (`frontend/` root + `js/` + `css/`, excl. shared) | 10 files |
| Shared frontend files (`js/api.js`, `sw.js`, `manifest.webmanifest`, `assets/*`) | 9 files |
| Backend (`backend/` `.py` + `run.py` + `wsgi.py`) | 14 files |
| Capacitor source, excluding `node_modules`/generated build/`.gradle` (config + Android project files) | 17 files |
| Tests (`tests/` + `e2e/`, excluding generated screenshots) | 7 files |
| Documentation (`docs/**/*.md`) | 64 files |
| Root-level config/docs | 10 files |

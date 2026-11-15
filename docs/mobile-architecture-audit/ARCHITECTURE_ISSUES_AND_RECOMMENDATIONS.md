# Architecture issues and recommendations

Read-only audit, 2026-11-14. No fixes were applied — per this audit's own rule, this phase reports and recommends only. Priorities: **Critical** (blocks the app from working for its intended audience), **High** (should be fixed before the next real milestone — e.g. judging, physical-device testing, or a release build), **Medium** (should be fixed, not urgent), **Low** (cosmetic/cleanup).

## Issues found, with evidence

### 1. The built Android app cannot be installed on a real phone or shown to anyone outside this dev machine — CRITICAL
- **Evidence:** `mobile/capacitor/capacitor.config.json` and the config baked into the built APK (`mobile/capacitor/android/app/src/main/assets/capacitor.config.json`) both set `server.url` to `http://10.0.2.2:8000/app` — the Android *emulator's* alias for the host machine's localhost. It is meaningless outside an emulator talking to a locally-running dev server.
- **Affected files:** `mobile/capacitor/capacitor.config.json`.
- **Risk:** Anyone who installs the current `app-debug.apk` on a physical device, or anyone without this exact dev setup running, sees only the bundled error page (`www/index.html`): *"The server... could not be reached."* This is the single biggest gap between "builds successfully" and "demonstrable to a judge on a real phone."
- **Recommended solution:** deploy the Flask backend somewhere reachable over HTTPS (`docs/DEPLOYMENT.md` already documents how), set `server.url` to that address, rebuild. This is a one-line config change plus a deployment step — not a restructuring.
- **Priority:** High if a physical-device demo is planned; the emulator-based demo already works today.
- **Restructuring required:** No.

### 2. This repository has no version control — HIGH
- **Evidence:** `git rev-parse --is-inside-work-tree` → `fatal: not a git repository (or any of the parent directories): .git`. A `.gitignore` file exists and is reasonably well-formed, but there is no `.git` directory anywhere.
- **Affected files/folders:** the whole repository.
- **Risk:** No commit history, no rollback safety net, no diffs to review, and — concretely for this audit — **neither CI workflow can run** (`.github/workflows/android-apk.yml`, `ios-build.yml` both require a GitHub remote to dispatch against). The iOS build path that exists on paper is unreachable until this is fixed.
- **Recommended solution:** `git init`, an initial commit, push to a GitHub remote. Outside this audit's scope to perform (a repository-initialization action, not a mobile-architecture fix), but worth flagging as the actual blocker behind "can CI build iOS" rather than treating it as a Capacitor/iOS problem.
- **Priority:** High — it blocks a documented, otherwise-working iOS path.
- **Restructuring required:** No — purely additive.

### 3. Capacitor toolchain is two major versions behind latest — MEDIUM
- **Evidence:** `npx cap doctor` (run this pass): installed `6.2.3` across `cli`/`core`/`android`/`ios`; latest is `8.6.2`.
- **Affected files:** `mobile/capacitor/package.json`.
- **Risk:** Missing two major versions of bug fixes/security patches; future Capacitor plugins may require 7.x+. No evidence of an active problem today — `cap doctor` reports a clean, internally-consistent install.
- **Recommended solution:** plan a Capacitor major-version upgrade as ordinary maintenance, with its own testing pass (major version bumps can change native project structure) — not an audit-phase action.
- **Priority:** Medium — not urgent, but will compound the longer it's deferred.
- **Restructuring required:** No, an upgrade, not a rebuild.

### 4. `.gitignore` doesn't exclude `mobile/capacitor/node_modules/` — MEDIUM
- **Evidence:** `.gitignore` excludes `.venv/` (the Python equivalent) but has no `node_modules` entry.
- **Affected files:** `.gitignore`.
- **Risk:** Combined with issue #2 (no git yet), the first real commit would check in the entire npm dependency tree if this isn't fixed first.
- **Recommended solution:** add `node_modules/` to `.gitignore` before the first commit.
- **Priority:** Medium (time-sensitive relative to issue #2, not on its own).
- **Restructuring required:** No.

### 5. No native device-capability integration — LOW / INFORMATIONAL, not necessarily a defect
- **Evidence:** zero matches for `Capacitor.*` bridge calls or `@capacitor/<plugin>` imports anywhere in `frontend/app/js/*.js`; `AndroidManifest.xml` requests only `INTERNET`.
- **Affected files:** the whole mobile client.
- **Risk:** none inherently — the app doesn't currently need camera/push/native-share to function, and the PWA already has a working installability story. This becomes a real gap only if a specific native feature (e.g. push notifications for new NASA data, native share sheet for research findings) is actually wanted.
- **Recommended solution:** if/when a specific native capability is desired, add the matching Capacitor plugin deliberately (e.g. `@capacitor/share`, `@capacitor/push-notifications`) rather than as a blanket "add native features" effort.
- **Priority:** Low — track as a product decision, not a defect.
- **Restructuring required:** No.

### 6. iOS has never been scaffolded — BLOCKED (environment), not a defect
- **Evidence:** no `ios/` directory exists; `@capacitor/ios` is installed as a dependency but `npx cap add ios` has never run.
- **Risk:** iOS is currently completely unverified — no bundle ID, no Info.plist, nothing to inspect.
- **Recommended solution:** run `npx cap add ios` on a machine with Xcode (or via the already-written `ios-build.yml` once a GitHub remote exists, per issue #2), then genuinely build and test before claiming any iOS readiness.
- **Priority:** Low until an iOS deliverable is actually required for the competition; High the moment it is.
- **Restructuring required:** No — the tooling and CI path are already in place; execution is what's missing.

### 7. Cosmetic: one stray, empty, accidentally-named directory — LOW
- **Evidence:** `{backend/ctrlspace/services,backend/ctrlspace/api,frontend/js,...}` at the repository root — an unexpanded brace-pattern from an early `mkdir` command, dated the project's first setup timestamp (2026-11-12 17:32). Empty except for one empty subdirectory.
- **Risk:** none — purely cosmetic clutter.
- **Recommended solution:** delete it in a future non-audit pass (explicitly not done here, per this audit's "do not delete" rule).
- **Priority:** Low.
- **Restructuring required:** No.

### 8. No Android release signing configuration yet — LOW, expected at this stage
- **Evidence:** `mobile/capacitor/android/app/build.gradle`'s `release` build type has no `signingConfig` block.
- **Risk:** none for development/demo use (debug builds work fine, as verified). Would block a real Play Store submission.
- **Recommended solution:** generate a release keystore and signing config when an actual release build is needed — not before.
- **Priority:** Low (Not Applicable until a release is actually planned).
- **Restructuring required:** No.

## Subsystem classification

| Subsystem | Classification | Why |
|---|---|---|
| Backend (Flask + SQLite, `backend/ctrlspace/`) | **KEEP** | Correctly shared by both clients; no mobile-specific defect found; already the subject of a separate architecture KEEP decision in `docs/strategic-audit/STRATEGIC_AUDIT.md` §1. |
| Mobile client (`frontend/app/`) | **KEEP** | Genuinely mobile-first (fluid single-column layout, safe-area padding, bottom tab bar, 0 width-based breakpoints because none are needed), installable PWA, 21/21 mobile E2E tests passing as of the last full regression. |
| Desktop web client (`frontend/`, excl. `app/`) | **KEEP** | Correctly isolated as a separate product; not mixed into the mobile client; serves a legitimate separate purpose (browser/desktop users). |
| Shared files (`js/api.js`, `sw.js`, `manifest.webmanifest`, `assets/*`) | **KEEP** | Sharing these is the architecturally correct choice, not an accident — see `WEB_VS_MOBILE_ANALYSIS.md`. |
| Capacitor Android shell | **IMPROVE** | Builds and runs correctly; one config value (`server.url`) must change before it's useful outside an emulator. A config fix, not a rebuild. |
| Capacitor iOS shell | **BLOCKED** | No macOS/Xcode available in this environment; tooling and CI path already exist and are well-formed. |
| Android release signing | **NOT APPLICABLE** (yet) | Not needed until an actual release build is planned. |
| Native device-capability plugins | **NOT APPLICABLE** | Nothing currently requires them; add deliberately if a specific feature needs one. |
| Version control (git) | **IMPROVE** | Missing entirely; blocks the already-written CI paths. Outside "mobile architecture" narrowly, but directly responsible for one of this audit's findings. |
| Capacitor toolchain version | **IMPROVE** | Two major versions behind; no active problem, ordinary maintenance. |
| Test suites (backend/desktop/mobile E2E) | **KEEP** | Comprehensive and correctly separated by target (Phase 3F); mobile-specific suite (`e2e/mobile_*.py`) genuinely exercises `frontend/app/` with real device emulation (iPhone 14, Pixel 7, Galaxy S9+). |
| Documentation (`docs/`) | **KEEP**, with the dated/historical subfolders correctly treated as frozen snapshots, not living docs needing updates. |
| Stray junk directory | **REMOVE** (in a future, non-audit pass) | Zero functional role, confirmed empty. |

**Nothing in this repository was found to warrant REFACTOR or REBUILD.** The architecture — one Flask backend, two deliberately separate vanilla-JS clients (desktop + dedicated mobile), one Capacitor WebView wrapper around the mobile client — is coherent, the separation between web and mobile code is real and consistently maintained, and the one genuinely significant problem (`server.url` pointing at an emulator-only address) is a one-line configuration fix, not an architectural flaw.

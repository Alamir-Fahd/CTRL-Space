# Project technology identification

Read-only audit. Every claim below was checked against the actual repository on 2026-11-14, not assumed from documentation or memory. Exact file paths are cited throughout.

## Backend

**Python 3 + Flask 3, one process, SQLite database.**
- App factory: [`backend/ctrlspace/__init__.py`](../../backend/ctrlspace/__init__.py) — `create_app()`, registers API routes (`from .api import register`) and two static-serving routes (`index()` at `/`, `static_files(path)` catch-all).
- Process entry points: [`run.py`](../../run.py) (dev server + CLI: `serve`, `create-admin`, `check-ai`) and [`wsgi.py`](../../wsgi.py) (production WSGI entry).
- Database: `backend/ctrlspace/db.py`, stdlib `sqlite3`, file at `data/ctrlspace.db` (WAL mode).
- 12 backend `.py` files total: `__init__.py`, `db.py`, `api/__init__.py`, `api/intelligence_routes.py`, `api/mobile_routes.py`, `api/platform.py`, `services/assistant.py`, `services/auth.py`, `services/experiments.py`, `services/ingest.py`, `services/intelligence.py`, `services/search.py`.
- There is exactly **one** backend. Both the desktop web client and the mobile client talk to the same Flask process over the same `/api/*` routes.

## Desktop web client (browser)

**Plain HTML/CSS/vanilla ES modules. No build step, no framework.**
- Root: `frontend/` — `index.html`, `sw.js`, `manifest.webmanifest`, `css/app.css`, `js/{app.js,ui.js,api.js,views-research.js,views-platform.js,views-extra.js}`.
- Served by Flask's `GET /` and the static-file catch-all (`backend/ctrlspace/__init__.py:108-121`).
- Confirmed separate CSS strategy from the mobile client: `frontend/css/app.css` has **14** `@media` breakpoints (genuinely responsive across viewport widths) vs. the mobile app's **1** (an accessibility query only — see `WEB_VS_MOBILE_ANALYSIS.md`).

## Dedicated mobile client (the actual "mobile application")

**Also plain HTML/CSS/vanilla ES modules — a separate, dedicated SPA, not a resized version of the desktop site.**
- Root: `frontend/app/` — `index.html`, `app.css`, `js/{core.js,i18n.js,main.js,screens-a.js,screens-b.js,screens-c.js,screens-d.js,screens-e.js}` (10 files).
- Served by the same Flask process: any `/app` or `/app/...` request that isn't a real static file returns `frontend/app/index.html` (`backend/ctrlspace/__init__.py:119-120`), and `frontend/app/js/main.js` does its own client-side hash-free history-API routing from there (`const ROUTES = [...]`, `frontend/app/js/main.js:11-27`).
- Installable as a **Progressive Web App**: `frontend/app/index.html:11` links `/manifest.webmanifest`; `frontend/app/js/main.js:265` registers `/sw.js`.
- Mobile-first CSS evidence: `frontend/app/app.css:8` caps the content column at `560px` and reserves `env(safe-area-inset-top/bottom)` padding; **10** separate `env(safe-area-inset...)` usages found across the stylesheet; a fixed 5-tab bottom nav bar (`frontend/app/index.html` `<nav class="tabbar">`).

## Native app shell

**Capacitor 6 (installed) — wraps the mobile web client in a WebView. This is the only native-adjacent technology in the repository.**
- `mobile/capacitor/capacitor.config.json`: `"appId": "com.ctrlspace.app"`, `"webDir": "www"`.
- `mobile/capacitor/package.json`: `@capacitor/core`, `@capacitor/android`, `@capacitor/ios`, `@capacitor/cli` all declared at `^6.1.0`; **installed** versions confirmed via `npx cap doctor` (run this pass) are **6.2.3** across cli/core/android/ios, while **8.6.2** is the latest available — installed tooling is two major versions behind current.
- **Android**: a real, generated native project exists at `mobile/capacitor/android/` (Gradle, `AndroidManifest.xml`, `build.gradle`, `variables.gradle` — see `ANDROID_IOS_READINESS.md` for full detail). A debug APK exists on disk: `mobile/capacitor/android/app/build/outputs/apk/debug/app-debug.apk` (3,747,776 bytes, built 2026-11-13 16:30, confirmed a valid signed Android package via the `file` command).
- **iOS**: `@capacitor/ios` is an installed *dependency*, and a CI workflow (`.github/workflows/ios-build.yml`) exists to build it on a macOS runner, but **no `ios/` native project directory exists anywhere in the repository** — `npx cap add ios` has never been run locally. iOS is UNVERIFIED/BLOCKED pending a macOS+Xcode environment (see `ANDROID_IOS_READINESS.md`).

## Explicitly ruled out (checked, not found)

A targeted search for every framework named in the audit request found **zero** evidence of any of the following anywhere in the repository (excluding `node_modules`):
- React Native — no `metro.config.js`, no `react-native` package, no `.ios`/`.android` RN project files.
- Expo — no `app.json`/`app.config.js`/`app.config.ts` at the project or client root, no `expo` package.
- Flutter — no `pubspec.yaml` anywhere.
- Native Android written by hand (Kotlin/Java app logic) — the only Android source is Capacitor's generated `MainActivity` bridge class; no hand-written screens, view models, or Compose/XML UI beyond Capacitor's own boilerplate.
- Native iOS (Swift/SwiftUI) — no iOS project exists at all.
- Ionic/Cordova as the app framework — `cordovaAndroidVersion` appears only as a Capacitor-internal compatibility shim (`mobile/capacitor/android/variables.gradle`) for Cordova-plugin interop, not as the actual app framework; no Ionic UI components or `ionic.config.json` exist.

## One-line classification

CTRL+SPACE's mobile application is a **Progressive Web App** (`frontend/app/`, plain JS/CSS/HTML, installable, offline-capable via service worker) that is **additionally wrapped in a Capacitor WebView shell** to produce an installable Android package. It is not a native-coded app and not a cross-platform framework app (RN/Flutter/Expo). Full implications in `WEB_VS_MOBILE_ANALYSIS.md` and `PHASE_0_FINAL_DECISION.md`.

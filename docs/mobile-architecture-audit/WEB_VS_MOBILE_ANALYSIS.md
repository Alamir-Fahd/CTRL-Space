# Web vs. mobile analysis

Read-only audit, 2026-11-14. This is the audit's central question: are web-only files accidentally being treated as mobile files, is the mobile app actually mobile-first, and what exactly is the relationship between the "native" Android build and the website.

## The two clients are genuinely separate, not one responsive codebase

| | Desktop web client | Mobile client |
|---|---|---|
| Root | `frontend/` | `frontend/app/` |
| Entry HTML | `frontend/index.html` | `frontend/app/index.html` |
| Stylesheet | `frontend/css/app.css` (324 lines) | `frontend/app/app.css` (229 lines) |
| JS | `frontend/js/{app,ui,views-research,views-platform,views-extra}.js` | `frontend/app/js/{main,core,i18n,screens-a..e}.js` |
| Responsive breakpoints | **14** `@media` rules — genuinely adapts layout across viewport widths (desktop/tablet/phone browser use) | **1** `@media` rule total, and it's `(prefers-reduced-motion: reduce)` — an accessibility preference, not a width breakpoint |
| Layout strategy | Multi-column, nav bar, viewport-responsive | Fixed-fluid single column, `max-width:560px`, bottom 5-tab nav bar, `env(safe-area-inset-*)` padding on every screen |
| Navigation | Traditional top nav / in-page routing for a browser tab | Hash-free History-API SPA router + a persistent native-style bottom tab bar |

No file was found that blurs this line: nothing in `frontend/app/` renders desktop-only layouts, and nothing in `frontend/` (outside `app/`) is reachable from the mobile client's router. They are two deliberately separate front ends sharing one backend — not a single responsive site mislabeled as two things.

**Conclusion for Phase 7's core question ("is web code accidentally being treated as mobile code?"): No.** The separation is real and consistently maintained, evidenced by the stylesheet/breakpoint difference above, which is hard to fake by accident.

## What's genuinely shared, and why that's correct, not a mistake

| File | Imported by | Why sharing it is correct |
|---|---|---|
| `frontend/js/api.js` | `frontend/js/app.js` (desktop) **and** `frontend/app/js/core.js:2` (mobile, via `import {api, ApiError} from '/js/api.js'`) | Both clients talk to the identical `/api/*` backend contract. Duplicating this file would mean two places to keep an API contract in sync — the shared file is the correct design, not an accidental dependency. |
| `frontend/sw.js` | Registered independently by both `frontend/js/app.js:273` and `frontend/app/js/main.js:265`, both pointing at the same `/sw.js` | One service worker, one cache versioning scheme (`VERSION` in `sw.js`), precaches both clients' shells in a single `SHELL` array. Correct for a single-origin, single-backend project. |
| `frontend/manifest.webmanifest` | Linked from both `frontend/index.html:16` and `frontend/app/index.html:11` | One PWA identity for the whole origin. |
| `frontend/assets/*` (icons, hero art, logo) | Both clients' CSS (`url(/assets/hero.jpg)` etc.) | Same brand assets, one copy, no duplication. |

None of these should be split per-client; doing so would be the kind of "restructuring" this audit's Phase 9 explicitly says not to recommend without strong technical evidence, and there isn't any evidence here that sharing causes a problem.

## The Capacitor Android shell: what's actually native vs. what's a website in a wrapper

This is the single most important finding of this audit, and it has triple-confirmed, file-level evidence (not inference):

1. `mobile/capacitor/capacitor.config.json`: `"webDir": "www"`, **but also** `"server": {"url": "http://10.0.2.2:8000/app", "cleartext": true}`.
2. `mobile/capacitor/www/index.html` — the folder `webDir` points at — contains **only a 3-line error page**, whose own text reads: *"The CTRL+SPACE server set in capacitor.config.json (server.url) could not be reached."* This is not the application. It is what the user sees if the configured server is unreachable.
3. The config and fallback page **actually baked into the built APK** (`mobile/capacitor/android/app/src/main/assets/capacitor.config.json` and `.../assets/public/index.html`) are byte-identical to the two files above — confirmed by direct inspection, not assumed from the source config.

**What this means concretely:** when Capacitor's native `server.url` option is set, it takes priority over the bundled `webDir` at runtime — the WebView navigates to the live URL over the network instead of loading local assets. The installed Android app is, architecturally, **a native WebView frame pointed at the live website** — not an offline-bundled app with a backup web view. This is a deliberate, sensible choice given how the app works (see below), not a bug — but it is a materially different thing from "a mobile app with its UI bundled inside the APK," and judges or reviewers should understand the distinction.

**Why this is the right design for this app, not a shortcut:** `frontend/js/api.js:10` calls `fetch('/api' + path, {credentials: 'same-origin'})` — a relative path. For that fetch to resolve, the WebView's own origin has to *be* the Flask server's origin. If the HTML/JS were bundled locally inside the APK (a `file://` or `capacitor://` origin), every single API call would need to be rewritten to an absolute URL and CORS would need to be configured on the backend. Pointing the whole WebView at the live server avoids that entire class of problem, at the cost of requiring network connectivity and a reachable server address. This is a legitimate, common Capacitor pattern for a server-rendered-content app — the issue is specifically that the *current* `server.url` value (`10.0.2.2`) only works from an emulator, not that the pattern itself is wrong.

**Which parts are genuinely native:** the Android process itself (an installable `.apk`, a launcher icon, a real `MainActivity`, the OS-level install/permission/lifecycle model) is real and native. **Which parts are web-based:** literally everything the user sees and interacts with — every screen, every pixel — is the same HTML/CSS/JS as the browser PWA, rendered inside a WebView. **Is the UI rendered inside a WebView:** yes, unconditionally. **Are native device capabilities integrated:** no — confirmed by the zero-results search for `Capacitor.*`/`@capacitor/<plugin>` usage in `WEB_VS_MOBILE_ANALYSIS`'s sibling doc (`ANDROID_IOS_READINESS.md`); the only permission requested is `INTERNET`.

**Honest classification, per the audit's own instruction not to over- or under-claim:** this is a **hybrid mobile application using a WebView-based framework (Capacitor)**, functioning today as **a website packaged for installation** rather than a native-feeling hybrid app with device integration. Both of those things can change independently — fixing the `server.url` makes it a genuinely useful installed app without any architecture change; adding Capacitor plugins (camera, push, share, secure storage) would be the separate step to make it feel more "native" than "a website in a frame." Neither has happened yet.

## Dependency map (major folders)

```
frontend/app/*  ──imports──▶  /js/api.js  ──fetch /api/*──▶  backend/ctrlspace/*
frontend/*      ──imports──▶  /js/api.js  ──fetch /api/*──▶  backend/ctrlspace/*
frontend/app/*  ──registers──▶ /sw.js  ──precaches──▶  both clients' shell files
frontend/*      ──registers──▶ /sw.js  (same file, same cache)
mobile/capacitor/android/*  ──WebView navigates to──▶  capacitor.config.json server.url  ──▶  frontend/app/* (over the network, same as above)
e2e/mobile_*.py  ──Playwright drives──▶  frontend/app/* (via a running backend instance)
e2e/test_e2e.py  ──Playwright drives──▶  frontend/* (desktop, via a running backend instance)
tests/test_backend.py  ──imports──▶  backend/ctrlspace/* directly (no HTTP, in-process Flask test client)
```

No folder was found with an import or build-time dependency that crosses from `frontend/` (desktop) into `frontend/app/` (mobile) or vice versa, other than the deliberately shared files listed above.

## PWA / WebView file inventory and whether each is required for the current architecture

| File | Required for mobile architecture? |
|---|---|
| `frontend/sw.js` | Yes — both the installable-PWA path and the offline-reading feature depend on it. |
| `frontend/manifest.webmanifest` | Yes — required for "Add to Home Screen" / PWA installability (verified by `pwa_test.py`'s "Chromium installability check" and "Manifest parses cleanly" tests, both passing). |
| `frontend/app/index.html` | Yes — the mobile entry point itself. |
| `mobile/capacitor/www/index.html` | Yes, but only as an offline/unreachable-server fallback — not required for normal operation once `server.url` points at a real reachable server. |
| `mobile/capacitor/capacitor.config.json` | Yes — the only thing defining how the native shell finds the app. |

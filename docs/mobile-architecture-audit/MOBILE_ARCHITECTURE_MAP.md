# Mobile architecture map

Read-only audit, 2026-11-14. Traces the actual execution flow of `frontend/app/` (the mobile application) from cold start to a rendered screen, with file:line citations, plus how the Capacitor native shell relates to it.

## Two ways the same mobile client gets loaded

1. **As an installed PWA / in a mobile browser** — the device requests `https://<server>/app`, Flask serves `frontend/app/index.html` directly (`backend/ctrlspace/__init__.py:119-120`).
2. **As the installed Android app** — Capacitor's `MainActivity` opens a WebView and points it at `capacitor.config.json`'s `server.url` (currently `http://10.0.2.2:8000/app`, confirmed identical in the built APK's baked-in config at `mobile/capacitor/android/app/src/main/assets/capacitor.config.json`) — i.e. the WebView loads the **exact same page** over the network, not a bundled copy. See `WEB_VS_MOBILE_ANALYSIS.md` for why.

From that point on, execution is identical in both cases — it's the same `index.html`, same JS, same everything.

## Execution flow, in order

1. **Entry point**: `frontend/app/index.html` — loads Google Fonts (Inter, Chakra Petch, IBM Plex Sans Arabic), `app.css`, and `js/main.js` as an ES module (`<script type="module" src="/app/js/main.js">`, confirmed by `main.js`'s own `import`/`export` syntax).
2. **Splash sequence** (`frontend/app/js/main.js:267-281`, function `boot()`): applies the saved theme and language, shows the splash screen (`#splash`, full-bleed background art — see the branding work in `docs/qa/CTRL_SPACE_BRANDING_IMPLEMENTATION.md`), calls `dl.init()` (offline-download store init), races `checkServer()` against a 6-second timeout to detect online/offline/server-down, then calls `loadUser()`.
3. **Auth check** (`main.js:76-80`, `loadUser()`): calls `api.me()` — if it 401s, `S.user` stays `null` (guest mode, not an error state); if a user comes back, also loads prefs/theme/unread-notification count.
4. **API client init**: `frontend/app/js/core.js:2` imports `{api, ApiError}` from **`/js/api.js`** — the desktop client's API module, reused as-is (see `WEB_VS_MOBILE_ANALYSIS.md`'s shared-files section). `frontend/js/api.js:10` calls `fetch('/api' + path, {credentials: 'same-origin', ...})` — a **relative** path. This is precisely why the Capacitor WebView is pointed at the live server URL rather than bundling static files: a relative `/api/...` fetch only resolves correctly when the WebView's own origin *is* the Flask server's origin.
5. **First-run redirect**: if `localStorage['cs.onboarded']` isn't set, `boot()` rewrites the URL to `/app/welcome` before the first render (`main.js:278-279`).
6. **Router init / screen registration**: `render(true)` (`main.js:33-64`) matches `location.pathname` against the `ROUTES` array (`main.js:11-27`, ~38 route patterns, each a `[regExp, tabName, viewFunction]` triple), calls the matching screen function (imported from `screens-a.js` through `screens-e.js`), and injects the returned HTML string into `#view`.
7. **Client-side navigation**: a single delegated `click` listener (`main.js:66-70`) intercepts same-origin `/app/...` links and calls `go(url)` → `history.pushState` + `render(true)`, so navigation never reloads the page (true SPA behaviour, not a sequence of server round-trips).
8. **Post-render hooks** (`after()`, `main.js:47-63`): CSP-safe dynamic sizing (bar widths via `data-w` → `el.style.width`), CSP-safe cover photos (`data-img` → `el.style.backgroundImage`, since inline `style=""` is blocked by the CSP), related-NASA-image panels, onboarding dot sync, comparison-card swipe-dot sync, textarea auto-grow.
9. **State management**: one in-memory module-level object, `S` (`core.js:23-26`) — `user`, `prefs`, `unread`, `online`/`conn`, `ai` provider name, `conv`/`msgs` (current AI conversation), `cmp` (comparison selection, persisted to `sessionStorage`), `tab` (per-screen sub-tab memory), `q` (search filter memory). No Redux/MobX/Zustand or any state-management library — plain module state, appropriate for a vanilla-JS SPA of this size.
10. **Theming**: `applyTheme()`/`setLang()` (referenced in `main.js`, defined via `i18n.js` for language) write to `localStorage['cs.mtheme']`/`['cs.lang']` and toggle `data-theme`/`dir` attributes on `<html>`; CSS custom properties in `app.css` (`:root,[data-theme="dark"]`, `[data-theme="light"]`) do the actual recoloring — no JS-driven style recalculation beyond the attribute toggle.
11. **Offline/asset resolution**: `frontend/sw.js` (registered at `main.js:265`) precaches a fixed shell list (both clients' JS/CSS/HTML plus icons) and serves cached copies when offline; a separate `dl` object (`core.js`, backed by IndexedDB/localStorage — downloads store) lets a signed-in user explicitly save individual reports for offline reading, independent of the service worker's own app-shell cache.

## Architecture diagram (actual, not idealized)

```
                        ┌─────────────────────────────┐
                        │   Android app (Capacitor)    │
                        │   MainActivity → WebView      │
                        │   loads capacitor.config.json │
                        │   server.url over the network │
                        └───────────────┬───────────────┘
                                        │  (same page as below, loaded remotely)
                        ┌───────────────▼───────────────┐
  Browser / PWA  ──────▶│   frontend/app/index.html      │  Mobile Application Entry Point
                        └───────────────┬───────────────┘
                                        │ loads
                        ┌───────────────▼───────────────┐
                        │   js/main.js: boot() → render() │  Navigation / Router
                        │   ROUTES[] pattern match         │  (history API, no page reloads)
                        └───────────────┬───────────────┘
                                        │ dispatches to
                 ┌──────────────────────┼──────────────────────┐
                 ▼                      ▼                      ▼
        screens-a.js            screens-b.js ... e.js    i18n.js (strings, RTL)
        (home, auth, research)  (assistant, experiments,
                                 workspace, combustion hub)
                 │                      │
                 └──────────┬───────────┘
                             ▼
                    core.js: S state object, UI primitives, icon set
                             │ imports
                             ▼
                    /js/api.js  (SHARED with the desktop client)
                             │ fetch('/api' + path, credentials:'same-origin')
                             ▼
                 ┌───────────────────────────────┐
                 │   Flask backend (single process) │
                 │   backend/ctrlspace/api/*.py      │
                 └───────────────┬───────────────┘
                                 ▼
                 ┌───────────────────────────────┐
                 │  services/: search, assistant,   │
                 │  experiments, auth, ingest        │
                 │  → SQLite (db.py) + AI provider   │
                 │  + NASA NTRS / PSI / Image Library │
                 └───────────────────────────────┘
```

No component in this diagram was invented — every box corresponds to a real file cited above. There is no separate "mobile backend" or "mobile API" layer; the mobile client, the desktop client, and (if built) the Capacitor Android app all call the identical `/api/*` surface on the identical Flask process.

# CTRL+SPACE mobile application — architecture report (v5)

## Decision on the native client

The specification asks for a React Native + Expo + TypeScript client when only a web client exists. **That client was not built.** The build environment has no internet access, so npm packages (React Native, Expo, TypeScript) cannot be installed, built, run or tested, and the specification forbids delivering untested functionality as complete.

What was built instead, and verified: a **dedicated mobile-first application at `/app`**, separate from the desktop website, designed around phone navigation (floating 5-tab bar, onboarding, bottom sheets, full-screen assistant). It installs to the home screen as an app (manifest `start_url` = `/app`), works offline for downloaded content, and reuses the existing Python backend unchanged in architecture. It is web technology, **not** a native app; it can be packaged for Android (PWABuilder or the Capacitor shell in `mobile/android/`), which loads this client in a native wrapper rather than reimplementing it.

To build a true React Native client later, use the API in `docs/API.md` and `backend/ctrlspace/api/mobile_routes.py` as the contract; every screen in `frontend/app/js/` maps one-to-one to a React Native screen. Do it on a machine with npm (for example with Claude Code), with an Android emulator and a physical phone.

## Structure

```
backend/ctrlspace/            Python API (unchanged architecture), schema v4
  api/mobile_routes.py        conversations, notifications, password resets, NASA images, profiles, AI comparison, feedback
frontend/app/                 mobile application (separate from the desktop site in frontend/)
  index.html, app.css         shell + design system (tokens from the specification)
  js/core.js                  state, routes, icons, UI primitives, offline downloads, sync outbox
  js/main.js                  router, splash/boot, all actions and forms, connectivity
  js/screens-a.js … d.js      28 screens
frontend/sw.js                offline app shell for both clients; public research data cached; personal data never cached
```

## Feature classification

| Feature | Status | Notes |
|---|---|---|
| Splash, onboarding, sign in, registration | Fully implemented | Backend check with 6 s cap; never traps the user |
| Password recovery | Partially implemented | No email service: request notifies admins; admin issues a one-time, 1-hour, hashed reset link |
| Google / Microsoft sign-in | Missing (not configured) | Spec: only if configured |
| Home dashboard | Fully implemented | Real counts and records only; personalized greeting, recent activity, saved reports |
| “AI insight” on Home | Not implemented | Would need a provider and a defined source; not invented |
| Discover, search results, filters | Fully implemented | Categories are combustion topics from the corpus; space-wide categories in the spec (astronomy, Earth science…) have no data and are not shown |
| Research details | Fully implemented | Abstract only where stored; figures not digitized (said on screen); related NASA images labeled as search results |
| AI assistant (history, follow-up context, report scope, export, copy, share, regenerate, feedback, follow-ups) | Fully implemented · requires credentials for generated answers | Without a provider: retrieval-only, clearly labeled. Streaming: not implemented |
| AI research analysis | Fully implemented · AI sections require credentials | 7 sections; implications need a provider |
| Evidence library, collections (create, rename, describe, remove, export) | Fully implemented | |
| NASA Image and Video Library | Implemented · not verified live | Official API, cached; tested with recorded responses; needs internet |
| NASA Earthdata / Open APIs | Missing | Not relevant to the combustion corpus; would need keys and a defined use |
| Experiment explorer, details, results | Fully implemented | Objective shown only where a source states it |
| Comparison (parameters, outcomes, notes, AI summary, export, brief) | Fully implemented · AI summary requires credentials | |
| Workspace, notes editor (autosave) | Fully implemented | Plain-text notes (no rich text) |
| Learning Studio, challenges | Fully implemented | |
| Community, public profiles | Fully implemented | |
| Notifications | Fully implemented | Real events only (welcome, replies, moderation, reset requests); in-app, no push |
| Push notifications | Missing | Needs a push service; not configured |
| Profile, edit profile, settings, sessions, privacy, storage | Fully implemented | Profile photo upload not supported (initial avatar) |
| Language setting | Fully implemented | English and Arabic (RTL). Interface fully translated by measurement; NASA titles, passages, experiment values and lesson content stay in English (verbatim sources); the assistant asks for English questions because retrieval matches English sources |
| Offline mode + sync | Fully implemented | Downloads, cached reads, outbox for saves/notes, last-sync time; distinguishes internet vs. server vs. NASA vs. AI availability |
| Demo mode, About, Help | Fully implemented | |
| Native iOS/Android app (React Native / Expo) | Missing — blocked | See decision above |
| Android APK / iOS app packaging (Capacitor shell) | Prepared, not built here | `mobile/capacitor/` + GitHub Actions workflows `.github/workflows/android-apk.yml`, `ios-build.yml`; see `docs/NATIVE_BUILDS.md`. Untested until first run |

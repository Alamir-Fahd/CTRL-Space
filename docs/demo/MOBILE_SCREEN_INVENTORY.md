# CTRL+SPACE mobile app — complete screen inventory

Built directly from the real route table (`frontend/app/js/main.js`'s `ROUTES` array, 38 patterns) and the screen functions it dispatches to (`frontend/app/js/screens-{a..e}.js`), not from memory or documentation claims. This is the actual, current screen list — nothing here was invented.

| # | Screen | Route | Purpose | Key interactive elements | Backend dependency | Offline availability | Recording chapter |
|---|---|---|---|---|---|---|---|
| 1 | Splash | `/app` (first paint) | Boot sequence, connectivity check, branding | None (auto-transitions) | `GET /api/health`, `GET /api/me` | Works offline (shows "Offline · opening saved research") | 01 |
| 2 | Onboarding | `/app/welcome` | First-run intro, 4 slides | Skip, Next/Get started, language switch | None | Full (static) | 01 |
| 3 | Login | `/app/login` | Email/password sign-in + demo access | Email/password fields, show/hide password, Sign in, demo credential copy buttons, Explore Demo | `POST /api/auth/login` | Requires internet | 02 |
| 4 | Register | `/app/register` | Account creation | Name/email/password/confirm fields, category radio cards (Student/Researcher/Educator/Other), institution field, Create account | `POST /api/auth/register` | Requires internet | 03 |
| 5 | Forgot password | `/app/forgot` | Password reset request | Email field, submit | `POST /api/auth/forgot` | Requires internet | 02 |
| 6 | Reset password | `/app/reset` | Set new password from reset link | New password field | `POST /api/auth/reset` | Requires internet | N/A (needs a real reset token, not demoed) |
| 7 | Home | `/app` (after boot) | Dashboard | Search bar, Discover/Ask AI/Experiments/Compare/Saved chips, AI hero card, live stats, NASA discoveries rail, experiments rail, NASA image rail, saved/activity (signed-in) | `GET /api/stats,/api/reports,/api/experiments,/api/media,/api/saved,/api/activity` | Partial (cached shell renders; data needs network or prior SW cache) | 04 |
| 8 | Research / Discover | `/app/research` | Browse all reports | Search, category/evidence/sort filter sheet, report cards | `GET /api/reports` | Partial (SW-cached if previously visited) | 06 |
| 9 | Search results | `/app/search` | Query results | Query input, result list | `GET /api/search` or `/api/reports?q=` | Partial | 06 |
| 10 | Report detail | `/app/report/:id` | One NASA report | Overview/Citations/Pages tabs, Ask about this report, Download for offline, AI analysis, Add to collection, related NASA images | `GET /api/reports/:id`, `/:id/pages` | **Full once downloaded** (IndexedDB `dl` store) | 05, 08 |
| 11 | AI Analysis | `/app/analysis` | Structured AI document analysis entry | Topic input | `POST /api/analysis` | Requires internet | 09 |
| 12 | AI Assistant | `/app/assistant` | Evidence-grounded Q&A | Message composer, send/stop, suggested questions, citation chips, follow-up actions | `POST /api/ask` | Input disabled offline (no on-device model yet) | 09 |
| 13 | Assistant conversation | `/app/assistant/:id` | Resume a saved conversation | Same as above | `GET /api/conversations/:id` | Requires internet | 09 |
| 14 | Conversation history | `/app/history` | List past AI conversations | Open/export/delete | `GET /api/conversations` | Requires internet | 09 |
| 15 | Evidence library | `/app/library` | Saved/Documents/Images/Collections/Downloads tabs | Tab switcher, search (images tab) | `GET /api/saved,/api/reports,/api/media,/api/collections` | Downloads tab is fully offline (IndexedDB) | 07 |
| 16 | Collection detail | `/app/collection/:id` | One saved collection | Rename, export, item list | `GET /api/collections/:id` | Requires internet | 13 |
| 17 | Experiment Explorer | `/app/experiments` | Browse experiments | Program filter chips (BASS-II/FLEX/SAME/Saffire/All), compare checkboxes | `GET /api/experiments` | Partial | 10 |
| 18 | Experiment detail | `/app/experiments/:id` | One experiment | Add to comparison, Analyze with AI, Add to collection, parameter/methodology/results sections, related NASA images, notes (signed-in) | `GET /api/experiments/:id` | Partial | 11 |
| 19 | Compare | `/app/compare` | Side-by-side experiment comparison | Picker, Parameters/Notes/AI/Outcomes tabs, swipeable cards | `POST /api/compare` | Requires internet | 12 |
| 20 | Visualization Lab | `/app/viz` | Corpus-wide charts | Chart tabs | `GET /api/experiments,/api/reports` | Partial | 10 |
| 21 | Workspace | `/app/workspace` | Notes/saved-item hub | Tabs, item list | `GET /api/notes` etc. | Requires internet | 13 |
| 22 | Note editor | `/app/note/:kind/:id` | Edit a note on a report/experiment | Textarea, autosave | `PATCH` note endpoint | Requires internet | 13 |
| 23 | Learning Studio | `/app/learn` | Lesson list | Lesson cards | `GET /api/lessons` | Partial | 14 |
| 24 | Lesson detail | `/app/learn/:id` | One lesson | Section nav, Mark complete, evidence citations | `GET /api/lessons/:id`, `POST .../complete` | Requires internet to mark complete | 14 |
| 25 | Challenge | `/app/challenge/:id` | Lesson-linked challenge | Answer submission, grading feedback | `POST` challenge endpoint | Requires internet | 15 |
| 26 | Community | `/app/community` | Discussion rooms | Room list, create post | `GET /api/rooms` | Requires internet | 16 |
| 27 | Room | `/app/community/:id` | One discussion room | Posts, reply, share | `GET /api/rooms/:id` | Requires internet | 16 |
| 28 | Post | `/app/community/post/:id` | One post + replies | Reply composer, edit (own post) | `GET/POST` post endpoints | Requires internet | 16 |
| 29 | User profile (public) | `/app/user/:id` | Another user's public profile | — | `GET /api/users/:id` | Requires internet | N/A |
| 30 | My Profile | `/app/profile` | Own account overview | Category/institution/demo badge, stats, menu links (Combustion Hub, Judge mode, Offline, Settings, About, Help) | `GET /api/me` | Partial (cached if visited) | 17 |
| 31 | Edit profile | `/app/profile/edit` | Edit name/category/institution | Form fields, category radio cards, Save | `PATCH /api/me` | Requires internet | 17 |
| 32 | Settings | `/app/settings` | Account/app settings | Theme toggle, language, notification prefs, password change, sessions, logout | `PATCH /api/me`, `POST /api/auth/logout` | Theme/language work offline; account changes need internet | 18, 19 |
| 33 | Offline & storage | `/app/offline` | Offline status hub | Connection status, downloaded-report list, storage controls (clear downloads/cache) | None (reads local state) | **Fully offline by design** | 20, 21 |
| 34 | Notifications | `/app/notifications` | Alerts list | Mark all read, open notification | `GET /api/notifications` | Requires internet | 04 |
| 35 | Demo info | `/app/demo` | Guided live-demo script for judges | Scripted walkthrough links | None | Full (static) | 02 |
| 36 | About | `/app/about` | App identity, disclaimers | — | None | Full (static) | 18 |
| 37 | Help | `/app/help` | Help/FAQ | — | None | Full (static) | 18 |
| 38 | Combustion Research Hub | `/app/combustion` | Real fire-safety case studies + NASA PSI data | Case study cards, PSI search entry | `GET /api/psi/search` | Partial | 05 |
| 39 | Case study | `/app/combustion/case/:id` | One historical case (Apollo 1/13, Mir) | — | None (static content) | Full | 05 |
| 40 | PSI search | `/app/combustion/psi` | NASA Physical Science Informatics search | Search input, results | `GET /api/psi/search` | Partial | 05 |
| 41 | PSI detail | `/app/combustion/psi/:id` | One PSI investigation | — | `GET /api/psi/search` (cached) | Partial | 05 |
| 42 | Impact Dashboard | `/app/impact` | Real usage/benchmark stats for judges | — | `GET /api/impact` | Requires internet | N/A (judge-facing, not in user journey) |
| 43 | Judge Mode | `/app/judge` | No-login judge entry point | Links to Impact Dashboard, live demo | None | Full (static shell) | N/A |

## Not found / explicitly not part of this app

The original task template listed "Challenges" and "Community" as hypothetical modules to verify — both **do exist** (rows 25 and 26–28). No screen in the template was found to be missing from the actual route table. One thing the template assumed that isn't accurate: the app is a single-activity WebView (Capacitor) / SPA (browser), not a screen stack with a hardware-style "drawer" — navigation is a persistent 5-tab bottom bar (Home/Discover/Ask AI/Experiments/My Research) plus an in-page hamburger-free profile menu; there is no slide-out drawer anywhere in the current UI.

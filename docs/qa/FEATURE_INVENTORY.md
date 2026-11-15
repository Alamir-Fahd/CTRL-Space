# CTRL+SPACE — feature inventory

Built from the actual registered Flask routes (`grep` over `backend/ctrlspace/api/*.py`, not from documentation) and the actual frontend screen files, 2026-11-13. 85 API routes exist; this groups them by feature.

| # | Feature | Screen(s) | Frontend | Backend | API | DB | Test cases | Status | Priority |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Home dashboard | `/`, `/app` | Implemented | Implemented | `/api/stats`, `/api/impact` | `reports`,`passages`,`experiments` | 3 | PASS | Critical |
| 2 | Research discovery | `/research`, `/app/research`, `/app/search` | Implemented | Implemented | `GET /api/reports` | `reports`,`report_categories` | 4 | PASS | Critical |
| 3 | Evidence library | `/library`, `/app/library` | Implemented | Implemented | `GET /api/reports`, `GET /api/media/search` | `passages` | 4 | PASS | High |
| 4 | Report details | `/app/report/:id` | Implemented | Implemented | `GET /api/reports/:id`, `GET /api/reports/:id/pages` | `reports`,`passages`,`report_pages` | 4 | PASS | Critical |
| 5 | AI research assistant | `/assistant`, `/app/assistant` | Implemented | Implemented | `POST /api/ask`, `POST /api/assistant/ask`, `POST /api/analyze` | `conversations`,`messages` | 11 (evidence-only/mocked) + 30 planned real-LLM | PASS (evidence-only path); real-LLM BLOCKED — see `AI_TEST_REPORT.md` | Critical |
| 6 | Experiment explorer | `/experiments`, `/app/experiments` | Implemented | Implemented | `GET /api/experiments`, `GET /api/experiments/:id` | `experiments`,`experiment_fields` | 4 | PASS | High |
| 7 | Experiment comparison | `/compare`, `/app/compare` | Implemented | Implemented | `POST /api/compare`, `POST /api/compare/ai`, `POST /api/compare/export` | `experiments`,`experiment_fields` | 6 | PASS | Critical |
| 8 | Scientific Visualization Lab | `/app/viz` | Implemented | N/A (client-side aggregation of existing endpoints) | reuses `/api/experiments`,`/api/reports` | — | 1 (manual, this session) | PASS | Medium |
| 9 | Combustion Research Hub / PSI | `/app/combustion*` | Implemented | Implemented | `GET /api/psi/search` | `psi_cache` | 1 automated + live probes | PASS | Medium |
| 10 | My Research / workspace | `/my-research`, `/app/workspace` | Implemented | Implemented | `GET/POST /api/collections`, `GET/PUT /api/notes` | `collections`,`collection_items`,`notes` | 5 | PASS | High |
| 11 | Learning Studio | `/studio`, `/app/learn` | Implemented | Implemented | `GET /api/lessons`, `POST /api/lessons/:id/complete` | `lessons` | 3 | PASS | Medium |
| 12 | Challenges | `/app/challenge/:id` | Implemented | Implemented | `GET /api/challenges`, `POST /api/challenges/:id/attempts` | `challenges` | 2 | PASS; draft-answer persistence across reload: **not implemented** (noted, not a bug — see `BUG_REPORT.md`) | Medium |
| 13 | Community | `/community`, `/app/community` | Implemented | Implemented | `GET /api/rooms`, `POST /api/rooms/:id/posts`, replies/report/moderate | `rooms`,`posts`,`replies` | 4 | PASS | Medium |
| 14 | Profile / settings | `/profile`, `/app/profile`, `/app/settings` | Implemented | Implemented | `GET/PATCH /api/me`, `POST /api/me/password`, sessions | `users`,`sessions` | 4 | PASS | High |
| 15 | Admin dashboard | `/admin` | Implemented | Implemented | `/api/admin/*` (14 routes) | all tables, `audit_log` | 6 | PASS | Critical |
| 16 | Authentication | `/login`, `/register` | Implemented | Implemented | `/api/auth/*` | `users`,`sessions`,`password_resets` | 5 | PASS | Critical |
| 17 | Mobile PWA / offline | `/app/*` (all) | Implemented | Implemented | service worker + IndexedDB | n/a (client storage) | 9 + 20 + 32 | PASS | Critical |
| 18 | Arabic (i18n/RTL) | `/app/*` (all, toggled) | Implemented | n/a | n/a | n/a | 5 | PASS | High |
| 19 | Native Android shell | Capacitor | Implemented, built this session | n/a (same backend) | n/a | n/a | 1 manual (emulator run) | PASS | Medium |
| 20 | Native iOS shell | Capacitor | Prepared, unbuilt | n/a | n/a | n/a | 0 | BLOCKED (no Mac/Xcode) | Low |

Total automated test cases executed and traced in this pass: **175** (90 backend + 19 desktop E2E + 20 mobile E2E + 5 Arabic + 9 PWA + 32 device sweep), plus live manual probes documented in `FEATURE_TEST_CASES.md` and `API_TEST_CASES.md`.

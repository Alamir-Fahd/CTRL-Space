# Screen inventory, routes and journeys (v3)

Every screen below runs against the real API and has loading, empty, error and retry states. "Tested" names the browser check in `e2e/test_e2e.py` (14/14 passing) and the backend tests in `tests/test_backend.py` (62/62).

| # | Screen | Route | Main endpoints | Tested by |
|---|---|---|---|---|
| — | Launch | (every full load) | `GET /api/health`, `GET /api/auth/me` | Launch |
| 01 | Home / Dashboard | `/` | `/api/stats`, `/api/reports?sort=indexed` | 01 Home, Journey A |
| 02 | Research Discovery | `/research?q=` | `/api/reports?q&category&material&year_from&year_to&evidence&sort` | Journey A |
| 03 | Evidence Library | `/library` | `/api/reports`, `/api/search` (passage tab) | Journey E |
| 04 | Report Details | `/library/:reportId` | `/api/reports/:id`, `/api/reports/:id/pages`, `/api/saved`, `/api/notes/:id` | Journeys A, D, E, F |
| 05 | Research Assistant | `/assistant` | `POST /api/ask` | Journey B |
| 06 | Experiment Explorer | `/experiments` | `/api/experiments` | Journey C |
| 07 | Experiment Details | `/experiments/:experimentId` | `/api/experiments/:id`, `/api/experiment-notes/:id` | Journey C |
| 08 | Compare | `/compare` | `POST /api/compare`, `POST /api/compare/export` | Journey C |
| 09 | My Research | `/my-research` | `/api/saved`, `/api/collections…`, `/api/research-notes`, `/api/me/activity`, exports | Journey D |
| 10 | Learning Studio | `/studio`, `/studio/:id` | `/api/lessons…` | 10 Studio |
| 11 | Challenges | `/challenges`, `/challenges/:id` | `/api/challenges…`, `POST …/attempts` | 11 Challenges |
| 12 | Community | `/community`, `/community/:room`, `/community/post/:id` | `/api/rooms…`, `/api/posts…`, `/api/community/recent` | 12 Community |
| 13 | Profile / Settings | `/profile`, `/settings` | `/api/me…`, `/api/me/sessions`, `/api/me/export` | 13 Settings |
| — | Research gaps | `/gaps` | `GET /api/gaps` | Research gaps |
| — | Demo mode | `/demo` | `GET /api/demo/preflight`, `POST /api/brief` | Demo mode |
| 14 | Admin | `/admin` (admin role, enforced by the API) | `/api/admin/*` | Journey F |

## Mandatory journeys (spec Part 3), all automated

- **A** Dashboard → search → Research Discovery → filters → results → report → evidence passage → NASA source link.
- **B** Assistant → too-short question rejected → example question → evidence with NASA links → off-topic question gets the exact insufficient-evidence message, question preserved.
- **C** Explorer (material filter) → details (oxygen basis, temperature, apparatus, verification column) → add to comparison → pick another → conditions and measurements tables, chart, notes → Markdown export.
- **D** Report → save → collection → note → My Research shows saved report, collection, note, activity.
- **E** Evidence Library → “only reports with extracted evidence” → report → extracted pages tab → NASA source → back → passage search.
- **F** Admin → system health → reports → flag a passage on a report page → experiment blocked as unverified → review and approve evidence → reject then approve an experiment → moderation → disable/enable user → audit log shows every action.

## Spec items intentionally not implemented

| Item | Reason |
|---|---|
| Angular + Node/Express/MongoDB | Owner chose to keep the tested Flask stack (decision 2026-11-12). The API is the contract for a later port. |
| Language setting | English only; an Arabic interface needs translation and right-to-left layout (open item). |
| Notification preferences | The app sends no notifications, so a toggle would do nothing. |
| Creating / joining / leaving rooms | Rooms are fixed and seeded; anyone signed in can read and post. Room management is an open item. |
| Search suggestions and search history | Not approved; recent activity is in My Research. |
| Simple/scientific explanation modes, follow-ups | Not approved in Phase 7; the assistant is stateless by design. |
| Abstracts and keywords for every report | Stored only where read from the NTRS record (abstract: 1 report; keywords: 3). Others say “not stored” with the NTRS link. |
| Page numbers for the BASS-II poster | Its text has no page breaks; passages cite section headings instead of guessed pages. |

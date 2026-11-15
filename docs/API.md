# API reference

Base path `/api`. JSON in and out. Errors always use:

```json
{"error": {"code": "validation_error", "message": "…", "details": {…}, "request_id": "…"}}
```

Every response carries `X-Request-ID`. Lists use `{"items", "total", "limit", "offset"}`. Auth is a session cookie (`cs_session`, HttpOnly, SameSite=Strict) set by register/login.

## Public

| Method | Path | Notes |
|---|---|---|
| GET | `/health` | status, database, AI provider name, indexed passage count |
| GET | `/stats` | reports, indexed reports, verified passages, experiments, programs |
| GET | `/reports?q=&program=&sort=date\|title&limit=1-100&offset=` | ranked by passage relevance when `q` is given |
| GET | `/reports/{ntrs_id}` | metadata + verified passages + experiments (+ `my_note` when signed in). Pending reports: admins only |
| GET | `/reports/{ntrs_id}/pages?limit=&offset=` | extracted page text (imported PDFs) |
| GET | `/search?q=&program=&kind=&limit=1-50&offset=` | verified passages, BM25 score, matched terms |
| POST | `/ask` `{"question": "...", "top_k": 2-8}` | see statuses below |
| GET | `/experiments` | published experiments with reported-field counts |
| GET | `/experiments/{id}` | every field with state, value, number+unit, source passage |
| POST | `/compare` `{"experiment_ids": [2-4 ids]}` | rows, warnings, chartable fields, methodology |

`/ask` statuses: `answered` (answer, points with validated citations, limits, warnings), `insufficient_evidence` (reason, closest passages; AI not called), `evidence_only` (AI not configured, unavailable, or returned invalid output; `error_code` says which).

Example:

```bash
curl -s localhost:8000/api/ask -H 'Content-Type: application/json' \
  -d '{"question":"How does oxygen concentration affect flame spread in microgravity?"}'
```

## Account (signed in)

| Method | Path | Notes |
|---|---|---|
| POST | `/auth/register` `{name,email,password}` | password ≥ 10 chars with a capital and a digit; 409 if email exists |
| POST | `/auth/login` `{email,password}` | 401 `invalid_credentials` (same message for unknown email) |
| POST | `/auth/logout` | revokes the session server-side |
| GET | `/auth/me` | `{"user": null}` when signed out |
| GET/POST | `/collections` | list / create `{name}` (max 50) |
| DELETE | `/collections/{id}` | owner only (others get 404) |
| POST | `/collections/{id}/items` `{kind: report\|experiment, id}` | |
| DELETE | `/collections/{id}/items/{kind}/{ref}` | |
| GET | `/collections/{id}/export` | Markdown with sources and notes |
| PUT | `/notes/{ntrs_id}` `{text}` | ≤ 5000 chars; empty text deletes |

## Admin (role `admin`)

| Method | Path | Notes |
|---|---|---|
| GET | `/admin/overview` | counts by status, AI provider |
| GET | `/admin/reports` | all reports incl. pending, with unverified passage counts |
| POST | `/admin/reports/{id}/status` `{status}` | approved / pending / rejected; reindexes |
| GET | `/admin/passages` | unverified passages |
| POST | `/admin/passages/{id}/review` `{action: verify\|reject, kind}` | verify needs a type; reject blocked (409) if an experiment cites it |
| POST | `/admin/ingest` `{ntrs_id}` | NTRS import; 400 invalid id, 404 not found, 502 not a PDF / id mismatch, 503 NTRS unreachable |
| POST | `/admin/reindex` | rebuild search index |
| GET | `/admin/audit`, `/admin/ingestion-log`, `/admin/users` | users never include password hashes |

Status codes used: 200, 201, 400, 401, 403, 404, 409, 413 (body > 64 KB), 415, 422, 429, 500, 502, 503.

## v2 endpoints

| Area | Endpoints |
|---|---|
| Profile | `GET/PATCH/DELETE /me`, `POST /me/password`, `GET/DELETE /me/activity`, `GET /me/recent`, `GET /notes` |
| Learning | `GET /lessons`, `GET /lessons/{id}`, `POST /lessons/{id}/complete` |
| Challenges | `GET /challenges`, `GET /challenges/{id}` (no answers), `POST /challenges/{id}/attempts` |
| Community | `GET /rooms`, `GET/POST /rooms/{id}/posts`, `GET /posts/{id}`, `POST /posts/{id}/replies`, `DELETE /posts/{id}`, `POST /posts/{id}/report` |
| Admin | `GET /admin/analytics`, `GET /admin/experiments`, `POST /admin/experiments/{id}/status`, `GET /admin/moderation`, `POST /admin/posts/{id}/moderate`, `POST /admin/users/{id}` |
| Reports | `GET /reports?category=` |

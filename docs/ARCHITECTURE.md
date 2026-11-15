# Architecture

## Decision summary

| Layer | Choice | Why |
|---|---|---|
| Backend | Python 3 + Flask 3 | Phases 2 and 5 chose a Python backend (FastAPI). FastAPI could not be installed in the offline build environment; Flask was available, keeps the same layering (routes → services → database), and is mature and simple to deploy. Migrating the routes to FastAPI later is mechanical. |
| Database | SQLite (stdlib `sqlite3`) | Phase 3 used SQLite for development and tests. Zero setup for the team. Integrity rules live in the schema. PostgreSQL is the documented upgrade path. |
| Search | BM25 keyword retrieval (`services/search.py`) | Phase 6 design: page-preserving passages, explainable ranking. Semantic/vector search was optional in Phase 6 and is not needed at the current corpus size. |
| AI | Provider adapter: none / anthropic / openai / ollama | Phase 7: one interface, config by environment, keys server-side, hard evidence gate before any call. |
| Frontend | Plain ES modules + CSS, no build step | Phase 9 used React; npm was unavailable here. The app is a hash-routed SPA with the same pages, states and API contract, and runs without Node. |
| Architecture | Modular monolith | Every phase document and the handoff reject microservices. |

The handoff document's Node/Express/MongoDB/Angular stack was not used: that repository was not in the project archive (see `docs/audit/CTRL_SPACE_PROJECT_AUDIT.md`), and all existing code was Python.

## Components

```
Browser (frontend/)  ──fetch /api/*──▶  Flask app (backend/ctrlspace)
                                         ├─ api/            validation, auth, JSON errors
                                         ├─ services/search      BM25 index (in memory, rebuilt on change)
                                         ├─ services/assistant   gate → prompt → provider → citation check
                                         ├─ services/experiments field states, comparison warnings
                                         ├─ services/auth        PBKDF2, sessions, rate limits
                                         ├─ services/ingest  ──▶ NASA NTRS API (https://ntrs.nasa.gov/api)
                                         └─ db.py            ──▶ SQLite file + data/originals/*.pdf
                                                  AI provider (optional) ◀── services/assistant
```

## Data model

`reports` → `report_pages` → `passages` → `experiment_fields` ← `experiments`; plus `users`, `sessions`, `collections`, `collection_items`, `notes`, `audit_log`, `ingestion_records`. Rules enforced by SQL `CHECK` constraints:

- A field in state `reported` must have a value and a `passage_id`.
- A number requires a unit and the `reported` state, so missing data can never be stored as zero.
- Field states are limited to reported / not_reported / unknown / unavailable / not_applicable / not_extracted.
- Report IDs must be 8–12 digit NTRS IDs. Passages cascade with their report.

## Evidence pipelines

**Documents (Phase 4 → 6 → 7):** NTRS metadata → eligibility check (public, disseminated as document) → PDF download (signature check, SHA-256, random file name, never overwrite) → page text → passages (`unreviewed`, unverified) → **admin verifies against the PDF** → search index → assistant.

**Experiments (Phase 8):** verified passage → field value with state and source → comparison with warnings → table and chart.

## Ask sequence

1. Validate question (8–400 chars) and rate limit (20 per 5 min per IP).
2. Retrieve verified passages from approved reports.
3. Evidence gate: at least 2 passages that each match ≥ ⅓ of the query terms. Otherwise return `insufficient_evidence` without calling the AI.
4. Build context: up to 6 passages tagged `[S5]`, `[B8]`… with type labels (hypotheses marked).
5. Provider returns JSON. Invalid JSON is discarded (`evidence_only`).
6. Citation validation: any cited ID not in the retrieved set is removed; points left with no valid citation are dropped; a warning reports how many.
7. Report titles, page/slide/section and NTRS links come from the database, never from the model.

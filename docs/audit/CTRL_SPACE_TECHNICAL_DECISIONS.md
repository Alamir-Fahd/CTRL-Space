# CTRL+SPACE — Technical Decisions

Status: **PROPOSED — awaiting owner approval.** Nothing here is implemented. The master prompt forbids silently switching frameworks, so every stack choice below needs an explicit yes/no.

## 1. Stack decision (resolves conflicts X-1, X-2, X-3)

### Option A — Python/FastAPI + React (recommended)
| Layer | Choice | Evidence it exists |
|---|---|---|
| Backend | Python 3.11+, FastAPI | P5 app (1,640 lines), P6 and P8 FastAPI adapters |
| DB | PostgreSQL (prod), SQLite (dev/tests) | P3 models + Alembic; P5 tests use SQLite |
| Search | P6 keyword retrieval; pgvector later | P6 package; P3 migration `0002_pgvector_embeddings` |
| PDF | pdfplumber now, PyMuPDF when installable | P4 `extract.py` supports both |
| Experiments | P8 engine | 55/55 tests verified |
| Frontend | React 18 + TS + Vite | P9 app (1,022 lines) |
| Charts | Existing SVG component (no new library) | P9 `BarChart.tsx` |

**Why:** it is the only code in the archive; it matches the Challenge Guide ("Backend (FastAPI) + dashboard frontend") and the original project PDF; the strongest module (P8) is Python; RAG/PDF tooling is mature in Python.
**Cost:** the handoff's Node backend phases (auth, sessions, collections) would have to be re-implemented in Python *if* they are still required.

### Option B — Node/Express + MongoDB + Angular (handoff)
**Only viable if the `D:\FlameLab` repository is supplied.** It does not exist in the archive, so choosing it from here means rewriting all six Track A modules in TypeScript and building Angular from zero, while discarding the verified P8 engine.

### Option C — Hybrid
Node/Express backend from `D:\FlameLab` for accounts/collections + Python service for ingestion, search, RAG and comparison. Violates the handoff's "modular monolith, no microservices" rule; not recommended.

## 2. Canonical data model (needed whichever option is chosen)

Base: **P3 schema** (reports → report_pages → passages; experiments → experiment_measurements; ingestion_records) extended with **P8's value semantics**:
- each measurement stores `value`, `unit`, `raw`, `kind ∈ {reported, not_reported, unknown, unavailable, not_applicable, not_extracted, derived}`, `basis` (O₂ volume/mole), `source_report_id`, `source_page`, `locator`, `quote`, `verification_status`;
- `derived` requires a `derivation` note; original value is never overwritten;
- no numeric defaults anywhere (missing ≠ zero).

Drop P5's `organism`, `assay_type`, `mission` columns (biology-domain leftovers). P4's SQLite tables map onto P3 (`files` → report file metadata, `pages` → `report_pages`, `processing_log` → `ingestion_records`).

## 3. Cross-cutting decisions

| Topic | Decision | Reason |
|---|---|---|
| Architecture | Modular monolith: one FastAPI app, modules `ingest`, `search`, `assistant`, `experiments`, `admin` | Matches every document; no microservices |
| API prefix | `/api` | All documents agree |
| Error format | P5's `{"error":{code,message,details,request_id}}` | Already implemented and tested |
| Admin auth | P5 `X-API-Key`, fail-closed | Exists; swap for accounts only if scope X-5 resolves that way |
| AI | Provider adapter interface (`generate(prompt) → text`), off by default; `/api/ask` returns retrieval-only results with an explicit "generation not configured" state until a key is set | Honors handoff's postponement while still delivering the challenge's evidence retrieval; no fake answers |
| Citations | Only from retrieved passages; validator rejects any cited ID not in the retrieved set | P7 plan |
| Insufficient evidence | Hard gate before any LLM call (score threshold + min passages) | P7 plan |
| Secrets | Env vars, `.env.example` placeholders only | All docs |
| Mobile | Responsive web first, PWA later; **no Android build** | Handoff §6; there is no mobile code |
| Branding | CTRL+SPACE everywhere; scientific concept unchanged | Master prompt |

## 4. Decisions only the owner can make

| ID | Question | Recommended answer |
|---|---|---|
| D-1 | Stack: Option A, B or C? | A, unless you can supply `D:\FlameLab` |
| D-2 | Is the `D:\FlameLab` Node repo real and available? | If yes, upload it before anything else |
| D-3 | AI provider for Phase 7 (OpenAI / Anthropic / Gemini / local Ollama) and is a key available? | Any one; Ollama if no budget |
| D-4 | Scope: the 4 core objectives (search, ask, compare, display) or the full ~58-feature list including community, challenges, rooms? | Core 4 for the hackathon; others later |
| D-5 | End-user accounts needed? | No for MVP (admin key only) |
| D-6 | Logo: approve a variant **without the NASA insignia** for app/icon/slides? | Yes — see §5 |
| D-7 | Who reviews extracted scientific values? | A named teammate; P8 requires human verification |

## 5. Logo handling

The artwork includes NASA's official insignia (top-left). NASA restricts use of its insignia, and displaying it in the app header, icon or slides could imply endorsement — which the project's own rules prohibit. Proposal: keep the artwork unchanged as the source file, and derive app assets (favicon, header mark, PWA icons, slide title) from the `ctrl + space` wordmark and the flame-hand crop, with the insignia removed. This is a recommendation, not a legal opinion; check the current NASA media-usage guidelines.

Design tokens drawn from the logo: background `#05070F` (space black), surface `#0B1426` (navy), accent blue `#2F6BFF`, flame `#FF6A1A`, ember red `#E5322D`, highlight `#FFC24A`, text `#F2F4F8` / `#9AA4B8`; monospace HUD typeface for labels (matches the LAT/LON readout).

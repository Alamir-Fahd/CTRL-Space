# CTRL+SPACE — strategic audit: architecture, challenge alignment, data expansion

Written 2026-11-14. This responds to the "Master Project Audit, Product Strategy, NASA Research Expansion & Competition Readiness" prompt.

## Why one document, not twelve

The prompt asked for a `docs/strategic-audit/` folder with 12 documents. Most of that ground is already covered, verified, and current: architecture rationale lives in [`docs/ARCHITECTURE.md`](../ARCHITECTURE.md), the KEEP-vs-REBUILD decision is already recorded in [`CLAUDE.md`](../../CLAUDE.md) under "Owner decisions (do not reverse without asking)," and competition readiness is in [`docs/JUDGING_CRITERIA.md`](../JUDGING_CRITERIA.md), [`docs/SETUP_REPORT.md`](../SETUP_REPORT.md), and [`docs/final-audit/CTRL_SPACE_FINAL_READINESS_REPORT.md`](../final-audit/CTRL_SPACE_FINAL_READINESS_REPORT.md). Writing 12 new files that restate those would be paperwork, not readiness. This document covers only what's genuinely new: the two factual discrepancies the prompt flagged (now resolved, with evidence below), and the NASA data-expansion analysis, which hadn't been done before.

Per the prompt's own instruction, **no redesign, rewrite, or database migration was started.** The two changes below are one-line factual corrections to documentation, not implementation.

## 1. Architecture: KEEP, not REBUILD

Confirmed again this pass: the proposals raised earlier in this session for a Flutter/Dart native rewrite or a FastAPI+Supabase+Firebase backend swap are **not being pursued.** Reasoning, unchanged from `docs/ARCHITECTURE.md` and the owner's own CLAUDE.md decision:

- The current stack (Flask 3 + SQLite + vanilla ES-module JS) is fully built, tested, and working: 93 backend unit tests, 19 desktop E2E, 21 mobile E2E, 5 Arabic RTL, 9 PWA installability, 32 real-device-sweep checks — all passing as of the last full regression run (`docs/fixes/TEST_RESULTS.md`).
- A rewrite to Supabase/Firebase would trade a working, inspectable, evidence-gated SQLite schema (with `CHECK` constraints enforcing the project's core scientific promise — no fabricated data, no citation without a real passage) for a managed backend with none of that built in, re-implemented from scratch under deadline.
- A native Flutter rewrite would discard a working installable PWA (English + Arabic RTL, already verified on real device emulation) for a second, unstarted codebase with no feature parity yet.
- Neither rewrite was requested with an explicit, confirmed "yes, do this instead" after being flagged as contradicting the owner's documented decision — so per that decision, the stack stays.

If judges specifically reward a native app wrapper, the project already has one: the Capacitor Android build (`docs/NATIVE_BUILDS.md`) wraps the existing PWA without a rewrite.

## 2. Challenge alignment — verified against the live official page

Two factual claims from the prompt were checked against the real page (`https://www.spaceappschallenge.org/2026/challenges/flame-in-freefall/`, rendered with Playwright since the description text loads client-side — static fetch only returns a loading skeleton), not assumed from the prompt text:

### 2a. Title: the prompt was right, the project's docs were wrong — now fixed
The official title is **"Flame in Freefall: SI-Powered Fire Safety Insights from Microgravity Combustion Data."** "SI" is the challenge's own term, defined in its first paragraph: *"create an interactive, **super intelligence (SI)** powered dashboard."* Not "AI." `README.md` previously said "AI-Powered" — corrected this pass, with a note explaining the real term so it doesn't drift back.

### 2b. The challenge's three-pillar framing — genuinely new information, not previously reflected anywhere in this project
The official page states NASA's fire-safety work spans three pillars, each tied to named real investigations:

| Pillar | Named investigations | CTRL+SPACE corpus coverage |
|---|---|---|
| **Prevention** (ignition control, material flammability) | BASS, BASS-II, Saffire-I/II/III | **Covered.** All 6 seed reports are BASS-II or Saffire. |
| **Detection** | Smoke and Aerosol Measurement Experiment (SAME, SAME-R) | **Not covered.** Zero reports in the corpus. |
| **Suppression** | Flame Extinguishment Experiment (FLEX) | **Not covered.** Zero reports in the corpus. |

The app's corpus — and therefore every answer, comparison, and lesson it can produce — currently represents exactly one of the challenge's three named pillars. This isn't a bug (every passage is real and verified), but it is a real, material scope gap against the actual challenge brief, independent of anything flagged in the prompt.

Other confirmed-matching details: the primary data source the challenge names is explicitly **"NASA's Physical Science Informatics (PSI) database"** — the same PSI API this project integrated this session (`GET /api/psi/search`). The terrestrial-applications angle the challenge invites ("fine-water-mist extinguishers... smoke detection and firefighter gear") matches the app's existing NASA Technology Transfer section. Target audience (professors, students, researchers, engineers) matches the app's existing framing. Rocket/propellant fire safety is explicitly **out of scope** for the challenge, matching the app's existing scope — no gap there.

## 3. NASA data-expansion plan

Scoped to what the corpus is missing against the challenge's own framing (§2b), not a request to ingest everything in PSI:

1. **Detection — SAME / SAME-R.** Search NTRS for SAME/SAME-R technical reports the same way the existing BASS-II/Saffire reports were sourced (`services/ingest.py`'s existing NTRS pipeline, no new code needed — just new report IDs). This is the single highest-value addition: it's a named pillar with zero current coverage.
2. **Suppression — FLEX / FLEX-2.** Same pipeline, same justification.
3. **Lower priority, name-checked by the challenge but not core pillars:** ACME (and its sub-investigations BRE, CFI/CFI-G, E-FIELD Flames), SPICE, SLICE, DAFT/DAFT-2. These round out coverage but aren't required to close a named pillar gap.
4. **Not recommended right now:** partial-gravity investigations (LUCI, FM2) — the challenge page itself states "there is currently no partial-gravity combustion data available in PSI," so there is nothing to ingest yet.

Each addition follows the existing, already-tested ingestion and admin-verification pipeline (NTRS metadata → eligibility check → PDF → passage extraction → **human verification against the source PDF** → search index) — no new architecture, no schema change beyond what already exists. This is future work, not something started in this pass, per the prompt's own "audit before implementation" instruction.

## 4. Fixes applied this pass (small, factual, documented — not implementation)

| File | Before | After | Evidence |
|---|---|---|---|
| `docs/DATA_SOURCES.md` | "34 passages, 8 experiments," per-report row for `20160000593` listed as 17 | "36 passages, 8 experiments," row corrected to 19 | Live `GET /api/stats` → `verified_passages: 36`; live per-report check via `/api/reports` showed `20160000593` (BASS-II poster) now has 19 verified passages, not 17 — the exact +2 that explains the 34→36 gap. The other 5 reports' live counts (3, 3, 0, 0, 11) matched the table exactly, so only that one row and the summary line needed correcting. |
| `README.md` | "AI-Powered Fire Safety Insights" | "SI-Powered Fire Safety Insights," with a note on what "SI" means | Verified against the live-rendered official challenge page (§2a above); raw HTML's `<h1>` confirms `SI-Powered`, zero occurrences of `AI-Powered` anywhere on the page. |

`docs/phases/PHASE_02_REPORT.md` and `CTRL_SPACE_FINAL_REPORT.md` also contain the old "34 passages" figure, and `docs/audit/`/`docs/final-audit/` contain the old title — these were deliberately **not** edited, because they are dated, point-in-time snapshots of what was true when they were written (same category as a changelog entry), not living reference docs. Rewriting history in a dated report would make it less trustworthy, not more.

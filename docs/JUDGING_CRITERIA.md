# CTRL+SPACE — NASA Space Apps 2026 judging criteria assessment

Honest status against the five official criteria, checked against the code and a live run on 2026-11-13. Legend: ✅ implemented and verified · 🟡 partial · ❌ not done (explicitly, with why).

## 1. Impact

| What | Status |
|---|---|
| Research Impact Dashboard (`/app/impact`, `GET /api/impact`) | ✅ real counts from this running instance: reports indexed, verified passages, experiments, questions processed, evidence-grounded answers, active sessions — not sample data |
| Scientific validation numbers surfaced alongside impact (recall@6, MRR, gate pass rate, correct-refusal rate) | ✅ read live from `eval/results.json`, re-run on 2026-11-13 |
| Controlled usability study, manual research vs. CTRL+SPACE-assisted | ❌ **not run.** This needs real human test subjects and a controlled protocol; nothing here would be honest without them. The dashboard says so explicitly rather than estimating a number. |
| Beginner/advanced explanations, glossary, visual learning | 🟡 Learning Studio (5 lessons) and the AI assistant's two answer depths exist; a dedicated glossary screen was not built this round |

## 2. Creativity

| What | Status |
|---|---|
| Scientific Knowledge Graph | ❌ not built. Evaluated and deprioritized: with 6 reports / 8 experiments the relational structure is already fully visible through Experiments → Compare → Visualization Lab; a graph view would be a visual restatement of the same ~15 nodes, not new insight, for significant UI effort. Revisit if the corpus grows. |
| Research Gap Detector | ✅ already existed (`/api/gaps`, corpus-scoped, typed gaps, surfaced via the assistant's “Generate research questions” action) — not new this round, just confirmed working |
| Scientific Contradiction Detector | ❌ not built. Evaluated and deprioritized: only 8 experiments across 2 programs exist, so a corpus-wide “contradiction scan” would mostly surface single-pair differences the Compare screen (Notes tab, `comparison_levels`) already explains with the same confound warnings this feature would need. Would need a larger corpus to produce real signal. |
| AI Research Copilot (question → reports → evidence → compare → limitations → brief → follow-ups) | ✅ already existed as the assistant's follow-up action chips (`fexplain`/`fevidence`/`fcompare`/`flimits`/`fquestions`/`saveans`) plus the research-brief generator — confirmed working, not renamed or restructured |
| NASA Physical Sciences Informatics (PSI) live integration | ✅ new this round — genuine differentiator: most student projects citing PSI link to the search page; this one calls PSI's own JSON API server-side and lets users browse/cite real investigations in-app |

## 3. Validity

| What | Status |
|---|---|
| Every statement traceable to report/NTRS ID/page/passage/experiment | ✅ unchanged from before — citation objects always carry `report_id`, `locator`, source URL |
| Verification statuses (verified / needs-verification / not-reported / not-extracted) | ✅ already existed (`passages.verified`, `experiment_fields.state`) |
| Scientific Validation Benchmark: recall@K, MRR, citation accuracy, groundedness, refusal behavior | ✅ already existed (`scripts/evaluate.py`, `eval/results.json`); re-run fresh on 2026-11-13: recall@6 = 0.958, MRR = 0.854, gate pass rate = 1.0 on 12 answerable questions, 4/4 unsupported questions correctly refused. Now also surfaced live in the Impact Dashboard, not just a static file. |
| Precision@K, hybrid retrieval vs. BM25 comparison | ❌ not added. No second retrieval method exists to compare against in this build (dense models are documented as unavailable offline); adding Precision@K to a single-method benchmark wouldn't add real signal. |
| Data integrity (measured/reported/derived/missing distinction, original units preserved) | ✅ unchanged — `value_type`/`normalized` fields, never fabricated |
| Reproducible research session export | ✅ already existed (conversation/comparison/collection export, research brief) |
| Explicit scientific-limitations statement | ✅ new this round — added to the About screen and Judge Mode: “not a validated spacecraft fire-prediction system or NASA safety-certification tool” |

## 4. Relevance

| What | Status |
|---|---|
| Dedicated Flame-in-Freefall / combustion explainer | ✅ new this round — Combustion Research Hub (`/app/combustion`): NASA Glenn combustion-science background, A Researcher's Guide to ISS Combustion Science, embedded NASA ScienceCasts video, all linking to their real NASA sources |
| NASA Research Coverage by program/category | ✅ already existed in the Scientific Visualization Lab (`/app/viz`: reports/experiments by program, evidence completeness, oxygen/temperature/flow/pressure distributions) — confirmed working |
| NASA data traceability throughout | ✅ unchanged |
| Historical spacecraft fire-safety case studies (Apollo 1, Apollo 13, Mir) | ✅ new this round — written from the official NASA SMA/history pages, each citing its source, clearly separated from the experimental PSI/NTRS data |
| NASA technology-transfer section (firefighter air tanks, fire detector, fire-resistant attire) | ✅ new this round — from NASA Spinoff, each with its source link |
| Required non-endorsement disclaimer | ✅ added verbatim to the Combustion Hub, case studies, PSI pages, and About |

## 5. Presentation

| What | Status |
|---|---|
| Judge Mode (`/app/judge`) — overview, challenge alignment, innovations, data sources, AI architecture, links to impact + live demo, no admin login required | ✅ new this round |
| Live Demo Scenario (search → evidence → ask → citations → compare → missing data → brief) | ✅ already existed (`/app/demo`, backed by `GET /api/demo/preflight`) — confirmed still working, linked from Judge Mode rather than duplicated |
| Interactive landing-page storytelling (problem → NASA background → challenge → solution → AI architecture → live demo → impact) | 🟡 the desktop landing page already covers problem/solution/innovation/impact/“how it works”; Judge Mode now adds the NASA-background and AI-architecture framing on the mobile side. A single unified narrative page spanning both was not built this round. |

## What this round actually changed

New: `GET /api/psi/search` (+ `psi_cache` table), `GET /api/impact`; mobile screens `/app/combustion`, `/app/combustion/psi[,/:id]`, `/app/combustion/case/:id`, `/app/impact`, `/app/judge`; CSP extended for `psi.nasa.gov` images and a `youtube.com` video embed; scientific-limitations and source-compliance text added to About.

Explicitly not attempted, and why: a human usability study (needs real subjects), a knowledge graph and contradiction detector (evaluated, more UI cost than signal at this corpus size), Precision@K / hybrid-retrieval comparison (nothing to compare against yet).

Verified 2026-11-13 on this machine after every change in this round: backend 90/90, desktop E2E 19/19, mobile app 20/20, Arabic 5/5, PWA 9/9.

# Data sources

All content comes from the **NASA Technical Reports Server (NTRS)**, https://ntrs.nasa.gov, retrieved in two batches: the original 6-report Prevention-only seed on **2026-11-12**, and 4 more reports covering Detection and Suppression on **2026-11-14** (see "Why these reports" below). CTRL+SPACE stores report metadata and short verbatim passages, and links every passage to its NTRS record. It is not affiliated with or endorsed by NASA.

## Reports in the corpus

| NTRS ID | Title | Type, date | Program | Verified passages | Citations by |
|---|---|---|---|---|---|
| [20150019858](https://ntrs.nasa.gov/citations/20150019858) | Results from On-Board CSA-CP and CDM Sensor Readings During the BASS-II Experiment in the MSG | Conference paper ICES-2015-196, 2015-07-12 | BASS-II | 11 | printed page number |
| [20160000593](https://ntrs.nasa.gov/citations/20160000593) | Combustion of Solids in Microgravity: Results from the BASS-II Experiment | Poster, 2014-10-23 | BASS-II | 19 | section heading (extract has no page breaks) |
| [20240007488](https://ntrs.nasa.gov/citations/20240007488) | Preliminary Results from the Saffire VI Experiment (presentation) | Presentation, 2024-07-21 | Saffire | 3 | printed slide number |
| [20240002981](https://ntrs.nasa.gov/citations/20240002981) | Preliminary Results from the Saffire VI Experiment | Conference paper ICES-2024-365, 2024-07-21 | Saffire | 3 | NTRS record abstract |
| [20210011385](https://ntrs.nasa.gov/citations/20210011385) | BASS-II Summary Report | Technical memorandum E-19939, 2021-10-01 | BASS-II | 0 (metadata only) | — |
| [20170008805](https://ntrs.nasa.gov/citations/20170008805) | Results of Large-Scale Spacecraft Flammability Tests | Presentation, 2017-07-16 | — | 0 (metadata only) | — |
| [20130000422](https://ntrs.nasa.gov/citations/20130000422) | Particle Morphology and Size Results from the Smoke Aerosol Measurement Experiment-2 | Conference paper AIAA 2012-3536, 2012-07-15 | SAME | 15 | printed page number |
| [20150010172](https://ntrs.nasa.gov/citations/20150010172) | Particle Morphology Results from the Smoke Aerosol Measurement Experiment-Reflight | Presentation, 2012-01-12 | SAME | 10 | printed page number |
| [20090014812](https://ntrs.nasa.gov/citations/20090014812) | Multi-User Droplet Combustion Apparatus - Flame Extinguishment Experiment | Project summary JSC-17962-27, 2009-02-23 | FLEX | 12 | printed page number |
| [20150023456](https://ntrs.nasa.gov/citations/20150023456) | Detailed Results from the Flame Extinguishment Experiment (FLEX) March 2009 to December 2011 | Technical publication NASA/TP-2015-216046, 2015-11-01 | FLEX | 14 | printed page number |

**87 passages, 10 experiments.** How they were made: each passage was copied verbatim from the NTRS PDF text or record page on the retrieval date, then checked against the source PDF before being marked verified (`POST /api/admin/passages/<id>/review`) — unverified auto-chunked text never backs an AI answer or an experiment value. Experiment values were taken only from those verified passages; anything shown only in a figure, a table caption, or not stated, is recorded as *Not extracted* or *Not reported* with a reason, never invented or guessed. The 4 new reports' auto-chunked passages (612 of them) were not all reviewed — only the ones listed as "verified passages" above were read and confirmed; the rest sit in `passages` with `verified=0` and are invisible to the app until an admin reviews them too.

### Why these 4 reports (2026-11-14)

The official NASA Space Apps 2026 "Flame in Freefall" challenge frames spacecraft fire safety as three pillars: **Prevention** (BASS, BASS-II, Saffire), **Detection** (the Smoke and Aerosol Measurement Experiment, SAME/SAME-R), and **Suppression** (the Flame Extinguishment Experiment, FLEX) — see `docs/strategic-audit/STRATEGIC_AUDIT.md` §2b. Before this pass, the corpus covered only Prevention. Real NTRS reports for SAME and FLEX were found via NTRS's public search API (`POST /api/citations/search`), checked for public eligibility (`distribution: PUBLIC`, `disseminated: DOCUMENT_AND_METADATA`), and ingested through the app's existing, unmodified ingestion pipeline (`services/ingest.py`) — the same code path used for the original 6 reports, not a special case.

Two new experiments were added from these reports' verified passages, following the same rule as every other experiment (`backend/ctrlspace/services/experiments.py`): a value is only ever `reported` when it cites a verified passage, and fields with no clean single reported value (e.g. FLEX's droplet-translation flow speed, or SAME-2's sample geometry) are honestly left `not_extracted`/`not_reported`/`not_applicable` rather than guessed:
- `same2-smoke` — **SAME-2: Spacecraft Material Smoke Particle Sizing**, from report 20130000422.
- `flex-mdca` — **MDCA-FLEX: Droplet Combustion Flame Extinguishment**, from reports 20090014812 and 20150023456.

One new lesson, `detection-and-suppression` ("How a spacecraft fire is detected and put out"), was added to the Learning Studio, citing 9 of the newly verified passages across its 5 sections — the first lesson in the app that isn't Prevention-only.

Real NASA Image and Video Library photos were added for the two new programs too (`frontend/app/js/core.js`'s `PROGRAM_PHOTOS`), verified the same way as the original BASS-II/Saffire photos: searched by name, matched by reading the real description text, and confirmed to return `200 image/jpeg` before use — e.g. `iss024e008351` (Shannon Walker working SAME in the Microgravity Science Glovebox during Expedition 24, the exact flight SAME-2's report describes) and `iss043e190395` (Terry Virts preparing the MDCA for "FLame Extinguishment" runs).

## Known limits

- Copyright: the two Saffire VI records state "portions of document may include copyright protected material", so only short excerpts are stored.
- Report 20170008805's title does not mention Saffire. Its link to Saffire comes from earlier project research and is unconfirmed, so its program is left blank.
- Figures and tables are not digitised; spread-rate curves in the BASS-II poster, and the chart/graph pages in the SAME presentation and the 314-page FLEX technical publication, are therefore not available as numbers — only passages that were legible as plain text were verified.
- 20150023456 (FLEX detailed results) is a 314-page, 478-passage report; only 14 representative passages (abstract, hardware, procedure) were verified, not the hundreds of individual per-droplet test narratives later in the document. Treat CTRL+SPACE's coverage of it as an introduction, not a full digitisation.
- NTRS asks harvesters to check `GET /api/citations/redistributions` weekly. That check is **not implemented** yet (see Phase 4 report).

## NTRS API used by the importer

`GET /api/citations/{id}`, `GET /api/citations/{id}/downloads`, then the listed PDF link. No key required. Limits from NASA's OpenAPI documentation: 500 requests per 15 minutes (client spaces calls ≥ 1.8 s), retries with backoff on 429/5xx. Only `Public` records not disseminated as `NONE` / `METADATA_ONLY` keep their documents.

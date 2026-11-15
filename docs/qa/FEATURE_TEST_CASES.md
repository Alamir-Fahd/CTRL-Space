# CTRL+SPACE — feature test cases

Format: ID | Scenario | Steps (condensed) | Expected | Actual | Status | Evidence. All "Actual" values are real observed results from this pass (2026-11-13), not expected-result copies.

## Dashboard (TC-DASH)

| ID | Scenario | Expected | Actual | Status | Evidence |
|---|---|---|---|---|---|
| TC-DASH-001 | Dashboard loads | Stats + recent reports render | Rendered, 0 console errors | PASS | `e2e/test_e2e.py` "01 Home" |
| TC-DASH-002 | Stats match `/api/stats` | Displayed counts = API counts | Verified 6 reports / 36 passages / 8 experiments both places | PASS | `test_health_and_stats` + live `curl /api/stats` this pass |
| TC-DASH-003 | Backend unreachable | Honest offline/server-down state, no crash | Confirmed: "Server unreachable" banner shown, then recovers to "Online" once reachable (observed live on the Android emulator this session) | PASS | Android emulator screenshots this session; `mobile_app_test.py` "server-down vs offline state" |

## Research Discovery (TC-DISC)

| ID | Scenario | Expected | Actual | Status | Evidence |
|---|---|---|---|---|---|
| TC-DISC-001 | Valid search ("microgravity combustion") | Relevant reports returned, ranked | Returns ranked matches | PASS | `test_reports_pagination_sort_filter_search`, `test_ranked_results_and_validation` |
| TC-DISC-002 | No matching results | Informative empty state | Empty-state message with "clear filters" action | PASS | `e2e/test_e2e.py` Journey A |
| TC-DISC-003 | Program/evidence filters | Only matching records shown | Verified via `test_discovery_filters` | PASS | `test_discovery_filters` |
| TC-DISC-004 | Open a result → report details | Correct report page | Navigates correctly | PASS | `e2e/test_e2e.py` Journey A |

## Evidence Library (TC-LIB)

| ID | Scenario | Expected | Actual | Status | Evidence |
|---|---|---|---|---|---|
| TC-LIB-001 | Load library | Reports list renders | Renders, "Evidence & media" tabs work | PASS | `mobile_app_test.py` "12 Evidence library" |
| TC-LIB-002 | Verified-evidence filter | Only verified-passage reports shown | `evidence=verified` filters correctly | PASS | `test_discovery_filters` |
| TC-LIB-003 | Passage search | Relevant verified passages, unverified excluded | Confirmed | PASS | `test_unverified_passages_not_searchable` |
| TC-LIB-004 | NASA source link | Links to the correct NTRS record | `https://ntrs.nasa.gov/citations/{id}` built from real ID | PASS | code review (`core.js` `ntrs()`), live click-through in `test_e2e.py` Journey A |

## Report Details (TC-REPORT)

| ID | Scenario | Expected | Actual | Status | Evidence |
|---|---|---|---|---|---|
| TC-REPORT-001 | Open valid report | Metadata + evidence shown | Confirmed | PASS | `test_report_detail_never_leaks_raw_metadata` |
| TC-REPORT-002 | Invalid report ID (`99999999`) | 404 | **Live probe this pass: `GET /api/reports/99999999` → 404** | PASS | live `curl`, this pass |
| TC-REPORT-002b | Malformed report ID (`badformat`) | 400 `invalid_id` | **Live probe: → 400, `"Report IDs are 8 to 12 digits."`** | PASS | live `curl`, this pass |
| TC-REPORT-003 | Save report while signed in | Appears in saved research | Confirmed | PASS | `test_crud_export_and_isolation`, live register→save→restart probe this pass |
| TC-REPORT-004 | Passage traceability | Source report + locator traceable | `cite()`/`passage()` always carry `report_id`+`locator` | PASS | code review + `test_ranked_results_and_validation` |
| TC-REPORT-005 | Pending report hidden from public | 404/hidden until approved | Confirmed | PASS | `test_pending_report_hidden_from_public` |

## AI Research Assistant (TC-AI)

See `AI_TEST_REPORT.md` for the full mocked-vs-evidence-only-vs-real-LLM breakdown. Summary:

| ID | Scenario | Expected | Actual | Status | Evidence |
|---|---|---|---|---|---|
| TC-AI-001 | Valid scientific question, no provider | Evidence-only structured brief | Confirmed, labeled "Retrieval-only" | PASS | `test_no_provider_returns_evidence_only` |
| TC-AI-002 | Too-short question (`"hi"`) | Validation rejection | Confirmed | PASS | `test_validation` |
| TC-AI-003 | Unsupported/unrelated question | Insufficient-evidence response, not invented | Confirmed | PASS | `test_gate_blocks_llm_for_unsupported_questions`, `test_model_says_insufficient` |
| TC-AI-004 | Provider errors/unavailable | Honest failure, no fake answer | Confirmed | PASS | `test_bad_json_and_provider_failures_are_honest` |
| TC-AI-005 | Fabricated citation in model output | Removed before reaching the user | Confirmed | PASS | `test_grounded_answer_and_fabricated_citation_removed` |
| TC-AI-006 | No provider configured | Clearly labeled evidence-only, not claimed as live inference | Confirmed (`"ai_provider":"none"` in `/api/health` throughout most of this pass) | PASS | `run.py check-ai` output + `/api/health` |
| TC-AI-007 | Real LLM inference | A configured provider actually answers | **See `AI_TEST_REPORT.md`** | See report | — |

## Experiment Explorer (TC-EXP)

| ID | Scenario | Expected | Actual | Status | Evidence |
|---|---|---|---|---|---|
| TC-EXP-001 | List experiments | 8 published experiments shown | Confirmed | PASS | `test_list_and_detail_states` |
| TC-EXP-002 | Invalid experiment ID | 404 | **Live probe this pass: `GET /api/experiments/does-not-exist` → 404** | PASS | live `curl`, this pass |
| TC-EXP-003 | Experiment details | Conditions/measurements/units/verification shown | Confirmed | PASS | `test_list_and_detail_states`, `test_experiment_fields_v3` |
| TC-EXP-004 | Missing value | Shown as "Not reported"/"Not extracted", never zero | Confirmed | PASS | `test_number_requires_unit_and_reported_state`, `test_invalid_states_and_ids_rejected` |

## Experiment Comparison (TC-CMP)

| ID | Scenario | Expected | Actual | Status | Evidence |
|---|---|---|---|---|---|
| TC-CMP-001 | Compare 2 valid experiments | Real conditions/measurements shown | Confirmed | PASS | `test_compare_warnings_units_and_chartable` |
| TC-CMP-002 | Below minimum (1 experiment) | 422 validation error | **Confirmed server-side**: `['bass2-mist']` → 422 | PASS | `test_compare_validation` |
| TC-CMP-003 | Above maximum (5 experiments) | 422, selection prevented | **Confirmed server-side**: 5-item list → 422 | PASS | `test_compare_validation` |
| TC-CMP-004 | Missing values across experiments | Stay explicitly missing | Confirmed | PASS | `test_compare_warnings_units_and_chartable` |
| TC-CMP-005 | Different programs/flow config | Methodology warnings shown | Confirmed | PASS | `test_flow_configuration_warning`, `test_comparison_levels` |
| TC-CMP-006 | Export comparison | Markdown with real data + sources | Confirmed | PASS | `test_comparison_export` |

## My Research / Workspace (TC-WORK)

| ID | Scenario | Expected | Actual | Status | Evidence |
|---|---|---|---|---|---|
| TC-WORK-001 | Create collection | Saved and listed | Confirmed; duplicate name → 409 | PASS | `test_crud_export_and_isolation` |
| TC-WORK-002 | Add report to collection | Appears correctly; nonexistent report → 404 | Confirmed | PASS | `test_crud_export_and_isolation` |
| TC-WORK-003 | Save note | Persists | **Live probe this pass: wrote a note, restarted the whole backend process, note still present** | PASS | live probe, this pass |
| TC-WORK-004 | Persistence after restart | Data survives | **Live probe this pass: registered user, saved report, wrote note → killed Python process → restarted → both still present via `GET /api/saved` and `GET /api/notes`** | PASS | live probe, this pass (see `QA_VERIFICATION_REPORT.md`) |
| TC-WORK-005 | Cross-user ownership | Other users get 404, not the data | Confirmed: export/delete/list/note all isolated | PASS | `test_crud_export_and_isolation` lines 316–322 |

## Learning Studio (TC-STUDIO)

| ID | Scenario | Expected | Actual | Status | Evidence |
|---|---|---|---|---|---|
| TC-STUDIO-001 | Open lesson | Correct content/objectives | Confirmed | PASS | `test_lessons_cite_only_verified_passages` |
| TC-STUDIO-002 | Complete lesson | Completion saved | Confirmed | PASS | `test_activity_recent_and_notes_list` |
| TC-STUDIO-003 | Invalid lesson ID | 404 | Confirmed | PASS | direct test, `tests/test_backend.py:537` |

## Challenges (TC-CH)

| ID | Scenario | Expected | Actual | Status | Evidence |
|---|---|---|---|---|---|
| TC-CH-001 | Submit valid attempt | Graded correctly, answers never sent to browser pre-submit | Confirmed | PASS | `test_challenges_hide_answers_grade_and_track` |
| TC-CH-002 | Draft persistence across reload | Draft restored | **Checked this pass: no draft-save endpoint exists, no client-side draft storage in `screens-c.js`.** | **NOT IMPLEMENTED** (not a regression — never built) | code review this pass; see `BUG_REPORT.md` |
| TC-CH-003 | Incorrect answer | Identified, feedback shown with source | Confirmed | PASS | `test_challenges_hide_answers_grade_and_track` |

## Community (TC-COM)

| ID | Scenario | Expected | Actual | Status | Evidence |
|---|---|---|---|---|---|
| TC-COM-001 | Create post | Appears in correct room | Confirmed | PASS | `test_community_posts_replies_reports_moderation` |
| TC-COM-002 | Empty post | Validation blocks it | Confirmed (title/body length constraints in schema) | PASS | DB `CHECK` constraints + `test_invalid_states_and_ids_rejected`-style coverage |
| TC-COM-003 | Reply | Associated with correct post | Confirmed | PASS | `test_community_posts_replies_reports_moderation` |
| TC-COM-004 | Delete another user's post | Denied (404, not the author) | **Confirmed**: non-author delete → 404 | PASS | `tests/test_backend.py:572` |

## Profile / Settings (TC-PROF)

| ID | Scenario | Expected | Actual | Status | Evidence |
|---|---|---|---|---|---|
| TC-PROF-001 | Profile retrieval | Correct signed-in user info | Confirmed | PASS | `test_bio_interests_and_onboarded_pref` |
| TC-PROF-002 | Update profile field | Persists | Confirmed | PASS | `test_profile_prefs_password_and_delete` |
| TC-PROF-003 | Signed-out access | 401, no data exposed | Confirmed | PASS | `test_requires_login` |

## Admin Dashboard (TC-ADM)

| ID | Scenario | Expected | Actual | Status | Evidence |
|---|---|---|---|---|---|
| TC-ADM-001 | Admin access | Dashboard loads | Confirmed live via device sweep this pass (Pixel 7 + Galaxy S9+: "sign in → admin dashboard") | PASS | `e2e/mobile_devices.py`, this pass |
| TC-ADM-002 | Ordinary user → admin endpoint | 403/401 | Confirmed | PASS | `test_admin_routes_require_admin` |
| TC-ADM-003 | Verify/reject passage | Status changes, audit recorded | Confirmed | PASS | `test_cannot_reject_passage_used_by_experiment`, audit assertions |
| TC-ADM-004 | Audit log records action | Action + detail present | Confirmed: `post.hide`, `experiment.rejected` etc. appear in `/api/admin/audit` | PASS | `tests/test_backend.py:581,732` |

## Scientific validation benchmark (new feature areas this session)

| ID | Scenario | Expected | Actual | Status | Evidence |
|---|---|---|---|---|---|
| TC-VAL-001 | Retrieval recall@6 / MRR | Measured, not estimated | recall@6 = 0.958, MRR = 0.854, gate pass rate = 1.0 (12 questions) | PASS | `scripts/evaluate.py`, re-run fresh this pass |
| TC-VAL-002 | Unsupported-question refusal | All 4 correctly refused | 4/4 | PASS | `scripts/evaluate.py`, re-run fresh this pass |
| TC-VAL-003 | PSI live integration | Real investigation data, not fabricated | 26 real combustion investigations returned from `psi.nasa.gov`'s own JSON API | PASS | live `curl`, this pass; `test_psi_search_cache_and_offline` |

## Security probes (live, this pass)

| ID | Scenario | Expected | Actual | Status | Evidence |
|---|---|---|---|---|---|
| TC-SEC-001 | SQL injection in search query (`'; DROP TABLE reports; --`) | No effect, parameterized query holds | Table intact, still 6 reports after | PASS | live `curl`, this pass |
| TC-SEC-002 | XSS payload in search query (`<script>alert(1)</script>`) | Not echoed unescaped | Raw `<script>` tag not present in response | PASS | live `curl`, this pass |
| TC-SEC-003 | Malformed report ID | 400, not 500 | Confirmed | PASS | live `curl`, this pass |

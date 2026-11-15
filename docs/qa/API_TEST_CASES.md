# CTRL+SPACE — API test cases

85 routes extracted directly from the Flask decorators in `backend/ctrlspace/api/*.py` (not from `docs/API.md`, which may lag). Grouped by category with real coverage evidence; full per-route detail lives in the backend test file referenced per group.

| Category | Routes | Valid | Invalid/validation | Auth required | Auth enforced | Boundary values | Evidence |
|---|---|---|---|---|---|---|---|
| System | `/api/health`, `/api/stats`, `/api/impact` | ✅ | n/a | No | n/a | n/a | `test_health_and_stats`, `test_impact_dashboard_counts_real_usage` |
| Reports | `GET /api/reports[/:id][/pages]` | ✅ | ✅ (400 malformed, 404 missing) | No (public reports only) | ✅ pending hidden | pagination limit/offset clamped | `test_reports_pagination_sort_filter_search`, `test_report_detail_never_leaks_raw_metadata`, `test_pending_report_hidden_from_public`, live probes this pass |
| Search | `GET /api/search` | ✅ | ✅ | No | n/a | n/a | `test_ranked_results_and_validation`, `test_unverified_passages_not_searchable` |
| Assistant | `POST /api/ask`, `/api/assistant/ask`, `/api/analyze`, `/api/brief`, `GET /api/gaps` | ✅ (evidence-only; real-LLM in `AI_TEST_REPORT.md`) | ✅ (length validation, rate limit) | Optional (anonymous allowed, not persisted) | ✅ | question length 3–400 chars | `test_validation`, `test_rate_limit`, `test_anonymous_ask_not_persisted`, `test_gaps_are_corpus_scoped` |
| Experiments | `GET /api/experiments[/:id]`, `POST /api/compare[/ai][/export]` | ✅ | ✅ (404 unknown, 422 out-of-range count) | No (published only) | ✅ | min 2 / max 4 experiments enforced server-side | `test_list_and_detail_states`, `test_compare_validation`, live 404 probe this pass |
| Auth | `/api/auth/register`, `/login`, `/logout`, `/me`, `/forgot`, `/reset` | ✅ | ✅ (duplicate email, wrong password, bad token) | Mixed | ✅ | rate-limited login attempts | `test_register_validation_and_duplicates`, `test_login_wrong_password_and_rate_limit`, `test_password_reset_flow` |
| Collections / Notes | `/api/collections*`, `/api/notes*`, `/api/experiment-notes*`, `/api/research-notes` | ✅ | ✅ (409 duplicate name, 404 nonexistent item) | Yes | ✅ (401 if signed out, 404 cross-user) | note length limit | `test_crud_export_and_isolation`, `test_note_limits`, `test_requires_login` |
| Profile / sessions | `GET/PATCH /api/me`, `/api/me/password`, `/api/me/sessions*`, `/api/me/activity`, `/api/me/export` | ✅ | ✅ | Yes | ✅ | n/a | `test_profile_prefs_password_and_delete`, `test_sessions_privacy_and_export`, `test_activity_recent_and_notes_list` |
| Learning | `/api/lessons[/:id][/complete]`, `/api/challenges[/:id][/attempts]` | ✅ | ✅ (404 unknown lesson) | Mixed (complete/attempt need login) | ✅ | n/a | `test_lessons_cite_only_verified_passages`, `test_challenges_hide_answers_grade_and_track` |
| Community | `/api/rooms*`, `/api/posts*`, `/api/community/recent` | ✅ | ✅ (empty-post validation, non-author delete → 404) | Mixed | ✅ | title/body length constraints | `test_community_posts_replies_reports_moderation`, `test_community_recent_and_edit` |
| Notifications | `/api/notifications`, `/api/notifications/read` | ✅ | n/a | Yes | ✅ | n/a | `test_notifications_from_real_events` |
| Conversations | `/api/conversations*` | ✅ | ✅ (404 cross-user) | Yes | ✅ | n/a | `test_conversation_history_context_and_export` |
| Saved answers | `/api/answers/*` | ✅ | n/a | Yes | ✅ (owner-only) | n/a | `test_save_answer_owner_only`, `test_answer_feedback_owner_only` |
| Admin | 14 `/api/admin/*` routes | ✅ | ✅ | Yes (admin role) | ✅ (401/403 for non-admin, tested for every route) | n/a | `test_admin_routes_require_admin` (loops every admin route), `test_admin_user_management_and_last_admin` |
| NASA Image Library | `GET /api/media/search` | ✅ (mocked network in tests; real in production) | ✅ (422 query length, 503 honest offline) | No | n/a | query length 2–80 | `test_nasa_media_search_cache_and_offline` |
| NASA PSI | `GET /api/psi/search` | ✅ (mocked in unit test; **real live call succeeded this pass**, 26 real investigations) | ✅ (422, 503 offline fallback) | No | n/a | query length 2–80 | `test_psi_search_cache_and_offline`, live `curl` this pass |
| Client errors | `POST /api/client-errors`, `GET /api/admin/client-errors` | ✅ | n/a | Mixed | ✅ | truncated to safe lengths | `test_client_error_monitoring` |

## Contract consistency
Every error response follows the same shape (`{"error": {"code","message","details","request_id"}}`) — enforced by a shared error handler, verified in `test_error_shape_and_request_id` and observed directly in every live probe this pass (e.g. the malformed-report-ID 400 above returned exactly this shape).

## Performance (measured, not estimated)
From `eval/results.json`, re-run fresh this pass, in-process (no network hop):

| Endpoint | p50 | p95 | n |
|---|---|---|---|
| `GET /api/search` | 0.33 ms | 0.53 ms | 40 |
| `GET /api/reports?q=` | 0.53 ms | 0.66 ms | 40 |
| `POST /api/compare` (3 experiments) | 0.85 ms | 1.12 ms | 40 |
| `POST /api/ask` (no provider) | 3.27 ms | 6.56 ms | 40 |
| Search index rebuild | 2.8 ms | 3.65 ms | 10 |

# Security

Audit date 2026-11-12, against this repository. **PASS** means verified by an automated test or by direct inspection (file named); **LIMITATION** means a known gap.

| Area | Control | Status | Evidence |
|---|---|---|---|
| Secrets | Keys only in env vars; `.env` git-ignored; `.env.example` has placeholders only; AI key never reaches the browser | PASS | `.gitignore`, `.env.example`, `services/assistant.py` (server-side calls) |
| Passwords | PBKDF2-SHA256, 310,000 iterations, 16-byte salt, constant-time compare | PASS | `services/auth.py`; test `test_password_hashing` |
| Account enumeration | Same 401 message for unknown email and wrong password; dummy hash keeps timing similar | PASS | `api/__init__.py` login; test `test_login_wrong_password_and_rate_limit` |
| Duplicate registration | Returns 409 (reveals that an email exists; accepted trade-off without email verification) | LIMITATION | |
| Sessions | 256-bit random tokens, stored only as SHA-256; HttpOnly + SameSite=Strict cookie; `Secure` required in production; logout deletes server-side | PASS | tests `test_session_cookie_flags_and_lifecycle`, `test_tokens_stored_hashed`, `test_production_requires_secure_cookie` |
| CSRF | SameSite=Strict cookie + JSON-only bodies (415 otherwise) | PASS | test `test_validation` (415) |
| Authorization | Admin routes return 401 / 403; collections and notes are owner-scoped (other users get 404) | PASS | tests `test_admin_routes_require_admin`, `test_crud_export_and_isolation`; E2E "non-admin is denied" |
| Rate limits | Login 10/5 min per IP and 5/5 min per email; register 10/h; ask 20/5 min | PASS (single process) | tests `test_rate_limit`, login test |
| Input validation | Every parameter checked (types, ranges, lengths, ID patterns); 64 KB body limit | PASS | test `test_payload_limit` (413), validation tests |
| SQL injection | Parameterised queries throughout; dynamic table names only from fixed whitelists | PASS | `api/__init__.py` |
| XSS | All dynamic text HTML-escaped in the frontend (`esc()`); CSP `script-src 'self'`, no inline scripts or styles | PASS | `frontend/js/app.js`; test `test_security_headers_and_spa_fallback`; stored `<script>` note exported as text |
| Headers | CSP, X-Frame-Options DENY, nosniff, Referrer-Policy, Permissions-Policy, `Cache-Control: no-store` on API | PASS | `__init__.py` `_headers` |
| Path traversal | Static files via Werkzeug `send_from_directory`; source files not served | PASS | test `test_security_headers_and_spa_fallback` |
| Uploads / imports | PDF signature check, 60 MB cap, SHA-256 duplicate detection, random file names, exclusive create (never overwrite) | PASS | `services/ingest.py`; test `test_full_import…`, `test_rejects_non_pdf…` |
| Untrusted content | NASA text, PDFs and model output treated as data; prompt tells the model passage text is not instructions; citations validated against retrieved IDs | PASS | `services/assistant.py`; assistant tests |
| Error handling | Unified error JSON; stack traces only in server log | PASS | `register()` error handlers; test `test_error_shape_and_request_id` |
| Data exposure | `raw_metadata`, file hash and password hashes never returned by public or user endpoints | PASS | tests `test_report_detail_never_leaks_raw_metadata`, admin users test |
| Audit | Admin logins, imports, verifications, status changes logged | PASS | Ingestion test checks audit entries |

## Known limitations

1. Rate limiter and SQLite connection are per process: run one process (threads are fine). Multi-instance deployment needs Redis-style rate limiting and PostgreSQL.
2. No email verification and no self-service password reset (no email provider). An operator with server access can reset any account by running `python run.py create-admin EMAIL NAME` with a new password; this also makes the account an admin and signs out its sessions. A user-level reset that keeps the `user` role needs an email provider.
3. Imported PDFs are not virus-scanned (they come only from ntrs.nasa.gov and are never executed or served).
4. No HTTPS termination built in: put the app behind a reverse proxy with TLS in production.
5. NTRS weekly redistribution check not implemented.

# Authentication — implementation notes

The login/signup system already existed (real backend validation, PBKDF2-SHA256 password hashing, HttpOnly/SameSite session cookies, rate limiting) and was preserved as-is. This pass added the pieces that were genuinely missing: user categories, institution, and demo access — nothing in the existing auth flow was replaced or duplicated.

## What already worked (verified, not rebuilt)
- Backend-verified login/registration (`backend/ctrlspace/api/__init__.py`, `services/auth.py`).
- Show/hide password toggle (`data-act=togglepw`).
- Forgot password → admin-issued one-time reset link (no email service, by design — documented in `docs/USER_GUIDE.md`).
- Required-field, email-format, and password-strength validation, with real inline error messages.

## What was added this pass
1. **User category** (`student` / `researcher` / `educator` / `other`) — new `users.category` column, selected as a required radio-card group on signup, editable later from Edit Profile, shown on the Profile page.
2. **Institution** (optional) — new `users.institution` column, optional signup field, editable in Edit Profile.
3. **Demo account access** — see `DEMO_ACCOUNT_SETUP.md`.

## Files modified
- `backend/ctrlspace/db.py` — `category`, `is_demo`, `institution` columns (migration, `SCHEMA_VERSION` 5→6).
- `backend/ctrlspace/services/auth.py` — `CATEGORIES`, `validate_signup(..., category)`, `ensure_demo_account()`, `user_for_token()` now returns `category`/`is_demo`.
- `backend/ctrlspace/__init__.py` — calls `ensure_demo_account()` on real (non-test, non-production-unless-opted-in) startup.
- `backend/ctrlspace/api/__init__.py` — registration accepts/validates `category`/`institution`; login/me responses include them.
- `backend/ctrlspace/api/platform.py` — `user_public()`, `PATCH /api/me` accept `category`/`institution`.
- `frontend/js/api.js` — `register()` now takes `category`, `institution`.
- `frontend/app/js/screens-a.js` — `vRegister()` category cards, `vLogin()` demo section; `CATEGORIES` exported for reuse.
- `frontend/app/js/screens-d.js` — `vEditProfile()` category cards + institution field.
- `frontend/app/js/screens-c.js` — `vProfile()` shows real category label, institution, and a Demo badge.
- `frontend/app/js/main.js` — `copydemo`/`exploredemo` actions; registration/edit-profile submit handlers pass the new fields.
- `frontend/app/js/i18n.js` — Arabic translations for every new string.
- `tests/test_backend.py` — `test_signup_category_saved_and_validated`, `test_category_update_and_rejects_invalid`, `test_demo_account_seeded_once_real_login_works_never_in_memory_or_production`.
- `e2e/mobile_app_test.py` — registration test extended with category/institution; new "Demo access" test.

## Validation rules (server-side, not just UI)
- `category`: must be one of the four values, or omitted/empty — never silently accepted if invalid (`422 validation_error`).
- `institution`: up to 120 characters.
- Role is never accepted from the client on registration — it's hardcoded to `'user'` server-side; there is no way to self-register as admin.

## Commands to run
```
<venv-python> -m unittest discover -s tests          # 93 tests
<venv-python> e2e/mobile_app_test.py http://127.0.0.1:8000 "iPhone 14"   # 21 tests, server must be running
```

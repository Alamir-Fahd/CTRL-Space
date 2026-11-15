# Demo account — setup and security

## Credentials
```
Email:    demo.student@ctrlspace.local
Password: Demo@12345
```
Shown directly on the login screen (both mobile and visible via copy buttons), so judges/visitors never need to ask for them.

## How it's created
`backend/ctrlspace/services/auth.py` → `ensure_demo_account(con)`: checks for the account by email; if absent, inserts one real row (`role='user'`, `category='student'`, `is_demo=1`), with the password run through the same PBKDF2-SHA256 hashing as every other account — **never stored in plain text**, verified by `test_demo_account_seeded_once_real_login_works_never_in_memory_or_production`.

Called from `backend/ctrlspace/__init__.py`'s `create_app()`:
```python
if cfg['DATABASE'] != ':memory:' and (cfg['ENV'] != 'production' or os.environ.get('CTRLSPACE_SEED_DEMO') == 'true'):
    ensure_demo_account(con)
```

## Why these specific gates
- **Never in the test harness**: every test uses an in-memory (`:memory:`) database; the condition excludes it entirely, so none of the 93 backend tests ever see an extra account they didn't ask for.
- **Never in production without opt-in**: `CTRLSPACE_ENV=production` skips seeding unless `CTRLSPACE_SEED_DEMO=true` is explicitly set — satisfies "restrict automatic demo-account creation to development/demo setup."
- **Idempotent**: re-running `create_app()` (i.e. every server restart) checks for the existing row first and never duplicates or resets it.
- **Never admin**: hardcoded `role='user'`; the demo account has exactly the same permissions as any real student account, nothing more.

## The "Explore Demo" button
`frontend/app/js/screens-a.js` (`vLogin()`) renders the credentials and a real button (`data-act=exploredemo`). `frontend/app/js/main.js`'s handler calls the actual `/api/auth/login` endpoint with those exact credentials — **this is real authentication, not a frontend redirect that skips the backend.** Verified live: `curl -X POST /api/auth/login` with these credentials returns a real session cookie and `{"category":"student","is_demo":true}`.

## Environment variable
Add to `.env.example` / `docs/DEPLOYMENT.md` if deploying with demo access enabled in production:
```
CTRLSPACE_SEED_DEMO=true   # only set this if you want the demo account seeded even when CTRLSPACE_ENV=production
```

## Tests
- `test_demo_account_seeded_once_real_login_works_never_in_memory_or_production` (backend) — covers all of the above in one test.
- `e2e/mobile_app_test.py` "Demo access" — real browser click-through: credentials visible → Explore Demo → real session → profile shows Student category + Demo badge.

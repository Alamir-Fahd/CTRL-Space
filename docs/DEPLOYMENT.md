# Deployment

Nothing has been deployed. This guide describes a single-server deployment; every step must be verified on the target machine.

1. Server with Python 3.10+. `git clone` or unzip the project.
2. `python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt waitress`
3. `cp .env.example .env`, then set `CTRLSPACE_ENV=production`, `CTRLSPACE_COOKIE_SECURE=true`, and the AI settings if used.
4. `python run.py create-admin admin@yourdomain "Admin"`
5. Run **one** process: `waitress-serve --listen=127.0.0.1:8000 wsgi:app` (or `gunicorn -w 1 --threads 8 wsgi:app` on Linux).
6. Put Nginx or Caddy in front with HTTPS, proxying to 127.0.0.1:8000.
7. Check `https://yourdomain/api/health` returns `"status":"ok"`, then run through `docs/DEMO_SCRIPT.md`.

## Backups

The whole state is `data/ctrlspace.db` plus `data/originals/`. Back up with `sqlite3 data/ctrlspace.db ".backup backup-$(date +%F).db"` (safe while running) and copy `data/originals/`. Restore: stop the app, replace the files, start. `data/seed/corpus.json` can always rebuild the verified seed corpus (`python run.py reset-db`), but that deletes users, collections and imports.

## Schema changes

`db.py` has `schema_version` (currently 1). Tables are created with `IF NOT EXISTS`. Any future change must add an explicit migration step and be tried on a copy of the production database first.

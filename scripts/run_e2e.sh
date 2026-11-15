#!/usr/bin/env bash
# Starts CTRL+SPACE on a throwaway database, runs the browser journeys, stops the server.
set -u
cd "$(dirname "$0")/.."
if [ -x .venv/Scripts/python.exe ]; then PY=.venv/Scripts/python.exe
elif [ -x .venv/bin/python ]; then PY=.venv/bin/python
else PY=python3
fi
export CTRLSPACE_DATABASE="${CTRLSPACE_DATABASE:-/tmp/ctrlspace-e2e.db}"
rm -f "$CTRLSPACE_DATABASE"*
export CTRLSPACE_E2E_ADMIN_EMAIL=e2e.admin@ctrlspace.local CTRLSPACE_E2E_ADMIN_PASSWORD='E2eAdminPass2026'
CTRLSPACE_ADMIN_PASSWORD="$CTRLSPACE_E2E_ADMIN_PASSWORD" "$PY" run.py create-admin "$CTRLSPACE_E2E_ADMIN_EMAIL" "E2E Admin" >/dev/null
"$PY" run.py serve --port 8765 > /tmp/ctrlspace-e2e-server.log 2>&1 &
PID=$!
for _ in $(seq 1 40); do curl -sf http://127.0.0.1:8765/api/health >/dev/null && break; sleep 0.25; done
"$PY" e2e/test_e2e.py http://127.0.0.1:8765; CODE=$?
kill "$PID" 2>/dev/null; wait "$PID" 2>/dev/null
exit $CODE

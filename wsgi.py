"""Production entry point.  waitress-serve --listen=0.0.0.0:8000 wsgi:app   |   gunicorn -w 1 --threads 8 wsgi:app
Use ONE process: SQLite access and the rate limiter are per-process (see docs/SECURITY.md)."""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, 'backend'))
from run import load_dotenv  # noqa: E402

load_dotenv(os.path.join(ROOT, '.env'))
from ctrlspace import create_app  # noqa: E402

app = create_app()

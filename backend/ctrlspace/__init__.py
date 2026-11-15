"""CTRL+SPACE web application: Flask API + static frontend (modular monolith)."""
import os
import secrets
import threading
import uuid

from flask import Flask, g, jsonify, request, send_from_directory

from . import db as dbm
from .services.assistant import make_provider
from .services.auth import LIMITER, ensure_demo_account
from .services.search import INDEX

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
VERSION = '5.3.0'


def load_config(overrides=None):
    e = os.environ.get
    cfg = {
        'ENV': e('CTRLSPACE_ENV', 'development'),
        'DATABASE': e('CTRLSPACE_DATABASE', os.path.join(ROOT, 'data', 'ctrlspace.db')),
        'CORPUS': e('CTRLSPACE_CORPUS', os.path.join(ROOT, 'data', 'seed', 'corpus.json')),
        'STORAGE_DIR': e('CTRLSPACE_STORAGE_DIR', os.path.join(ROOT, 'data', 'originals')),
        'FRONTEND_DIR': os.path.join(ROOT, 'frontend'),
        'SESSION_HOURS': int(e('CTRLSPACE_SESSION_HOURS', '12')),
        'COOKIE_SECURE': e('CTRLSPACE_COOKIE_SECURE', 'false').lower() == 'true',
        'AI_PROVIDER': e('CTRLSPACE_AI_PROVIDER', 'none').lower(),
        'AI_MODEL': e('CTRLSPACE_AI_MODEL', ''),
        'AI_API_KEY': e('CTRLSPACE_AI_API_KEY', ''),
        'AI_BASE_URL': e('CTRLSPACE_AI_BASE_URL', ''),
        'AI_TIMEOUT': int(e('CTRLSPACE_AI_TIMEOUT', '45')),
        'AI_MAX_TOKENS': int(e('CTRLSPACE_AI_MAX_TOKENS', '1200')),
        'NTRS_BASE': e('CTRLSPACE_NTRS_BASE', 'https://ntrs.nasa.gov/api'),
        'MAX_CONTENT_LENGTH': 64 * 1024,
    }
    cfg.update(overrides or {})
    if cfg['AI_PROVIDER'] not in ('none', 'anthropic', 'openai', 'ollama'):
        raise RuntimeError('CTRLSPACE_AI_PROVIDER must be none, anthropic, openai or ollama')
    if cfg['ENV'] == 'production' and not cfg['COOKIE_SECURE']:
        raise RuntimeError('In production set CTRLSPACE_COOKIE_SECURE=true (HTTPS only).')
    return cfg


def create_app(overrides=None, provider=None, ntrs_client=None):
    cfg = load_config(overrides)
    if os.environ.get('SENTRY_DSN'):                      # optional, server-side only; untested without a DSN
        try:
            import sentry_sdk
            sentry_sdk.init(dsn=os.environ['SENTRY_DSN'], traces_sample_rate=0.0, send_default_pii=False)
        except ImportError:
            pass
    app = Flask(__name__, static_folder=None)
    app.config.update(cfg)
    app.config['MAX_CONTENT_LENGTH'] = cfg['MAX_CONTENT_LENGTH']
    con = dbm.connect(cfg['DATABASE'])
    dbm.init_db(con)
    app.extensions['db'] = con
    app.extensions['db_lock'] = threading.RLock()
    app.extensions['provider'] = provider or make_provider(cfg)
    app.extensions['ntrs'] = ntrs_client
    app.extensions['media_opener'] = (overrides or {}).get('MEDIA_OPENER')
    app.extensions['psi_opener'] = (overrides or {}).get('PSI_OPENER')
    # Demo account: never in the test harness (:memory: DB), never in production unless explicitly opted in.
    if cfg['DATABASE'] != ':memory:' and (cfg['ENV'] != 'production' or os.environ.get('CTRLSPACE_SEED_DEMO') == 'true'):
        ensure_demo_account(con)
    if os.path.exists(cfg['CORPUS']):
        if not con.execute('SELECT 1 FROM reports LIMIT 1').fetchone():
            dbm.seed(con, cfg['CORPUS'])
        else:
            dbm.upgrade_seed(con, cfg['CORPUS'])
    INDEX.build(con)
    LIMITER.reset()

    @app.before_request
    def _req():
        g.request_id = request.headers.get('X-Request-ID', '')[:64] or uuid.uuid4().hex
        g.db = con
        g.lock = app.extensions['db_lock']
        g.lock.acquire()

    @app.teardown_request
    def _done(_exc):
        lock = g.pop('lock', None)
        if lock:
            lock.release()

    @app.after_request
    def _headers(resp):
        resp.headers['X-Request-ID'] = g.get('request_id', '')
        resp.headers['X-Content-Type-Options'] = 'nosniff'
        resp.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        resp.headers['X-Frame-Options'] = 'DENY'
        resp.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
        resp.headers['Content-Security-Policy'] = (
            "default-src 'self'; img-src 'self' data: https://images-assets.nasa.gov https://psi.nasa.gov; style-src 'self' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; script-src 'self'; connect-src 'self'; frame-src https://www.youtube.com; frame-ancestors 'none'; "
            "base-uri 'none'; form-action 'self'")
        if request.path.startswith('/api/'):
            resp.headers['Cache-Control'] = 'no-store'
        elif request.path in ('/sw.js', '/', '/index.html', '/manifest.webmanifest') or request.path == '/app' or request.path.startswith('/app/') and '.' not in request.path.rsplit('/', 1)[-1]:
            resp.headers['Cache-Control'] = 'no-cache'
        return resp

    from .api import register
    register(app)

    @app.get('/')
    def index():
        return send_from_directory(cfg['FRONTEND_DIR'], 'index.html')

    @app.get('/<path:path>')
    def static_files(path):
        if path.startswith('api/'):
            return jsonify(error={'code': 'not_found', 'message': 'Unknown API route.', 'request_id': g.request_id}), 404
        full = os.path.join(cfg['FRONTEND_DIR'], path)
        if os.path.isfile(full):
            return send_from_directory(cfg['FRONTEND_DIR'], path)
        if path == 'app' or path.startswith('app/'):        # mobile app client: client-side routes
            return send_from_directory(os.path.join(cfg['FRONTEND_DIR'], 'app'), 'index.html')
        return send_from_directory(cfg['FRONTEND_DIR'], 'index.html')

    return app

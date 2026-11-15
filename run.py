#!/usr/bin/env python3
"""CTRL+SPACE command line.

  python run.py serve [--host 127.0.0.1] [--port 8000]   start the web application
  python run.py create-admin EMAIL "Name"                 create an admin, or promote an existing user and reset their password
  python run.py ingest NTRS_ID                            import a NASA NTRS record (needs internet)
  python run.py reset-db                                  delete the local database and re-seed from data/seed/corpus.json
  python run.py check-ai                                  verify the configured AI provider end to end (latency, valid JSON)
  python run.py preflight                                 competition demo readiness checklist
"""
import argparse
import getpass
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))


def load_dotenv(path='.env'):
    if os.path.exists(path):
        for line in open(path, encoding='utf-8'):
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())


def main():
    load_dotenv()
    from ctrlspace import create_app, load_config
    from ctrlspace.db import audit, now
    from ctrlspace.services import auth, ingest

    ap = argparse.ArgumentParser(description='CTRL+SPACE')
    sub = ap.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('serve'); s.add_argument('--host', default='127.0.0.1'); s.add_argument('--port', type=int, default=8000)
    a = sub.add_parser('create-admin'); a.add_argument('email'); a.add_argument('name')
    i = sub.add_parser('ingest'); i.add_argument('ntrs_id')
    sub.add_parser('reset-db')
    sub.add_parser('check-ai')
    sub.add_parser('preflight')
    args = ap.parse_args()

    if args.cmd == 'reset-db':
        path = load_config()['DATABASE']
        for suffix in ('', '-wal', '-shm'):
            if os.path.exists(path + suffix):
                os.remove(path + suffix)
        create_app()
        print(f'Database recreated and seeded at {path}')
        return
    app = create_app()
    con = app.extensions['db']
    if args.cmd == 'serve':
        print(f'CTRL+SPACE running at http://{args.host}:{args.port}  (AI provider: {app.extensions["provider"].name})')
        app.run(host=args.host, port=args.port, threaded=True, debug=False)
    elif args.cmd == 'create-admin':
        pw = os.environ.get('CTRLSPACE_ADMIN_PASSWORD') or getpass.getpass('Admin password: ')
        errors = auth.validate_signup(args.email, args.name, pw)
        if errors:
            sys.exit('; '.join(errors.values()))
        if con.execute('SELECT 1 FROM users WHERE email=?', (args.email.lower(),)).fetchone():
            uid = con.execute('SELECT id FROM users WHERE email=?', (args.email.lower(),)).fetchone()[0]
            con.execute('UPDATE users SET role=\'admin\', pw_hash=? WHERE id=?', (auth.hash_password(pw), uid))
            con.execute('DELETE FROM sessions WHERE user_id=?', (uid,))
            print('Existing user promoted to admin; password reset and all sessions signed out.')
        else:
            con.execute('INSERT INTO users (email,name,pw_hash,role,created_at) VALUES (?,?,?,?,?)',
                        (args.email.lower(), args.name, auth.hash_password(pw), 'admin', now()))
            print('Admin created.')
        con.commit()
        audit(con, 'cli', 'admin.created', args.email.lower())
    elif args.cmd == 'check-ai':
        from ctrlspace.services.assistant import check_provider
        r = check_provider(app.extensions['provider'])
        print(f"AI provider: {r['provider']} | status: {r['status']} | latency: {r['latency_ms']} ms\n{r['detail']}")
        sys.exit(0 if r['status'] == 'ok' else 1)
    elif args.cmd == 'preflight':
        r = app.test_client().get('/api/demo/preflight').get_json()
        for c in r['checks']:
            print(f"{c['status'].upper():5} {c['check']}: {c['detail']}")
        print(f"\nOverall: {r['status'].upper()} | assistant mode: {r['mode']}")
        sys.exit(1 if r['status'] == 'fail' else 0)
    elif args.cmd == 'ingest':
        try:
            res = ingest.ingest(con, ingest.NTRSClient(app.config['NTRS_BASE']), args.ntrs_id, app.config['STORAGE_DIR'])
            print(res)
            print('Report is pending: approve it and verify its passages in the Admin page.')
        except ingest.IngestError as e:
            sys.exit(f'{e.code}: {e}')


if __name__ == '__main__':
    main()

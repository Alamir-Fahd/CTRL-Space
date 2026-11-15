"""Backend tests: run with  python -m unittest discover -s tests -v"""
import io
import json
import os
import sqlite3
import sys
import tempfile
import unittest
import urllib.error

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
from ctrlspace import create_app  # noqa: E402
from ctrlspace.services import auth, ingest  # noqa: E402
from ctrlspace.services.assistant import Provider, ProviderError  # noqa: E402
from ctrlspace.services.search import INDEX, tokens  # noqa: E402

PW = 'FlameSpread2026'


class FakeProvider(Provider):
    name = 'fake'

    def __init__(self, reply=None, exc=None):
        self.reply, self.exc, self.calls = reply, exc, []

    def generate(self, system, user):
        self.calls.append(user)
        if self.exc:
            raise self.exc
        return self.reply(user) if callable(self.reply) else self.reply


def make(provider=None, ntrs=None, **cfg):
    tmp = tempfile.mkdtemp()
    app = create_app({'DATABASE': ':memory:', 'STORAGE_DIR': os.path.join(tmp, 'orig'), **cfg}, provider=provider, ntrs_client=ntrs)
    return app, app.test_client()


def signup(c, email='a@example.com', name='Ada'):
    r = c.post('/api/auth/register', json={'email': email, 'name': name, 'password': PW})
    assert r.status_code == 201, r.get_json()
    return r


def make_admin(app, c, email='admin@example.com'):
    signup(c, email, 'Admin')
    app.extensions['db'].execute("UPDATE users SET role='admin' WHERE email=?", (email,))
    app.extensions['db'].commit()


class HealthAndReports(unittest.TestCase):
    def setUp(self):
        self.app, self.c = make()

    def test_health_and_stats(self):
        h = self.c.get('/api/health').get_json()
        self.assertEqual((h['status'], h['database'], h['indexed_passages']), ('ok', 'ok', 36))
        s = self.c.get('/api/stats').get_json()
        self.assertEqual((s['reports'], s['verified_passages'], s['experiments']), (6, 36, 8))
        self.assertEqual(s['programs'], ['BASS-II', 'Saffire'])

    def test_reports_pagination_sort_filter_search(self):
        r = self.c.get('/api/reports?limit=2&offset=0&sort=title').get_json()
        self.assertEqual((len(r['items']), r['total']), (2, 6))
        self.assertLessEqual(r['items'][0]['title'].lower(), r['items'][1]['title'].lower())
        self.assertTrue(all(x['program'] == 'Saffire' for x in self.c.get('/api/reports?program=Saffire').get_json()['items']))
        hits = [h['id'] for h in self.c.get('/api/reports?q=carbon monoxide').get_json()['items']]
        self.assertEqual(set(hits), {'20240002981', '20150019858'})     # both CO sources, nothing unrelated
        self.assertEqual(self.c.get('/api/reports?q=global equivalence ratio').get_json()['items'][0]['id'], '20150019858')
        self.assertEqual(self.c.get('/api/reports?q=test matrix slide').get_json()['items'][0]['id'], '20240007488')
        for bad in ('limit=0', 'limit=101', 'limit=abc', 'offset=-1', 'sort=evil'):
            self.assertEqual(self.c.get('/api/reports?' + bad).status_code, 422, bad)

    def test_report_detail_never_leaks_raw_metadata(self):
        d = self.c.get('/api/reports/20150019858').get_json()
        self.assertEqual(len(d['passages']), 11)
        self.assertNotIn('raw_metadata', d)
        self.assertNotIn('file_sha256', d)
        self.assertEqual(self.c.get('/api/reports/123').status_code, 400)
        self.assertEqual(self.c.get('/api/reports/99999999').status_code, 404)

    def test_pending_report_hidden_from_public(self):
        con = self.app.extensions['db']
        con.execute("UPDATE reports SET status='pending' WHERE id='20150019858'")
        con.commit()
        INDEX.build(con)
        self.assertEqual(self.c.get('/api/reports/20150019858').status_code, 404)
        self.assertEqual(self.c.get('/api/stats').get_json()['reports'], 5)
        ids = {h['report_id'] for h in self.c.get('/api/search?q=carbon monoxide ppm').get_json()['items']}
        self.assertNotIn('20150019858', ids)

    def test_error_shape_and_request_id(self):
        r = self.c.get('/api/nope', headers={'X-Request-ID': 'abc123'})
        e = r.get_json()['error']
        self.assertEqual((r.status_code, e['code'], e['request_id']), (404, 'not_found', 'abc123'))
        self.assertEqual(r.headers['X-Request-ID'], 'abc123')


class Search(unittest.TestCase):
    def setUp(self):
        self.app, self.c = make()

    def test_normalisation(self):
        self.assertEqual(tokens('Flames'), tokens('flame'))
        self.assertEqual(tokens('O2 airflow'), ['oxygen', 'flow'])
        self.assertIn('extinction', tokens('self-extinguish'))

    def test_ranked_results_and_validation(self):
        r = self.c.get('/api/search?q=radiative quenching low flow').get_json()
        self.assertEqual(r['items'][0]['id'], 'B6')
        scores = [i['score'] for i in r['items']]
        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertEqual(self.c.get('/api/search?q=a').status_code, 422)
        self.assertEqual(self.c.get('/api/search?q=flame&kind=bogus').status_code, 422)
        self.assertTrue(all(i['kind'] == 'hypothesis' for i in self.c.get('/api/search?q=microgravity&kind=hypothesis').get_json()['items']))

    def test_unverified_passages_not_searchable(self):
        con = self.app.extensions['db']
        con.execute("INSERT INTO passages (id,report_id,locator,kind,text,verified,origin,created_at) VALUES "
                    "('X1','20150019858','p. 3','unreviewed','zebra unicorn passage text',0,'auto','t')")
        con.commit()
        INDEX.build(con)
        self.assertEqual(self.c.get('/api/search?q=zebra unicorn').get_json()['total'], 0)


class Assistant(unittest.TestCase):
    Q = 'How does oxygen concentration affect flame spread in microgravity?'

    def ask(self, provider, q=None):
        app, c = make(provider=provider)
        return c.post('/api/ask', json={'question': q or self.Q})

    def test_grounded_answer_and_fabricated_citation_removed(self):
        def reply(user):
            ids = [l.split(']')[0][1:] for l in user.splitlines() if l.startswith('[')]
            return json.dumps({'status': 'answered', 'summary': 'Spread rate rose with oxygen in the MIST tests.',
                               'points': [{'text': 'Rate rose with oxygen.', 'sources': [ids[0], 'Z999']},
                                          {'text': 'Invented claim.', 'sources': ['FAKE1']}], 'limits': 'Only PMMA rods.'})
        r = self.ask(FakeProvider(reply)).get_json()
        self.assertEqual(r['status'], 'answered')
        self.assertEqual(len(r['points']), 1)                     # point with only fake citations dropped
        cit = r['points'][0]['citations']
        self.assertEqual(len(cit), 1)
        self.assertTrue(cit[0]['source_url'].startswith('https://ntrs.nasa.gov/citations/'))
        self.assertIn('2 citation(s) were removed', r['warnings'][0])

    def test_gate_blocks_llm_for_unsupported_questions(self):
        p = FakeProvider('{"status":"answered"}')
        r = self.ask(p, 'What is the best pizza topping in Cairo?').get_json()
        self.assertEqual(r['status'], 'insufficient_evidence')
        self.assertEqual(p.calls, [])                             # hard gate BEFORE any LLM call

    def test_model_says_insufficient(self):
        r = self.ask(FakeProvider('{"status":"insufficient_evidence","points":[],"limits":"No pressure data."}')).get_json()
        self.assertEqual((r['status'], r['reason']), ('insufficient_evidence', 'No pressure data.'))

    def test_bad_json_and_provider_failures_are_honest(self):
        r = self.ask(FakeProvider('Sure! Here is an answer without JSON')).get_json()
        self.assertEqual((r['status'], r['error_code'], r['answer']), ('evidence_only', 'bad_output', None))
        r = self.ask(FakeProvider(exc=ProviderError('upstream_unavailable', 'AI provider could not be reached or timed out.'))).get_json()
        self.assertEqual(r['status'], 'evidence_only')
        self.assertGreaterEqual(len(r['evidence']), 2)

    def test_no_provider_returns_evidence_only(self):
        r = self.ask(None).get_json()
        self.assertEqual((r['status'], r['error_code'], r['provider']), ('evidence_only', 'not_configured', 'none'))

    def test_prompt_contains_only_verified_passages_and_rules(self):
        p = FakeProvider('{"status":"insufficient_evidence","points":[]}')
        self.ask(p)
        self.assertIn('Passages:', p.calls[0])
        self.assertNotIn('unreviewed', p.calls[0].lower().replace('(unreviewed)', 'X'))

    def test_validation(self):
        _, c = make()
        self.assertEqual(c.post('/api/ask', json={'question': 'hi'}).status_code, 422)
        self.assertEqual(c.post('/api/ask', json={'question': 'x' * 401}).status_code, 422)
        self.assertEqual(c.post('/api/ask', json={'question': self.Q, 'top_k': 99}).status_code, 422)
        self.assertEqual(c.post('/api/ask', data='question=hi', content_type='text/plain').status_code, 415)
        self.assertEqual(c.post('/api/ask', data='[1]', content_type='application/json').status_code, 400)

    def test_rate_limit(self):
        _, c = make()
        codes = [c.post('/api/ask', json={'question': self.Q}).status_code for _ in range(21)]
        self.assertEqual(codes[-1], 429)


class Experiments(unittest.TestCase):
    def setUp(self):
        self.app, self.c = make()

    def test_list_and_detail_states(self):
        items = self.c.get('/api/experiments').get_json()['items']
        self.assertEqual(len(items), 8)
        e = self.c.get('/api/experiments/bass2-smmrf').get_json()
        self.assertEqual(e['fields']['pressure']['state'], 'not_reported')
        self.assertIsNone(e['fields']['pressure']['number'])      # missing is never zero
        self.assertEqual(e['fields']['result']['source']['passage_id'], 'B12')
        self.assertEqual(self.c.get('/api/experiments/NOPE!').status_code, 400)
        self.assertEqual(self.c.get('/api/experiments/nope').status_code, 404)

    def test_compare_warnings_units_and_chartable(self):
        r = self.c.post('/api/compare', json={'experiment_ids': ['bass2-mist', 'saffire6-3', 'saffire6-4']}).get_json()
        codes = {w['code'] for w in r['warnings']}
        self.assertTrue({'different_programs', 'missing_values', 'unit_mismatch'} <= codes)
        tests = next(x for x in r['rows'] if x['field'] == 'tests')
        self.assertFalse(tests['numeric_comparable'])
        self.assertIn('size', r['chartable_fields'])
        same = self.c.post('/api/compare', json={'experiment_ids': ['saffire6-3', 'saffire6-4']}).get_json()
        flow = next(x for x in same['rows'] if x['field'] == 'flow')
        self.assertEqual((flow['numeric_comparable'], flow['unit']), (True, 'cm/s'))

    def test_flow_configuration_warning(self):
        r = self.c.post('/api/compare', json={'experiment_ids': ['bass2-rtfs', 'bass2-gel']}).get_json()
        self.assertIn('flow_configuration', {w['code'] for w in r['warnings']})

    def test_compare_validation(self):
        for ids in (['bass2-mist'], ['a', 'b', 'c', 'd', 'e'], ['bass2-mist', 'bass2-mist'], 'x', [1, 2]):
            self.assertEqual(self.c.post('/api/compare', json={'experiment_ids': ids}).status_code, 422, ids)
        r = self.c.post('/api/compare', json={'experiment_ids': ['bass2-mist', 'ghost']})
        self.assertEqual((r.status_code, r.get_json()['error']['details']['missing']), (404, ['ghost']))


class SchemaIntegrity(unittest.TestCase):
    def setUp(self):
        self.app, _ = make()
        self.con = self.app.extensions['db']

    def test_reported_value_requires_source(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.con.execute("INSERT INTO experiment_fields (experiment_id,field,state,value_text) VALUES ('bass2-mist','x','reported','5')")

    def test_number_requires_unit_and_reported_state(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.con.execute("INSERT INTO experiment_fields (experiment_id,field,state,value_text,num_value,passage_id) VALUES ('bass2-mist','y','reported','5',5,'B8')")
        with self.assertRaises(sqlite3.IntegrityError):
            self.con.execute("INSERT INTO experiment_fields (experiment_id,field,state,num_value,num_unit) VALUES ('bass2-mist','z','not_reported',0,'cm')")

    def test_invalid_states_and_ids_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.con.execute("INSERT INTO experiment_fields (experiment_id,field,state) VALUES ('bass2-mist','w','guessed')")
        with self.assertRaises(sqlite3.IntegrityError):
            self.con.execute("INSERT INTO reports (id,title,source_url,retrieved_at,created_at) VALUES ('abc','t','u','t','t')")

    def test_seed_is_idempotent(self):
        from ctrlspace.db import seed
        self.assertEqual(seed(self.con, self.app.config['CORPUS']), {'reports': 0, 'passages': 0, 'experiments': 0})


class Auth(unittest.TestCase):
    def setUp(self):
        self.app, self.c = make()

    def test_password_hashing(self):
        h = auth.hash_password(PW)
        self.assertTrue(h.startswith('pbkdf2_sha256$'))
        self.assertTrue(auth.check_password(PW, h))
        self.assertFalse(auth.check_password(PW + 'x', h))
        self.assertFalse(auth.check_password(PW, 'garbage'))

    def test_register_validation_and_duplicates(self):
        r = self.c.post('/api/auth/register', json={'email': 'bad', 'name': '', 'password': 'short'})
        self.assertEqual(set(r.get_json()['error']['details']), {'email', 'name', 'password'})
        self.assertEqual(self.c.post('/api/auth/register', json={'email': 'a@b.co', 'name': 'A', 'password': 'alllowercase1'}).status_code, 422)
        signup(self.c)
        self.assertEqual(self.c.post('/api/auth/register', json={'email': 'A@example.com', 'name': 'B', 'password': PW}).status_code, 409)

    def test_signup_category_saved_and_validated(self):
        r = self.c.post('/api/auth/register', json={'email': 'stu@example.com', 'name': 'Stu', 'password': PW, 'category': 'student'})
        self.assertEqual((r.status_code, r.get_json()['user']['category']), (201, 'student'))
        self.assertEqual(self.c.get('/api/auth/me').get_json()['user']['category'], 'student')
        bad = self.c.post('/api/auth/register', json={'email': 'x@example.com', 'name': 'X', 'password': PW, 'category': 'admin'})
        self.assertEqual((bad.status_code, bad.get_json()['error']['details']), (422, {'category': 'Choose a valid category.'}))
        no_cat = self.c.post('/api/auth/register', json={'email': 'y@example.com', 'name': 'Y', 'password': PW})
        self.assertEqual((no_cat.status_code, no_cat.get_json()['user']['category']), (201, None))  # category stays optional server-side

    def test_session_cookie_flags_and_lifecycle(self):
        r = signup(self.c)
        cookie = r.headers['Set-Cookie']
        self.assertIn('HttpOnly', cookie)
        self.assertIn('SameSite=Strict', cookie)
        self.assertEqual(self.c.get('/api/auth/me').get_json()['user']['email'], 'a@example.com')
        self.c.post('/api/auth/logout')
        self.assertIsNone(self.c.get('/api/auth/me').get_json()['user'])
        row = self.app.extensions['db'].execute('SELECT token_hash FROM sessions').fetchone()
        self.assertIsNone(row)                                   # server-side session revoked

    def test_login_wrong_password_and_rate_limit(self):
        signup(self.c)
        self.c.post('/api/auth/logout')
        self.assertEqual(self.c.post('/api/auth/login', json={'email': 'a@example.com', 'password': 'Wrong12345X'}).status_code, 401)
        self.assertEqual(self.c.post('/api/auth/login', json={'email': 'nobody@example.com', 'password': 'Wrong12345X'}).get_json()['error']['code'], 'invalid_credentials')
        codes = [self.c.post('/api/auth/login', json={'email': 'a@example.com', 'password': 'x'}).status_code for _ in range(6)]
        self.assertIn(429, codes)

    def test_tokens_stored_hashed(self):
        r = signup(self.c)
        token = r.headers['Set-Cookie'].split('cs_session=')[1].split(';')[0]
        stored = self.app.extensions['db'].execute('SELECT token_hash FROM sessions').fetchone()[0]
        self.assertNotEqual(stored, token)
        self.assertEqual(stored, auth.tok_hash(token))


class CollectionsAndNotes(unittest.TestCase):
    def setUp(self):
        self.app, self.c = make()

    def test_requires_login(self):
        self.assertEqual(self.c.get('/api/collections').status_code, 401)
        self.assertEqual(self.c.put('/api/notes/20150019858', json={'text': 'x'}).status_code, 401)

    def test_crud_export_and_isolation(self):
        signup(self.c)
        col = self.c.post('/api/collections', json={'name': 'Reading'}).get_json()
        self.assertEqual(self.c.post('/api/collections', json={'name': 'Reading'}).status_code, 409)
        self.assertEqual(self.c.post(f'/api/collections/{col["id"]}/items', json={'kind': 'report', 'id': '20150019858'}).status_code, 201)
        self.assertEqual(self.c.post(f'/api/collections/{col["id"]}/items', json={'kind': 'experiment', 'id': 'bass2-smmrf'}).status_code, 201)
        self.assertEqual(self.c.post(f'/api/collections/{col["id"]}/items', json={'kind': 'report', 'id': '11111111'}).status_code, 404)
        self.c.put('/api/notes/20150019858', json={'text': '<script>alert(1)</script> check p. 7'})
        md = self.c.get(f'/api/collections/{col["id"]}/export').get_data(as_text=True)
        self.assertIn('check p. 7', md)
        self.assertIn('Not reported', md)                        # missing values exported honestly
        self.assertIn('(NTRS 20160000593, Spacecraft Materials Microgravity Research on Flammability)', md)
        self.assertLess(md.index('NTRS: https://ntrs.nasa.gov/citations/20150019858'), md.index('## Spacecraft Materials'))  # insertion order
        # another user cannot see or touch it
        other = self.app.test_client()
        signup(other, 'b@example.com', 'Bo')
        self.assertEqual(other.get(f'/api/collections/{col["id"]}/export').status_code, 404)
        self.assertEqual(other.delete(f'/api/collections/{col["id"]}').status_code, 404)
        self.assertEqual(other.get('/api/collections').get_json()['items'], [])
        self.assertEqual(other.get('/api/reports/20150019858').get_json()['my_note'], '')
        self.assertEqual(self.c.delete(f'/api/collections/{col["id"]}').status_code, 200)

    def test_note_limits(self):
        signup(self.c)
        self.assertEqual(self.c.put('/api/notes/20150019858', json={'text': 'x' * 5001}).status_code, 422)


class FakeResp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def pdf_bytes(pages):
    from reportlab.pdfgen import canvas
    buf = io.BytesIO()
    cv = canvas.Canvas(buf)
    for text in pages:
        y = 800
        for line in text.split('\n'):
            cv.drawString(50, y, line)
            y -= 14
        cv.showPage()
    cv.save()
    return buf.getvalue()


class FakeNTRS:
    """Scripted stand-in for urlopen: maps URL suffix -> bytes | HTTPError code."""
    def __init__(self, routes):
        self.routes, self.seen = routes, []

    def __call__(self, req, timeout=None):
        url = req.full_url
        self.seen.append(url)
        for suffix, val in self.routes.items():
            if url.endswith(suffix):
                if isinstance(val, int):
                    raise urllib.error.HTTPError(url, val, 'x', {}, None)
                return FakeResp(val if isinstance(val, bytes) else json.dumps(val).encode())
        raise urllib.error.HTTPError(url, 404, 'x', {}, None)


META = {'id': 20990000001, 'title': 'Test Flame Report', 'distribution': 'PUBLIC', 'disseminated': 'DOCUMENT_AND_METADATA', 'stiType': 'TECHNICAL_MEMORANDUM'}


class Ingestion(unittest.TestCase):
    def client(self, routes):
        fake = FakeNTRS(routes)
        return ingest.NTRSClient('https://ntrs.test/api', min_interval=0, retries=1, opener=fake), fake

    def run_admin(self, routes):
        cl, fake = self.client(routes)
        app, c = make(ntrs=cl)
        make_admin(app, c)
        return app, c, fake

    def test_full_import_creates_pending_report_and_unverified_passages(self):
        pdf = pdf_bytes(['Flame spread over PMMA was measured in the flow duct during the test campaign.\nOxygen was reduced by nitrogen dilution before each burn.',
                         'Page two discusses extinction at low flow velocity and radiative losses in detail here.'])
        app, c, fake = self.run_admin({'/citations/20990000001': {**META, 'id': '20990000001'},
                                       '/downloads': [{'mimetype': 'application/pdf', 'links': {'pdf': '/api/citations/20990000001/downloads/r.pdf'}}],
                                       'r.pdf': pdf})
        r = c.post('/api/admin/ingest', json={'ntrs_id': '20990000001'})
        self.assertEqual(r.status_code, 201, r.get_json())
        d = r.get_json()
        self.assertEqual((d['pages'], d['document']), (2, 'stored'))
        con = app.extensions['db']
        self.assertEqual(con.execute("SELECT status FROM reports WHERE id='20990000001'").fetchone()[0], 'pending')
        self.assertEqual(con.execute("SELECT COUNT(*) FROM passages WHERE report_id='20990000001' AND verified=1").fetchone()[0], 0)
        self.assertEqual(con.execute("SELECT page_number FROM report_pages WHERE report_id='20990000001' ORDER BY 1").fetchall()[-1][0], 2)
        self.assertEqual(c.get('/api/reports/20990000001').status_code, 200)       # admin can preview pending
        anon = app.test_client()
        self.assertEqual(anon.get('/api/reports/20990000001').status_code, 404)    # public cannot
        # review workflow: verify one passage, approve report, then it is searchable
        pend = c.get('/api/admin/passages').get_json()['items']
        self.assertEqual(c.post(f'/api/admin/passages/{pend[0]["id"]}/review', json={'action': 'verify'}).status_code, 422)
        self.assertEqual(c.post(f'/api/admin/passages/{pend[0]["id"]}/review', json={'action': 'verify', 'kind': 'method'}).status_code, 200)
        c.post('/api/admin/reports/20990000001/status', json={'status': 'approved'})
        self.assertEqual(anon.get('/api/search?q=nitrogen dilution burn').get_json()['items'][0]['report_id'], '20990000001')
        actions = [a['action'] for a in c.get('/api/admin/audit').get_json()['items']]
        self.assertTrue({'ingest.ok', 'passage.verify', 'report.approved'} <= set(actions))
        stored = os.listdir(app.config['STORAGE_DIR'])
        self.assertEqual(len(stored), 1)
        self.assertRegex(stored[0], r'^[0-9a-f]{24}\.pdf$')                        # random storage name

    def test_rejects_non_pdf_and_metadata_only_and_bad_ids(self):
        app, c, _ = self.run_admin({'/citations/20990000001': {**META, 'id': '20990000001'},
                                    '/downloads': [{'mimetype': 'application/pdf', 'links': {'pdf': '/x/r.pdf'}}], 'r.pdf': b'<html>not a pdf</html>'})
        r = c.post('/api/admin/ingest', json={'ntrs_id': '20990000001'})
        self.assertEqual((r.status_code, r.get_json()['error']['code']), (502, 'not_pdf'))
        self.assertEqual(c.post('/api/admin/ingest', json={'ntrs_id': '../../etc'}).status_code, 400)
        app, c, _ = self.run_admin({'/citations/20990000002': {**META, 'id': '20990000002', 'disseminated': 'METADATA_ONLY'}})
        d = c.post('/api/admin/ingest', json={'ntrs_id': '20990000002'}).get_json()
        self.assertEqual(d['document'], 'not_stored')
        self.assertIn('metadata only', d['message'])

    def test_not_found_and_id_mismatch(self):
        app, c, _ = self.run_admin({'/citations/20990000003': 404, '/citations/20990000004': {**META, 'id': '11111111'}})
        self.assertEqual(c.post('/api/admin/ingest', json={'ntrs_id': '20990000003'}).status_code, 404)
        self.assertEqual(c.post('/api/admin/ingest', json={'ntrs_id': '20990000004'}).get_json()['error']['code'], 'id_mismatch')

    def test_retries_then_fails_cleanly(self):
        cl, fake = self.client({'/citations/20990000005': 503})
        with self.assertRaises(ingest.IngestError) as ctx:
            cl.citation('20990000005')
        self.assertEqual(ctx.exception.code, 'upstream_error')
        self.assertEqual(len(fake.seen), 2)                                      # 1 retry

    def test_chunking_keeps_page_locator(self):
        chunks = ingest.chunk('Sentence one is here. ' * 80)
        self.assertTrue(all(40 <= len(x) <= 720 for x in chunks))


class AdminSecurity(unittest.TestCase):
    def setUp(self):
        self.app, self.c = make()

    def test_admin_routes_require_admin(self):
        routes = [('get', '/api/admin/overview'), ('get', '/api/admin/audit'), ('get', '/api/admin/users'),
                  ('post', '/api/admin/reindex'), ('post', '/api/admin/ingest'), ('get', '/api/admin/passages')]
        for m, p in routes:
            self.assertEqual(getattr(self.c, m)(p, json={}).status_code, 401, p)
        signup(self.c)
        for m, p in routes:
            self.assertEqual(getattr(self.c, m)(p, json={}).status_code, 403, p)
        users = self.app.test_client()
        make_admin(self.app, users)
        u = users.get('/api/admin/users').get_json()['items'][0]
        self.assertNotIn('pw_hash', u)

    def test_cannot_reject_passage_used_by_experiment(self):
        make_admin(self.app, self.c)
        self.assertEqual(self.c.post('/api/admin/passages/B12/review', json={'action': 'reject'}).status_code, 409)

    def test_security_headers_and_spa_fallback(self):
        r = self.c.get('/')
        self.assertEqual(r.status_code, 200)
        for h in ('Content-Security-Policy', 'X-Content-Type-Options', 'X-Frame-Options', 'Referrer-Policy'):
            self.assertIn(h, r.headers)
        self.assertIn("script-src 'self'", r.headers['Content-Security-Policy'])
        self.assertEqual(self.c.get('/api/health').headers['Cache-Control'], 'no-store')
        self.assertEqual(self.c.get('/../backend/ctrlspace/db.py').status_code in (200, 404), True)
        self.assertNotIn(b'SCHEMA', self.c.get('/../backend/ctrlspace/db.py').data)   # no source disclosure
        self.assertNotIn(b'CREATE TABLE', self.c.get('/%2e%2e/backend/ctrlspace/db.py').data)

    def test_payload_limit(self):
        r = self.c.post('/api/ask', data=json.dumps({'question': 'x' * 70000}), content_type='application/json')
        self.assertEqual(r.status_code, 413)

    def test_production_requires_secure_cookie(self):
        with self.assertRaises(RuntimeError):
            make(ENV='production')


if __name__ == '__main__':
    unittest.main()


# ======================= v2 platform features =======================
class Platform(unittest.TestCase):
    def setUp(self):
        self.app, self.c = make()
        signup(self.c)

    def test_categories_temperature_and_new_passages(self):
        s = self.c.get('/api/stats').get_json()
        self.assertIn('Combustion products', s['categories'])
        self.assertEqual((s['lessons'], s['challenges'], s['verified_passages']), (5, 3, 36))
        ids = {r['id'] for r in self.c.get('/api/reports?category=Combustion products').get_json()['items']}
        self.assertEqual(ids, {'20150019858', '20240002981'})
        t = self.c.get('/api/experiments/bass2-mist').get_json()['fields']['temperature']
        self.assertEqual((t['state'], t['number']), ('not_reported', None))

    def test_profile_prefs_password_and_delete(self):
        p = self.c.patch('/api/me', json={'name': 'Ada L', 'prefs': {'theme': 'dark'}}).get_json()
        self.assertEqual((p['user']['name'], p['prefs']['theme']), ('Ada L', 'dark'))
        self.assertEqual(self.c.patch('/api/me', json={'prefs': {'theme': 'neon'}}).status_code, 422)
        self.assertEqual(self.c.patch('/api/me', json={'prefs': {'evil': 1}}).status_code, 422)
        other = self.app.test_client()
        other.post('/api/auth/login', json={'email': 'a@example.com', 'password': PW})
        self.assertEqual(self.c.post('/api/me/password', json={'current_password': 'Wrong12345X', 'new_password': 'NewFlame2027x'}).status_code, 422)
        self.assertEqual(self.c.post('/api/me/password', json={'current_password': PW, 'new_password': 'weak'}).status_code, 422)
        self.assertEqual(self.c.post('/api/me/password', json={'current_password': PW, 'new_password': 'NewFlame2027x'}).status_code, 200)
        self.assertIsNotNone(self.c.get('/api/auth/me').get_json()['user'])        # this session kept
        self.assertIsNone(other.get('/api/auth/me').get_json()['user'])            # other device signed out
        self.assertEqual(self.c.delete('/api/me', json={'password': 'bad'}).status_code, 422)
        self.assertEqual(self.c.delete('/api/me', json={'password': 'NewFlame2027x'}).status_code, 200)
        self.assertEqual(self.app.extensions['db'].execute('SELECT COUNT(*) FROM users').fetchone()[0], 0)

    def test_activity_recent_and_notes_list(self):
        self.c.get('/api/reports/20160000593')
        self.c.get('/api/experiments/bass2-gel')
        self.c.post('/api/ask', json={'question': 'How does oxygen affect flame spread in microgravity?'})
        acts = [a['action'] for a in self.c.get('/api/me/activity').get_json()['items']]
        self.assertEqual(acts, ['asked', 'viewed_experiment', 'viewed_report'])
        self.assertEqual([i['id'] for i in self.c.get('/api/me/recent').get_json()['items']], ['bass2-gel', '20160000593'])
        anon = self.app.test_client()
        self.assertEqual(anon.get('/api/me/activity').status_code, 401)
        self.c.put('/api/notes/20150019858', json={'text': 'check CO'})
        self.assertEqual(self.c.get('/api/notes').get_json()['items'][0]['report_id'], '20150019858')
        self.c.delete('/api/me/activity')
        self.assertEqual(self.c.get('/api/me/activity').get_json()['items'], [])

    def test_lessons_cite_only_verified_passages(self):
        for l in self.c.get('/api/lessons').get_json()['items']:
            d = self.c.get(f'/api/lessons/{l["id"]}').get_json()
            for s in d['sections']:
                self.assertTrue(s['evidence'], f'{l["id"]} section without evidence')
                self.assertTrue(all(e['source_url'].startswith('https://ntrs.nasa.gov/citations/') for e in s['evidence']))
        self.assertEqual(self.c.post('/api/lessons/why-microgravity/complete').status_code, 200)
        self.assertTrue(self.c.get('/api/lessons').get_json()['items'][0]['completed'])
        self.assertEqual(self.c.get('/api/lessons/nope').status_code, 404)

    def test_seed_rejects_lessons_with_unknown_evidence(self):
        from ctrlspace.db import seed_learning
        bad = os.path.join(tempfile.mkdtemp(), 'l.json')
        json.dump({'lessons': [{'id': 'x', 'title': 't', 'level': 'l', 'minutes': 1, 'summary': 's', 'sections': [{'heading': 'h', 'explanation': 'e', 'evidence': ['NOPE']}]}],
                   'challenges': [], 'rooms': []}, open(bad, 'w'))
        with self.assertRaises(ValueError):
            seed_learning(self.app.extensions['db'], bad)

    def test_challenges_hide_answers_grade_and_track(self):
        c = self.c.get('/api/challenges/products').get_json()
        self.assertNotIn('answer', json.dumps(c['questions']))
        self.assertEqual(self.c.post('/api/challenges/products/attempts', json={'answers': {'q1': 0}}).status_code, 422)
        self.assertEqual(self.c.post('/api/challenges/products/attempts', json={'answers': {'q1': 9, 'q2': 0, 'q3': 0, 'q4': 0}}).status_code, 422)
        r = self.c.post('/api/challenges/products/attempts', json={'answers': {'q1': 0, 'q2': 2, 'q3': 0, 'q4': 2}}).get_json()
        self.assertEqual((r['score'], r['passed']), (3, True))
        self.assertEqual(r['results'][2]['source']['id'], 'S6')
        prog = next(x for x in self.c.get('/api/challenges').get_json()['items'] if x['id'] == 'products')['progress']
        self.assertEqual((prog['best_score'], prog['attempts'], prog['passed']), (3, 1, True))
        anon = self.app.test_client()
        self.assertEqual(anon.post('/api/challenges/products/attempts', json={'answers': {}}).status_code, 401)

    def test_community_posts_replies_reports_moderation(self):
        self.assertEqual(self.c.post('/api/rooms/bass-ii/posts', json={'title': 'x', 'body': 'b'}).status_code, 422)
        self.assertEqual(self.c.post('/api/rooms/bass-ii/posts', json={'title': 'Good', 'body': 'b', 'ref_kind': 'report', 'ref_id': '11111111'}).status_code, 422)
        p = self.c.post('/api/rooms/bass-ii/posts', json={'title': 'SMMRF margin', 'body': '<b>bold?</b>', 'ref_kind': 'experiment', 'ref_id': 'bass2-smmrf'}).get_json()
        self.assertEqual(p['body'], '<b>bold?</b>')                          # stored as text; frontend escapes
        self.assertEqual(p['ref']['title'], 'Spacecraft Materials Microgravity Research on Flammability')
        self.assertEqual(self.c.post(f'/api/posts/{p["id"]}/replies', json={'body': 'Agreed'}).status_code, 201)
        self.assertEqual(self.c.post(f'/api/posts/{p["id"]}/report', json={'reason': 'spam'}).status_code, 422)   # own post
        bob = self.app.test_client()
        signup(bob, 'b@example.com', 'Bob')
        self.assertEqual(bob.post(f'/api/posts/{p["id"]}/report', json={'reason': 'bogus'}).status_code, 422)
        self.assertEqual(bob.post(f'/api/posts/{p["id"]}/report', json={'reason': 'misinformation'}).status_code, 200)
        self.assertEqual(bob.delete(f'/api/posts/{p["id"]}').status_code, 404)  # not the author
        adm = self.app.test_client()
        make_admin(self.app, adm, 'mod@example.com')
        q = adm.get('/api/admin/moderation').get_json()['items']
        self.assertEqual((q[0]['id'], q[0]['reasons']), (p['id'], 'misinformation'))
        adm.post(f'/api/admin/posts/{p["id"]}/moderate', json={'action': 'hide'})
        d = bob.get(f'/api/posts/{p["id"]}').get_json()['post']
        self.assertEqual((d['status'], d['title'], d['ref']), ('hidden', None, None))
        self.assertEqual(adm.get('/api/admin/moderation').get_json()['items'], [])
        self.assertIn('post.hide', [a['action'] for a in adm.get('/api/admin/audit').get_json()['items']])
        self.assertEqual(self.c.delete(f'/api/posts/{p["id"]}').status_code, 200)
        self.assertEqual(self.c.get('/api/rooms/bass-ii/posts').get_json()['total'], 0)

    def test_admin_user_management_and_last_admin(self):
        adm = self.app.test_client()
        make_admin(self.app, adm, 'boss@example.com')
        uid = self.app.extensions['db'].execute("SELECT id FROM users WHERE email='a@example.com'").fetchone()[0]
        me = self.app.extensions['db'].execute("SELECT id FROM users WHERE email='boss@example.com'").fetchone()[0]
        self.assertEqual(adm.post(f'/api/admin/users/{me}', json={'role': 'user'}).status_code, 409)   # not yourself
        self.assertEqual(adm.post(f'/api/admin/users/{uid}', json={'disabled': True}).status_code, 200)
        self.assertIsNone(self.c.get('/api/auth/me').get_json()['user'])                                # sessions revoked
        r = self.c.post('/api/auth/login', json={'email': 'a@example.com', 'password': PW})
        self.assertEqual((r.status_code, r.get_json()['error']['code']), (403, 'account_disabled'))
        adm.post(f'/api/admin/users/{uid}', json={'disabled': False, 'role': 'admin'})
        self.assertEqual(self.c.post('/api/auth/login', json={'email': 'a@example.com', 'password': PW}).status_code, 200)
        self.assertEqual(adm.post(f'/api/admin/users/{uid}', json={'role': 'user'}).status_code, 200)   # boss still admin
        self.assertEqual(self.c.post(f'/api/admin/users/{me}', json={'role': 'user'}).status_code, 403)

    def test_experiment_approval_requires_verified_evidence(self):
        adm = self.app.test_client()
        make_admin(self.app, adm, 'boss@example.com')
        self.assertEqual(adm.post('/api/admin/experiments/bass2-gel/status', json={'status': 'draft'}).status_code, 200)
        self.assertEqual(len(self.c.get('/api/experiments').get_json()['items']), 7)                   # drafts hidden
        self.assertEqual(self.c.get('/api/experiments/bass2-gel').status_code, 404)
        con = self.app.extensions['db']
        con.execute("UPDATE passages SET verified=0 WHERE id='B15'"); con.commit()
        r = adm.post('/api/admin/experiments/bass2-gel/status', json={'status': 'published'})
        self.assertEqual((r.status_code, r.get_json()['error']['details']['fields']), (409, ['geometry', 'material', 'size', 'tests']))
        con.execute("UPDATE passages SET verified=1 WHERE id='B15'"); con.commit()
        self.assertEqual(adm.post('/api/admin/experiments/bass2-gel/status', json={'status': 'published'}).status_code, 200)

    def test_analytics_are_aggregate_only(self):
        self.c.get('/api/search?q=oxygen flame')
        self.c.post('/api/compare', json={'experiment_ids': ['bass2-mist', 'bass2-gel']})
        adm = self.app.test_client()
        make_admin(self.app, adm, 'boss@example.com')
        a = adm.get('/api/admin/analytics?days=7').get_json()
        self.assertEqual((a['totals']['search'], a['totals']['compare'], a['totals']['signup']), (1, 1, 2))
        cols = {r[1] for r in self.app.extensions['db'].execute('PRAGMA table_info(metrics)')}
        self.assertEqual(cols, {'day', 'name', 'count'})                                                # no user id, no text
        self.assertEqual(self.c.get('/api/admin/analytics').status_code, 403)


class Migration(unittest.TestCase):
    def test_v1_database_upgrades_in_place(self):
        path = os.path.join(tempfile.mkdtemp(), 'old.db')
        con = sqlite3.connect(path)
        con.executescript("""CREATE TABLE schema_version (version INTEGER NOT NULL); INSERT INTO schema_version VALUES (1);
            CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT NOT NULL UNIQUE COLLATE NOCASE, name TEXT NOT NULL,
            pw_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'user', created_at TEXT NOT NULL);
            INSERT INTO users (email,name,pw_hash,role,created_at) VALUES ('old@example.com','Old','x','user','2026-01-01');""")
        con.commit(); con.close()
        app = create_app({'DATABASE': path})
        db = app.extensions['db']
        self.assertEqual(db.execute('SELECT version FROM schema_version').fetchone()[0], 7)
        self.assertEqual(db.execute("SELECT disabled, prefs FROM users WHERE email='old@example.com'").fetchone()[:], (0, '{}'))
        self.assertIsNotNone(db.execute("SELECT 1 FROM sqlite_master WHERE name='posts'").fetchone())

    def test_demo_account_seeded_once_real_login_works_never_in_memory_or_production(self):
        path = os.path.join(tempfile.mkdtemp(), 'demo.db')
        app = create_app({'DATABASE': path})
        db = app.extensions['db']
        row = db.execute('SELECT role, category, is_demo, pw_hash FROM users WHERE email=?', (auth.DEMO_EMAIL,)).fetchone()
        self.assertIsNotNone(row)
        self.assertEqual((row['role'], row['category'], row['is_demo']), ('user', 'student', 1))
        self.assertNotIn(auth.DEMO_PASSWORD, row['pw_hash'])  # never stored as plain text
        r = app.test_client().post('/api/auth/login', json={'email': auth.DEMO_EMAIL, 'password': auth.DEMO_PASSWORD})
        self.assertEqual((r.status_code, r.get_json()['user']['category'], r.get_json()['user']['is_demo']), (200, 'student', True))
        self.assertEqual(db.execute('SELECT COUNT(*) FROM users WHERE email=?', (auth.DEMO_EMAIL,)).fetchone()[0], 1)
        create_app({'DATABASE': path})  # re-opening must not duplicate or reset the account
        self.assertEqual(db.execute('SELECT COUNT(*) FROM users WHERE email=?', (auth.DEMO_EMAIL,)).fetchone()[0], 1)
        # never in the in-memory test harness used by every other test in this file
        self.assertIsNone(make()[0].extensions['db'].execute('SELECT 1 FROM users WHERE email=?', (auth.DEMO_EMAIL,)).fetchone())
        # never in production without an explicit opt-in
        prod_path = os.path.join(tempfile.mkdtemp(), 'prod.db')
        prod_app = create_app({'DATABASE': prod_path, 'ENV': 'production', 'COOKIE_SECURE': True})
        self.assertIsNone(prod_app.extensions['db'].execute('SELECT 1 FROM users WHERE email=?', (auth.DEMO_EMAIL,)).fetchone())


# ======================= v3 spec alignment =======================
class V3(unittest.TestCase):
    def setUp(self):
        self.app, self.c = make()
        signup(self.c)

    def test_discovery_filters(self):
        g = lambda q: [r['id'] for r in self.c.get('/api/reports?' + q).get_json()['items']]
        self.assertEqual(g('evidence=metadata_only'), ['20210011385', '20170008805'])
        self.assertEqual(set(g('material=SIBAL')), {'20160000593', '20240007488'})
        self.assertEqual(g('year_to=2016&sort=oldest'), ['20160000593', '20150019858'])
        self.assertEqual(self.c.get('/api/reports?evidence=maybe').status_code, 422)
        self.assertEqual(self.c.get('/api/reports?material=_').get_json()['total'], 0)           # LIKE wildcard escaped (no material contains '_')
        self.assertEqual(self.c.get('/api/reports?material=75%25').get_json()['total'], 1)      # literal % matches SIBAL 75% cotton

    def test_experiment_fields_v3(self):
        e = self.c.get('/api/experiments/bass2-mist').get_json()
        keys = [f['key'] for f in e['field_order']]
        self.assertTrue({'oxygenBasis', 'apparatus', 'temperature'} <= set(keys))
        self.assertEqual({f['key'] for f in e['field_order'] if f['group'] == 'measurement'}, {'tests', 'result'})
        self.assertEqual(e['fields']['oxygenBasis']['state'], 'not_reported')
        self.assertTrue(e['fields']['apparatus']['verified'])
        con = self.app.extensions['db']
        con.execute("UPDATE passages SET verified=0 WHERE id='B8'"); con.commit()
        self.assertEqual(self.c.get('/api/experiments/bass2-mist').get_json()['fields']['material']['state'], 'needs_verification')

    def test_saved_items_and_experiment_notes(self):
        self.assertEqual(self.c.post('/api/saved', json={'kind': 'report', 'id': '11111111'}).status_code, 422)
        self.c.post('/api/saved', json={'kind': 'report', 'id': '20160000593'})
        self.c.post('/api/saved', json={'kind': 'experiment', 'id': 'saffire6-3'})
        items = self.c.get('/api/saved').get_json()['items']
        self.assertEqual({i['kind'] for i in items}, {'report', 'experiment'})
        self.assertTrue(all(i['saved_at'] for i in items))
        self.c.delete('/api/saved/report/20160000593')
        self.assertEqual(len(self.c.get('/api/saved').get_json()['items']), 1)
        self.c.put('/api/experiment-notes/saffire6-3', json={'text': 'flow cut at 1120 s'})
        self.c.put('/api/notes/20150019858', json={'text': 'CO data'})
        kinds = [n['kind'] for n in self.c.get('/api/research-notes').get_json()['items']]
        self.assertEqual(sorted(kinds), ['experiment', 'report'])

    def test_comparison_export(self):
        r = self.c.post('/api/compare/export', json={'experiment_ids': ['saffire6-3', 'saffire6-4']})
        md = r.get_data(as_text=True)
        self.assertIn('## Conditions', md); self.assertIn('## Measurements and results', md)
        self.assertIn('20 cm/s (NTRS 20240007488, slide 11)', md)
        self.assertIn('Not reported', md)

    def test_sessions_privacy_and_export(self):
        other = self.app.test_client()
        other.post('/api/auth/login', json={'email': 'a@example.com', 'password': PW})
        ss = self.c.get('/api/me/sessions').get_json()['items']
        self.assertEqual((len(ss), sum(s['current'] for s in ss)), (2, 1))
        foreign = next(s['id'] for s in ss if not s['current'])
        self.assertEqual(self.c.delete(f'/api/me/sessions/{foreign}').status_code, 200)
        self.assertIsNone(other.get('/api/auth/me').get_json()['user'])
        self.c.get('/api/reports/20160000593')
        self.c.patch('/api/me', json={'prefs': {'history': False}})
        self.assertEqual(self.c.get('/api/me/activity').get_json()['items'], [])
        self.c.get('/api/reports/20150019858')
        self.assertEqual(self.c.get('/api/me/activity').get_json()['items'], [])            # tracking off
        data = json.loads(self.c.get('/api/me/export').get_data(as_text=True))
        self.assertEqual(data['user']['email'], 'a@example.com'); self.assertNotIn('pw_hash', json.dumps(data))

    def test_lessons_challenges_meta(self):
        l = self.c.get('/api/lessons/flow-and-extinction').get_json()
        self.assertTrue(l['objectives'] and l['topic'] and l['related_reports'])
        self.assertEqual((l['prev']['id'], l['next']['id']), ('why-microgravity', 'oxygen-and-flammability'))
        c = self.c.get('/api/challenges/products').get_json()
        self.assertTrue(c['objective'] and c['background'] and c['instructions'] and c['difficulty'])
        self.assertEqual({r['id'] for r in c['related_reports']}, {'20150019858', '20240002981'})
        self.assertEqual(next(x for x in self.c.get('/api/challenges').get_json()['items'] if x['id'] == 'products')['status'], 'not_started')

    def test_community_recent_and_edit(self):
        p = self.c.post('/api/rooms/saffire/posts', json={'title': 'VI-3 flow change', 'body': 'v1', 'ref_kind': 'experiment', 'ref_id': 'saffire6-3'}).get_json()
        e = self.c.patch(f'/api/posts/{p["id"]}', json={'body': 'v2'}).get_json()
        self.assertEqual((e['body'], bool(e['edited_at'])), ('v2', True))
        bob = self.app.test_client(); signup(bob, 'b@example.com', 'Bob')
        self.assertEqual(bob.patch(f'/api/posts/{p["id"]}', json={'body': 'hack'}).status_code, 404)
        r = self.c.get('/api/community/recent').get_json()
        self.assertEqual((r['posts'][0]['room_name'], r['shared'][0]['ref']['id']), ('Saffire', 'saffire6-3'))

    def test_admin_health_flag_reject(self):
        adm = self.app.test_client(); make_admin(self.app, adm, 'boss@example.com')
        h = adm.get('/api/admin/health').get_json()
        self.assertEqual((h['database'], h['schema_version'], h['ntrs']), ('ok', 7, 'not_checked'))
        self.assertEqual(adm.post('/api/admin/passages/B12/flag', json={'reason': 'x'}).status_code, 422)
        adm.post('/api/admin/passages/B12/flag', json={'reason': 'Value differs from PDF'})
        self.assertIn('Value differs', adm.get('/api/admin/passages').get_json()['items'][0]['flag_reason'])
        self.assertEqual(adm.get('/api/admin/experiments').get_json()['items'][[x['id'] for x in adm.get('/api/admin/experiments').get_json()['items']].index('bass2-smmrf')]['blocking_fields'], ['gravity', 'result', 'size'])
        self.assertEqual(adm.post('/api/admin/experiments/bass2-smmrf/reject', json={'reason': 'Recheck B12'}).status_code, 200)
        self.assertEqual(self.c.get('/api/experiments/bass2-smmrf').status_code, 404)
        self.assertIn('experiment.rejected', [a['action'] for a in adm.get('/api/admin/audit').get_json()['items']])
        self.assertEqual(adm.get('/api/admin/failed-imports').get_json()['items'], [])

    def test_upgrade_never_restores_rejected_passages(self):
        path = os.path.join(tempfile.mkdtemp(), 'u.db')
        app = create_app({'DATABASE': path})
        con = app.extensions['db']
        con.execute("DELETE FROM passages WHERE id='B19'")      # simulate an older DB where it was removed
        con.execute("DELETE FROM experiment_fields WHERE field='apparatus'"); con.commit()
        app2 = create_app({'DATABASE': path})
        con2 = app2.extensions['db']
        self.assertIsNone(con2.execute("SELECT 1 FROM passages WHERE id='B19'").fetchone())
        self.assertEqual(con2.execute("SELECT COUNT(*) FROM experiment_fields WHERE field='apparatus'").fetchone()[0], 8)


# ======================= competition release: scientific intelligence =======================
from ctrlspace.services import intelligence as intel  # noqa: E402


class Intelligence(unittest.TestCase):
    def setUp(self):
        self.app, self.c = make()

    def test_question_analysis(self):
        a = intel.analyze_question
        self.assertEqual(a('Compare BASS-II and Saffire airflow')['type'], 'comparison')
        self.assertEqual(a('What will happen at 10% oxygen?')['type'], 'prediction')
        self.assertEqual(a('Why do flames quench at low flow?')['type'], 'interpretation')
        self.assertEqual(a('What oxygen range was tested?')['type'], 'fact')
        x = a('How does oxygen affect PMMA flame spread in microgravity on BASS-II?')
        self.assertEqual(x['variables'], ['gravity', 'material', 'oxygen', 'spread']); self.assertEqual(x['programs'], ['BASS-II'])

    def test_coverage_rules(self):
        an = intel.analyze_question('How does oxygen affect flame spread?')
        f = lambda kind, text, rid='1': {'kind': kind, 'text': text, 'report_id': rid}
        self.assertEqual(intel.evaluate_evidence(an, [])['level'], 'insufficient')
        good = intel.evaluate_evidence(an, [f('finding', 'spread rate rose with oxygen'), f('finding', 'oxygen raised spread', '2')])
        self.assertEqual(good['level'], 'well_supported')
        hyp = intel.evaluate_evidence(an, [f('hypothesis', 'oxygen may change spread'), f('condition', 'oxygen 16 to 21%')])
        self.assertEqual(hyp['level'], 'partially_supported'); self.assertTrue(any('hypothesis' in n for n in hyp['notes']))
        miss = intel.evaluate_evidence(intel.analyze_question('How does pressure affect flame spread?'), [f('finding', 'spread rate rose'), f('finding', 'spread fell', '2')])
        self.assertIn('pressure', miss['variables_missing'])
        pred = intel.evaluate_evidence(intel.analyze_question('What will spread rate be at 10% oxygen?'), [f('finding', 'oxygen spread'), f('finding', 'oxygen spread', '2')])
        self.assertEqual(pred['level'], 'partially_supported')
        self.assertIn('not a probability', good['definition'])

    def test_numeric_grounding(self):
        self.assertEqual(intel.numeric_grounding('Steady spread at 13.6% oxygen', ['steady spreading at 13.6% oxygen']), [])
        self.assertEqual(intel.numeric_grounding('Spread at 12.1% oxygen and 40 cm/s', ['13.6% oxygen', 'crosses 40 cm/s']), ['12.1'])

    def test_normalization_keeps_original(self):
        n = intel.normalize({'value': 20.0, 'unit': 'cm/s'})
        self.assertEqual((n['value'], n['unit'], n['original']['unit']), (0.2, 'm/s', 'cm/s'))
        self.assertIsNone(intel.normalize({'value': 54, 'unit': 'flame spread rates'}))
        f = self.c.get('/api/experiments/saffire6-4').get_json()['fields']
        self.assertEqual((f['flow']['value_type'], f['flow']['normalized']['value'], f['flow']['number']['unit']), ('reported', 0.2, 'cm/s'))
        self.assertEqual(f['oxygen']['value_type'], 'missing')

    def test_structured_answer_with_numeric_check(self):
        def reply(user):
            ids = [l.split(']')[0][1:] for l in user.splitlines() if l.startswith('[')]
            return json.dumps({'status': 'answered', 'direct_answer': {'text': 'Spread rate rose with oxygen.', 'sources': [ids[0]]},
                               'explanation': [{'text': 'Higher oxygen raised spread at 99.9% certainty.', 'sources': [ids[0]]}],
                               'evidence': [{'text': 'A finding.', 'sources': ['FAKE']}], 'conditions': [{'text': 'PMMA rods.', 'sources': [ids[1]]}],
                               'limitations': 'Only PMMA.'})
        _, c = make(provider=FakeProvider(reply))
        r = c.post('/api/ask', json={'question': 'How does oxygen concentration affect flame spread in microgravity?'}).get_json()
        self.assertEqual((r['status'], r['mode']), ('answered', 'ai'))
        self.assertEqual(r['sections']['evidence'], [])                                 # only-fake-citation item dropped
        self.assertEqual(r['sections']['explanation'][0]['ungrounded_numbers'], ['99.9'])
        self.assertTrue(any('99.9' in w for w in r['warnings']))
        self.assertEqual(r['coverage']['level'], 'well_supported'); self.assertEqual(r['analysis']['type'], 'interpretation')

    def test_answer_without_cited_direct_answer_is_refused(self):
        _, c = make(provider=FakeProvider('{"status":"answered","direct_answer":{"text":"Yes","sources":["NOPE"]},"explanation":[]}'))
        r = c.post('/api/ask', json={'question': 'How does oxygen concentration affect flame spread in microgravity?'}).get_json()
        self.assertEqual(r['status'], 'insufficient_evidence')

    def test_retrieval_only_brief(self):
        r = self.c.post('/api/ask', json={'question': 'What happens to flames at very low airflow?'}).get_json()
        self.assertEqual((r['status'], r['mode']), ('evidence_only', 'retrieval_only'))
        b = r['brief']
        self.assertTrue(b['findings'] and b['sources'])
        self.assertTrue(all(e['kind'] == 'finding' for e in b['findings']))

    def test_comparison_levels(self):
        r = self.c.post('/api/compare', json={'experiment_ids': ['bass2-smmrf', 'saffire6-3']}).get_json()
        titles = {w['title'] for w in r['levels']['level2']}
        self.assertTrue({'Different materials', 'Different experimental platforms'} <= titles)
        types = {f['statement_type'] for f in r['levels']['level3']['findings']}
        self.assertEqual(types, {'Reported experimental finding', 'Reported test condition'})
        self.assertEqual(r['levels']['level3']['relationships'], [])             # a condition is never treated as a finding
        self.assertIn('does not infer', r['levels']['level3']['rule'])

    def test_gaps_are_corpus_scoped(self):
        g = self.c.get('/api/gaps').get_json()
        cats = {x['category'] for x in g['gaps']}
        self.assertTrue({'data_not_reported', 'data_not_extracted', 'topic_not_found', 'no_data_in_db'} <= cats)
        self.assertNotIn('verified_absence', cats)
        self.assertIn('never proves', g['scope'])
        nf = next(x for x in g['gaps'] if x['category'] == 'topic_not_found')
        self.assertIn('NOT evidence that NASA never studied it', nf['question_note'])

    def test_brief_and_preflight(self):
        b = self.c.post('/api/brief', json={'question': 'What is the oxygen margin of safety for PMMA rods?', 'experiment_ids': ['bass2-smmrf', 'saffire6-3']})
        md = b.get_data(as_text=True)
        for part in ('Mode: retrieval-only', 'Evidence coverage', 'Reported findings (verbatim)', 'Why these results are hard to compare', 'ntrs.nasa.gov/citations/20160000593'):
            self.assertIn(part, md)
        self.assertEqual(self.c.post('/api/brief', json={}).status_code, 422)
        p = self.c.get('/api/demo/preflight').get_json()
        self.assertEqual((p['status'], p['mode']), ('warn', 'retrieval_only'))
        self.assertTrue(all(c['status'] == 'ok' for c in p['checks'] if c['check'] != 'AI provider configured'))

    def test_ai_check(self):
        adm = self.app.test_client(); make_admin(self.app, adm)
        self.assertEqual(adm.post('/api/admin/ai/check').get_json()['status'], 'not_configured')
        _, c2 = make(provider=FakeProvider('{"ok": true}'))
        app2 = c2.application; adm2 = app2.test_client(); make_admin(app2, adm2)
        self.assertEqual(adm2.post('/api/admin/ai/check').get_json()['status'], 'ok')
        self.assertEqual(self.c.post('/api/admin/ai/check').status_code, 401)


# ======================= mobile app backend (v5) =======================
NASA_SAMPLE = {'collection': {'metadata': {'total_hits': 2}, 'items': [
    {'data': [{'nasa_id': 'GRC-2016-C-01234', 'title': 'Flame in microgravity', 'description': '<p>A flame burning on the ISS.</p>', 'date_created': '2016-03-01T00:00:00Z', 'center': 'GRC'}],
     'links': [{'href': 'https://images-assets.nasa.gov/image/GRC-2016-C-01234/GRC-2016-C-01234~thumb.jpg', 'render': 'image'}]},
    {'data': [{'nasa_id': 'BAD', 'title': 'Off-site thumb'}], 'links': [{'href': 'https://evil.example/x.jpg', 'render': 'image'}]}]}}


class MediaOpener:
    def __init__(self, payload=None, fail=False):
        self.payload, self.fail, self.urls = payload, fail, []

    def __call__(self, req, timeout=None):
        self.urls.append(req.full_url)
        if self.fail:
            raise urllib.error.URLError('offline')
        return FakeResp(json.dumps(self.payload).encode())


PSI_SAMPLE = {'hits': {'total': 1, 'hits': [{'_source': {
    'Accession': 'PSI-117', 'Title': 'Cool Flame Dynamics', 'Person': {'First Name': 'Tanvir', 'Middle Initials': 'Mike', 'Last Name': 'Farouk Hicks'},
    'Keywords': 'Cool Flames     Droplet combustion     FLEX', 'Research Area': 'Combustion Science', 'SubResearch Area': 'Droplet',
    'Project Type': 'Ground Investigation', 'Investigation Start Date': '02-15-2017', 'Investigation End Date': '02-14-2022',
    'Sponsoring Agency': 'NASA', 'Monitoring Center': 'Glenn Research Center (GRC)', 'Objectives': 'Study cool-flame dynamics.', 'Approach': 'CFD modeling.'}}]}}


class PsiOpener:
    def __init__(self, payload=None, fail=False):
        self.payload, self.fail, self.urls = payload, fail, []

    def __call__(self, req, timeout=None):
        self.urls.append(req.full_url)
        if self.fail:
            raise urllib.error.URLError('offline')
        return FakeResp(json.dumps(self.payload).encode())


class Mobile(unittest.TestCase):
    def setUp(self):
        self.app, self.c = make()
        signup(self.c)

    def test_conversation_history_context_and_export(self):
        r = self.c.post('/api/assistant/ask', json={'question': 'What happens to flames at very low airflow?'}).get_json()
        cid = r['conversation_id']
        f = self.c.post('/api/assistant/ask', json={'question': 'and at high flow?', 'conversation_id': cid}).get_json()
        self.assertTrue(f['context_used']['follow_up'])
        self.assertIn('very low airflow', f['retrieval_query'])
        conv = self.c.get(f'/api/conversations/{cid}').get_json()
        self.assertEqual([m['role'] for m in conv['messages']], ['user', 'assistant', 'user', 'assistant'])
        md = self.c.get(f'/api/conversations/{cid}/export').get_data(as_text=True)
        self.assertIn('## Q: and at high flow?', md); self.assertIn('NTRS', md)
        other = self.app.test_client(); signup(other, 'b@example.com', 'Bo')
        self.assertEqual(other.get(f'/api/conversations/{cid}').status_code, 404)
        self.assertEqual(other.post('/api/assistant/ask', json={'question': 'flames?', 'conversation_id': cid}).status_code, 404)
        self.assertEqual(self.c.delete(f'/api/conversations/{cid}').status_code, 200)

    def test_report_scoped_question(self):
        r = self.c.post('/api/assistant/ask', json={'question': 'Summarize the carbon monoxide findings', 'report_id': '20150019858'}).get_json()
        self.assertEqual(r['report_scope'], '20150019858')
        self.assertTrue(r['evidence'] and all(e['report_id'] == '20150019858' for e in r['evidence']))
        self.assertEqual(self.c.post('/api/assistant/ask', json={'question': 'x y z', 'report_id': '11111111'}).status_code, 404)

    def test_anonymous_ask_not_persisted(self):
        anon = self.app.test_client()
        r = anon.post('/api/assistant/ask', json={'question': 'What happens to flames at very low airflow?'}).get_json()
        self.assertNotIn('conversation_id', r)

    def test_notifications_from_real_events(self):
        n = self.c.get('/api/notifications').get_json()
        self.assertEqual((n['unread'], n['items'][0]['title']), (1, 'Welcome to CTRL+SPACE'))
        p = self.c.post('/api/rooms/bass-ii/posts', json={'title': 'Quenching question', 'body': 'b'}).get_json()
        bob = self.app.test_client(); signup(bob, 'b@example.com', 'Bob')
        bob.post(f'/api/posts/{p["id"]}/replies', json={'body': 'Reply'})
        n = self.c.get('/api/notifications').get_json()
        self.assertEqual(n['items'][0]['kind'], 'replies'); self.assertIn('Bob replied', n['items'][0]['title'])
        self.c.post('/api/notifications/read', json={'ids': 'all'})
        self.assertEqual(self.c.get('/api/notifications').get_json()['unread'], 0)
        self.c.patch('/api/me', json={'prefs': {'notify': {'replies': False}}})
        bob.post(f'/api/posts/{p["id"]}/replies', json={'body': 'Again'})
        self.assertEqual(self.c.get('/api/notifications').get_json()['unread'], 0)                      # preference respected
        self.assertEqual(self.c.post('/api/notifications/read', json={'ids': 'x'}).status_code, 422)

    def test_moderation_notifies_author(self):
        p = self.c.post('/api/rooms/general/posts', json={'title': 'Hello there', 'body': 'b'}).get_json()
        adm = self.app.test_client(); make_admin(self.app, adm, 'boss@example.com')
        adm.post(f'/api/admin/posts/{p["id"]}/moderate', json={'action': 'hide'})
        self.assertEqual(self.c.get('/api/notifications').get_json()['items'][0]['kind'], 'moderation')

    def test_password_reset_flow(self):
        adm = self.app.test_client(); make_admin(self.app, adm, 'boss@example.com')
        r = self.app.test_client().post('/api/auth/forgot', json={'email': 'a@example.com'}).get_json()
        self.assertIn('no email service', r['message'])
        same = self.app.test_client().post('/api/auth/forgot', json={'email': 'nobody@example.com'}).get_json()
        self.assertEqual(r['message'], same['message'])                                               # no account enumeration
        self.assertIn('Password reset requested', adm.get('/api/notifications').get_json()['items'][0]['title'])
        uid = self.app.extensions['db'].execute("SELECT id FROM users WHERE email='a@example.com'").fetchone()[0]
        self.assertEqual(self.c.post(f'/api/admin/users/{uid}/reset-link').status_code, 403)
        link = adm.post(f'/api/admin/users/{uid}/reset-link').get_json()
        token = link['url'].split('token=')[1]
        anon = self.app.test_client()
        self.assertEqual(anon.post('/api/auth/reset', json={'token': token, 'password': 'weak'}).status_code, 422)
        self.assertEqual(anon.post('/api/auth/reset', json={'token': token, 'password': 'Reset2027Pass'}).status_code, 200)
        self.assertEqual(anon.post('/api/auth/reset', json={'token': token, 'password': 'Reset2027Pass'}).status_code, 400)    # single use
        self.assertIsNone(self.c.get('/api/auth/me').get_json()['user'])                                # old sessions revoked
        self.assertEqual(anon.post('/api/auth/login', json={'email': 'a@example.com', 'password': 'Reset2027Pass'}).status_code, 200)
        stored = self.app.extensions['db'].execute('SELECT token_hash FROM password_resets').fetchone()[0]
        self.assertNotEqual(stored, token)                                                              # token stored hashed

    def test_nasa_media_search_cache_and_offline(self):
        op = MediaOpener(NASA_SAMPLE)
        app, c = make(MEDIA_OPENER=op)
        r = c.get('/api/media/search?q=flame microgravity').get_json()
        self.assertTrue(op.urls[0].startswith('https://images-api.nasa.gov/search?') and 'media_type=image' in op.urls[0])
        self.assertEqual(len(r['items']), 1)                                                            # off-site thumbnail rejected
        it = r['items'][0]
        self.assertEqual((it['nasa_id'], it['description'], it['details_url']), ('GRC-2016-C-01234', 'A flame burning on the ISS.', 'https://images.nasa.gov/details/GRC-2016-C-01234'))
        self.assertIn('images-api.nasa.gov', r['source']); self.assertTrue(r['retrieved_at'])
        self.assertTrue(c.get('/api/media/search?q=flame microgravity').get_json()['cached'])           # served from cache
        app2, c2 = make(MEDIA_OPENER=MediaOpener(fail=True))
        e = c2.get('/api/media/search?q=saturn')
        self.assertEqual((e.status_code, e.get_json()['error']['code']), (503, 'requires_internet'))
        self.assertEqual(c2.get('/api/media/search?q=x').status_code, 422)
        self.assertIn('https://images-assets.nasa.gov', c.get('/').headers['Content-Security-Policy'])

    def test_impact_dashboard_counts_real_usage(self):
        before = self.c.get('/api/impact').get_json()
        self.assertEqual((before['research']['verified_passages'], before['research']['experiments']), (36, 8))
        self.c.post('/api/assistant/ask', json={'question': 'What happens to flames at very low airflow?'})
        after = self.c.get('/api/impact').get_json()
        self.assertEqual(after['research']['questions_processed'], before['research']['questions_processed'] + 1)
        self.assertGreaterEqual(after['research']['evidence_grounded_answers'] + after['research']['insufficient_evidence_answers'], 1)
        self.assertIn('No efficiency comparison', after['disclaimer'])
        if after['validation']:
            self.assertIn('recall_at_6', after['validation'])

    def test_psi_search_cache_and_offline(self):
        op = PsiOpener(PSI_SAMPLE)
        app, c = make(PSI_OPENER=op)
        r = c.get('/api/psi/search?q=combustion').get_json()
        self.assertTrue(op.urls[0].startswith('https://psi.nasa.gov/geode-py/ws/repo/search?') and 'term=combustion' in op.urls[0])
        self.assertEqual(len(r['items']), 1)
        it = r['items'][0]
        self.assertEqual((it['accession'], it['pi'], it['research_area']), ('PSI-117', 'Tanvir Mike Farouk Hicks', 'Combustion Science'))
        self.assertEqual(it['keywords'], ['Cool Flames', 'Droplet combustion', 'FLEX'])
        self.assertEqual(it['landing_url'], 'https://psi.nasa.gov/physci/repo/data/investigations/PSI-117')
        self.assertTrue(r['retrieved_at'])
        self.assertTrue(c.get('/api/psi/search?q=combustion').get_json()['cached'])
        app2, c2 = make(PSI_OPENER=PsiOpener(fail=True))
        e = c2.get('/api/psi/search?q=saturn')
        self.assertEqual((e.status_code, e.get_json()['error']['code']), (503, 'requires_internet'))
        self.assertEqual(c2.get('/api/psi/search?q=x').status_code, 422)

    def test_public_profile(self):
        self.c.post('/api/rooms/saffire/posts', json={'title': 'VI-3 flow', 'body': 'b', 'ref_kind': 'report', 'ref_id': '20240007488'})
        uid = self.app.extensions['db'].execute("SELECT id FROM users WHERE email='a@example.com'").fetchone()[0]
        p = self.app.test_client().get(f'/api/users/{uid}').get_json()
        self.assertEqual((p['name'], p['contributions']['discussions'], p['contributions']['shared_research']), ('Ada', 1, 1))
        self.assertNotIn('email', p)
        self.assertEqual(self.app.test_client().get('/api/users/9999').status_code, 404)

    def test_ai_comparison(self):
        r = self.c.post('/api/compare/ai', json={'experiment_ids': ['bass2-smmrf', 'saffire6-3']}).get_json()
        self.assertEqual(r['status'], 'retrieval_only'); self.assertTrue(r['evidence'] and r['context_warnings'])
        def reply(user):
            ids = [l.split(']')[0][1:] for l in user.splitlines() if l.startswith('[')]
            return json.dumps({'status': 'answered', 'direct_answer': {'text': 'They differ in scale and material.', 'sources': [ids[0], 'FAKE']},
                               'explanation': [], 'evidence': [{'text': 'x', 'sources': ['FAKE']}], 'conditions': [], 'limitations': 'Different hardware.'})
        _, c = make(provider=FakeProvider(reply))
        a = c.post('/api/compare/ai', json={'experiment_ids': ['bass2-smmrf', 'saffire6-3']}).get_json()
        self.assertEqual(a['status'], 'answered'); self.assertEqual(a['sections']['evidence'], [])
        self.assertEqual(len(a['sections']['direct_answer'][0]['citations']), 1)


class MobileV51(unittest.TestCase):
    def setUp(self):
        self.app, self.c = make()
        signup(self.c)

    def test_answer_feedback_owner_only(self):
        r = self.c.post('/api/assistant/ask', json={'question': 'What happens to flames at very low airflow?'}).get_json()
        mid = r['message_id']
        self.assertEqual(self.c.post('/api/feedback', json={'message_id': mid, 'rating': 'up'}).status_code, 200)
        self.assertEqual(self.c.post('/api/feedback', json={'message_id': mid, 'rating': 'meh'}).status_code, 422)
        other = self.app.test_client(); signup(other, 'b@example.com', 'Bo')
        self.assertEqual(other.post('/api/feedback', json={'message_id': mid, 'rating': 'down'}).status_code, 404)
        conv = self.c.get(f"/api/conversations/{r['conversation_id']}").get_json()
        self.assertEqual(conv['messages'][1]['content']['message_id'], mid)

    def test_collection_rename_description(self):
        col = self.c.post('/api/collections', json={'name': 'A', 'description': 'first'}).get_json()
        self.assertEqual(col['description'], 'first')
        u = self.c.patch(f"/api/collections/{col['id']}", json={'name': 'B', 'description': 'second'}).get_json()
        self.assertEqual((u['name'], u['description']), ('B', 'second'))
        self.assertEqual(self.c.patch(f"/api/collections/{col['id']}", json={'name': ''}).status_code, 422)
        other = self.app.test_client(); signup(other, 'b@example.com', 'Bo')
        self.assertEqual(other.patch(f"/api/collections/{col['id']}", json={'name': 'X'}).status_code, 404)
        self.assertEqual(self.c.get(f"/api/collections/{col['id']}").get_json()['name'], 'B')

    def test_bio_interests_and_onboarded_pref(self):
        p = self.c.patch('/api/me', json={'bio': 'Student', 'interests': ['flame spread', 'PMMA'], 'prefs': {'onboarded': True}}).get_json()
        self.assertEqual((p['user']['bio'], p['user']['interests'], p['prefs']['onboarded']), ('Student', ['flame spread', 'PMMA'], True))
        self.assertEqual(self.c.patch('/api/me', json={'interests': ['x'] * 9}).status_code, 422)

    def test_category_update_and_rejects_invalid(self):
        self.assertEqual(self.c.patch('/api/me', json={'category': 'researcher'}).get_json()['user']['category'], 'researcher')
        self.assertEqual(self.c.get('/api/me').get_json()['user']['category'], 'researcher')
        self.assertEqual(self.c.patch('/api/me', json={'category': 'not-a-real-category'}).status_code, 422)
        self.assertEqual(self.c.patch('/api/me', json={'bio': 'x' * 501}).status_code, 422)

    def test_mobile_routes_served(self):
        for path in ('/app', '/app/research', '/app/report/20150019858', '/app/assistant/3'):
            r = self.c.get(path)
            self.assertEqual(r.status_code, 200, path); self.assertIn(b'/app/js/main.js', r.data)
        self.assertIn(b'"start_url": "/app?source=pwa"', self.c.get('/manifest.webmanifest').data)


class MobileV53(unittest.TestCase):
    def setUp(self):
        self.app, self.c = make(); signup(self.c)

    def test_save_answer_owner_only(self):
        r = self.c.post('/api/assistant/ask', json={'question': 'What happens to flames at very low airflow?'}).get_json()
        mid = r['message_id']
        self.assertEqual(self.c.post(f'/api/answers/{mid}/save').status_code, 200)
        s = self.c.get('/api/answers/saved').get_json()['items']
        self.assertEqual((s[0]['message_id'], s[0]['question'], s[0]['mode']), (mid, 'What happens to flames at very low airflow?', 'retrieval_only'))
        other = self.app.test_client(); signup(other, 'b@example.com', 'Bo')
        self.assertEqual(other.post(f'/api/answers/{mid}/save').status_code, 404)
        self.c.delete(f'/api/answers/{mid}/save'); self.assertEqual(self.c.get('/api/answers/saved').get_json()['items'], [])

    def test_client_error_monitoring(self):
        anon = self.app.test_client()
        self.assertEqual(anon.post('/api/client-errors', json={'message': 'TypeError: x is null', 'source': 'main.js:10', 'route': '/app'}).status_code, 201)
        self.assertEqual(anon.post('/api/client-errors', json={}).status_code, 422)
        self.assertEqual(self.c.get('/api/admin/client-errors').status_code, 403)
        adm = self.app.test_client(); make_admin(self.app, adm, 'boss@example.com')
        self.assertEqual(adm.get('/api/admin/client-errors').get_json()['items'][0]['message'], 'TypeError: x is null')

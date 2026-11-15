"""NASA NTRS ingestion (Phase 04), ported from the Phase 04 package to the canonical schema.

Documented NTRS limits (https://sti.nasa.gov/docs/20221122_OpenAPI_Documentation.pdf): 500 requests / 15 min,
no auth. Only public records disseminated as DOCUMENT_AND_METADATA may keep documents.
Imported reports start as 'pending' and their auto-chunked passages as unverified: they are searchable by admins
but cannot back an AI answer or an experiment value until an admin verifies them."""
import hashlib
import io
import json
import os
import re
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request

from ..db import now

NTRS_ID = re.compile(r'^\d{8,12}$')
MAX_PDF = 60 * 1024 * 1024


class IngestError(Exception):
    def __init__(self, code, message, status=422):
        super().__init__(message)
        self.code, self.status = code, status


class NTRSClient:
    def __init__(self, base='https://ntrs.nasa.gov/api', min_interval=1.8, timeout=30, retries=3, opener=None):
        self.base, self.min_interval, self.timeout, self.retries = base.rstrip('/'), min_interval, timeout, retries
        self.opener = opener or urllib.request.urlopen
        self._last = 0.0

    def _get(self, url, binary=False, limit=None):
        for attempt in range(self.retries + 1):
            wait = self.min_interval - (time.monotonic() - self._last)
            if wait > 0:
                time.sleep(wait)
            self._last = time.monotonic()
            try:
                req = urllib.request.Request(url, headers={'Accept': 'application/pdf' if binary else 'application/json',
                                                           'User-Agent': 'CTRL-SPACE-research-explorer/1.0'})
                with self.opener(req, timeout=self.timeout) as r:
                    data = r.read((limit or MAX_PDF) + 1)
                    if limit and len(data) > limit:
                        raise IngestError('file_too_large', 'The document exceeds the size limit.')
                    return data if binary else json.loads(data.decode())
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    raise IngestError('not_found', 'NTRS has no record with this ID.', 404) from None
                if e.code in (429, 500, 502, 503, 504) and attempt < self.retries:
                    time.sleep(min(60, 2 ** attempt))
                    continue
                raise IngestError('upstream_error', f'NTRS returned HTTP {e.code}.', 502) from None
            except (urllib.error.URLError, TimeoutError, ConnectionError):
                if attempt < self.retries:
                    time.sleep(min(60, 2 ** attempt))
                    continue
                raise IngestError('upstream_unavailable', 'NTRS could not be reached.', 503) from None

    def citation(self, ntrs_id):
        return self._get(f'{self.base}/citations/{ntrs_id}')

    def downloads(self, ntrs_id):
        d = self._get(f'{self.base}/citations/{ntrs_id}/downloads')
        if isinstance(d, dict):
            d = d.get('downloads') or d.get('results') or []
        return d if isinstance(d, list) else []

    def fetch(self, url):
        return self._get(url, binary=True, limit=MAX_PDF)


def _abs(url):
    return url if url.startswith('http') else urllib.parse.urljoin('https://ntrs.nasa.gov', url)


def eligible(meta):
    dist = str(meta.get('distribution', '')).lower()
    diss = str(meta.get('disseminated', '')).upper()
    if dist and dist != 'public':
        return False, 'Record is not publicly distributed.'
    if diss in ('NONE', 'METADATA_ONLY'):
        return False, 'NTRS disseminates metadata only for this record; its document may not be stored.'
    if not str(meta.get('title') or '').strip():
        return False, 'Record has no title.'
    return True, None


def pick_pdf(downloads):
    for d in downloads:
        if d.get('draft'):
            continue
        links = d.get('links') or {}
        if 'pdf' in str(d.get('mimetype', '')).lower() or links.get('pdf'):
            url = links.get('pdf') or links.get('original')
            if url:
                return _abs(url)
    return None


def extract_pages(pdf_bytes):
    try:
        import pdfplumber
    except ImportError:
        raise IngestError('extractor_missing', 'pdfplumber is not installed; run pip install pdfplumber.', 500)
    pages = []
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                text = (page.extract_text() or '').strip()
                pages.append({'page_number': i, 'text': text, 'is_empty': int(not text),
                              'needs_ocr': int(len(text) < 20 and len(page.images) > 0)})
    except Exception:
        raise IngestError('pdf_unreadable', 'The PDF could not be parsed.')
    return pages


def chunk(text, max_chars=700):
    paras = [p.strip() for p in re.split(r'\n\s*\n|(?<=[.!?])\s{2,}', text) if p.strip()]
    out, cur = [], ''
    for p in paras or [text]:
        for sent in re.split(r'(?<=[.!?])\s+', p):
            if cur and len(cur) + len(sent) + 1 > max_chars:
                out.append(cur.strip())
                cur = ''
            cur += ' ' + sent
    if cur.strip():
        out.append(cur.strip())
    return [c for c in out if len(c) >= 40]


def log(con, report_id, step, status, message=''):
    con.execute('INSERT INTO ingestion_records (at,report_id,step,status,message) VALUES (?,?,?,?,?)', (now(), report_id, step, status, message))


def ingest(con, client, ntrs_id, storage_dir):
    if not NTRS_ID.match(ntrs_id or ''):
        raise IngestError('invalid_id', 'NTRS IDs are 8 to 12 digits.', 400)
    meta = client.citation(ntrs_id)
    if str(meta.get('id')) != ntrs_id:
        raise IngestError('id_mismatch', 'NTRS returned a different record than requested.', 502)
    log(con, ntrs_id, 'metadata', 'ok')
    ok, why = eligible(meta)
    authors = '; '.join(a.get('meta', {}).get('author', {}).get('name', '') for a in meta.get('authorAffiliations') or [] if isinstance(a, dict)).strip('; ')
    pub = str(meta.get('publications', [{}])[0].get('publicationDate', '') if meta.get('publications') else '')[:10] or None
    exists = con.execute('SELECT status FROM reports WHERE id=?', (ntrs_id,)).fetchone()
    if not exists:
        con.execute('INSERT INTO reports (id,title,doc_type,published,authors,source_url,status,provider,retrieved_at,raw_metadata,created_at,loc_kind) '
                    'VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                    (ntrs_id, str(meta.get('title')).strip()[:1000], meta.get('stiType'), pub, authors or None,
                     f'https://ntrs.nasa.gov/citations/{ntrs_id}', 'pending', 'NTRS', now(), json.dumps(meta)[:200000], now(), 'page'))
    result = {'report_id': ntrs_id, 'created': not exists, 'pages': 0, 'passages': 0, 'document': 'not_stored'}
    if not ok:
        log(con, ntrs_id, 'eligibility', 'skipped', why)
        con.commit()
        return {**result, 'message': why}
    pdf_url = pick_pdf(client.downloads(ntrs_id))
    if not pdf_url:
        log(con, ntrs_id, 'download', 'skipped', 'No PDF listed')
        con.commit()
        return {**result, 'message': 'Metadata imported; NTRS lists no PDF for this record.'}
    data = client.fetch(pdf_url)
    if not data.startswith(b'%PDF-'):
        log(con, ntrs_id, 'download', 'error', 'Not a PDF signature')
        con.commit()
        raise IngestError('not_pdf', 'The downloaded file is not a PDF.', 502)
    sha = hashlib.sha256(data).hexdigest()
    dup = con.execute('SELECT id FROM reports WHERE file_sha256=? AND id<>?', (sha, ntrs_id)).fetchone()
    if dup:
        log(con, ntrs_id, 'download', 'warning', f'Same file as {dup["id"]}')
        con.commit()
        return {**result, 'message': f'Identical document already stored under {dup["id"]}; extraction skipped.'}
    os.makedirs(storage_dir, exist_ok=True)
    name = f'{secrets.token_hex(12)}.pdf'
    with open(os.path.join(storage_dir, name), 'xb') as fh:   # never overwrite
        fh.write(data)
    pages = extract_pages(data)
    con.execute('UPDATE reports SET file_sha256=?, pdf_url=? WHERE id=?', (sha, pdf_url, ntrs_id))
    con.execute('DELETE FROM passages WHERE report_id=? AND origin=\'auto\' AND verified=0', (ntrs_id,))
    n = 0
    for pg in pages:
        con.execute('INSERT OR REPLACE INTO report_pages VALUES (?,?,?,?,?)', (ntrs_id, pg['page_number'], pg['text'], pg['is_empty'], pg['needs_ocr']))
        for i, c in enumerate(chunk(pg['text'])):
            con.execute('INSERT OR IGNORE INTO passages (id,report_id,locator,kind,text,verified,origin,created_at) VALUES (?,?,?,?,?,0,\'auto\',?)',
                        (f'{ntrs_id}-p{pg["page_number"]}-{i}', ntrs_id, f'p. {pg["page_number"]}', 'unreviewed', c, now()))
            n += 1
    log(con, ntrs_id, 'extract', 'ok', f'{len(pages)} pages, {n} passages')
    con.commit()
    return {**result, 'pages': len(pages), 'passages': n, 'document': 'stored',
            'needs_ocr_pages': [p['page_number'] for p in pages if p['needs_ocr']]}

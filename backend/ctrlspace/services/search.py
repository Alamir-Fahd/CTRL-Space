"""Keyword retrieval over passages (Phase 06). BM25 with light, explainable normalisation.
The index is rebuilt from the database on demand (reindex) so admin changes take effect."""
import math
import re
import threading

STOP = set(('a an and are as at be by can do does for from has have how in is it its of on or that the their this to was were '
            'what when which who why will with about into than then there these those under over between more less most did any all '
            'very happen happens happened really much many').split())
SYN = {'o2': 'oxygen', 'acrylic': 'pmma', 'polymethylmethacrylate': 'pmma', 'ug': 'microgravity', 'μg': 'microgravity',
       'weightless': 'microgravity', 'velocity': 'flow', 'airflow': 'flow', 'speed': 'flow', 'ventilation': 'flow',
       'fire': 'flame', 'burning': 'burn', 'combustion': 'burn', 'extinguish': 'extinction', 'selfextinguish': 'extinction',
       'extinguished': 'extinction', 'quench': 'extinction', 'quenching': 'extinction', 'quenched': 'extinction',
       'sibal': 'fabric', 'cloth': 'fabric', 'cotton': 'fabric', 'co': 'monoxide', 'co2': 'dioxide'}
WORD = re.compile(r'[a-z0-9μ]+(?:-[a-z0-9]+)*')


def stem(w: str) -> str:
    if w in SYN:
        return SYN[w]
    if len(w) > 4:
        if w.endswith('ies'):
            w = w[:-3] + 'y'
        elif w.endswith(('ss', 'us', 'is')):
            pass
        elif w.endswith(('ches', 'shes', 'xes', 'sses')):
            w = w[:-2]
        elif w.endswith('s'):
            w = w[:-1]
    return SYN.get(w, w)


def tokens(text: str) -> list[str]:
    out = []
    for w in WORD.findall((text or '').lower()):
        joined = w.replace('-', '')
        out.append(joined)
        if '-' in w and joined not in SYN:
            out.extend(w.split('-'))
    return [stem(w) for w in out if w not in STOP and len(w) > 1]


class SearchIndex:
    K1, B = 1.4, 0.7

    def __init__(self):
        self._lock = threading.Lock()
        self.docs, self.df, self.avg = [], {}, 1.0

    def build(self, con) -> int:
        rows = con.execute(
            'SELECT p.id, p.report_id, p.locator, p.kind, p.text, p.verified, r.title, r.program, r.published, r.doc_type '
            'FROM passages p JOIN reports r ON r.id = p.report_id WHERE r.status = \'approved\'').fetchall()
        docs, df = [], {}
        for r in rows:
            tk = tokens(f"{r['text']} {r['locator']} {r['program'] or ''} {r['title']}")
            tf = {}
            for t in tk:
                tf[t] = tf.get(t, 0) + 1
            for t in tf:
                df[t] = df.get(t, 0) + 1
            docs.append({'row': dict(r), 'tf': tf, 'len': len(tk)})
        with self._lock:
            self.docs, self.df = docs, df
            self.avg = (sum(d['len'] for d in docs) / len(docs)) if docs else 1.0
        return len(docs)

    def search(self, query: str, limit: int = 10, offset: int = 0, verified_only: bool = False,
               program: str | None = None, kind: str | None = None, report_id: str | None = None):
        qt = list(dict.fromkeys(tokens(query)))
        with self._lock:
            docs, df, avg = self.docs, self.df, self.avg
        n = len(docs)
        hits = []
        for d in docs:
            row = d['row']
            if verified_only and not row['verified']:
                continue
            if program and row['program'] != program:
                continue
            if kind and row['kind'] != kind:
                continue
            if report_id and row['report_id'] != report_id:
                continue
            score, matched = 0.0, 0
            for t in qt:
                f = d['tf'].get(t)
                if not f:
                    continue
                matched += 1
                idf = math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5))
                score += idf * f * (self.K1 + 1) / (f + self.K1 * (1 - self.B + self.B * d['len'] / avg))
            if score > 0:
                hits.append({**row, 'score': round(score, 4), 'matched_terms': matched})
        hits.sort(key=lambda h: (-h['score'], h['id']))
        known = [t for t in qt if t in df]
        return {'terms': qt, 'known_terms': known, 'total': len(hits), 'results': hits[offset:offset + limit]}


INDEX = SearchIndex()

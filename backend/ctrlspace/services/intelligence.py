"""Deterministic scientific intelligence: question analysis, evidence evaluation and coverage, a structured
retrieval-only brief, numeric grounding of generated text, unit normalization, comparison levels and corpus gaps.

Nothing here generates scientific claims. It only organizes, labels and checks verified passages, so it works
without an AI provider and is fully testable. Coverage is a rule-based description of the evidence found,
NOT a calibrated probability that an answer is correct."""
import re

from .search import INDEX, tokens

# Standardized variables and the words that signal them (after search normalization).
VARIABLES = {
    'oxygen': {'oxygen', 'o2'},
    'flow': {'flow', 'velocity', 'airflow', 'ventilation', 'wind', 'speed'},
    'pressure': {'pressure', 'atm'},
    'temperature': {'temperature', 'thermal'},
    'gravity': {'microgravity', 'gravity', '1g', 'buoyancy', 'buoyant'},
    'material': {'pmma', 'fabric', 'sibal', 'nomex', 'material', 'plastic', 'polymethyl'},
    'extinction': {'extinction', 'blowoff', 'blow', 'limit', 'flammability'},
    'spread': {'spread', 'spreading', 'growth'},
    'products': {'monoxide', 'dioxide', 'product', 'heat', 'release', 'hrr', 'equivalence', 'toxic'},
    'geometry': {'rod', 'sheet', 'slab', 'thickness', 'thick', 'diameter', 'width', 'sphere'},
}
LABEL = {'oxygen': 'oxygen concentration', 'flow': 'flow velocity', 'pressure': 'pressure', 'temperature': 'temperature',
         'gravity': 'gravity condition', 'material': 'material', 'extinction': 'extinction / flammability limits',
         'spread': 'flame spread', 'products': 'combustion products', 'geometry': 'sample geometry'}
PROGRAMS = {'bass': 'BASS-II', 'bassii': 'BASS-II', 'saffire': 'Saffire', 'smmrf': 'BASS-II', 'mist': 'BASS-II'}
STATEMENT = {'finding': 'Reported experimental finding', 'condition': 'Reported test condition', 'method': 'Method',
             'hypothesis': 'Hypothesis (not a result)', 'context': 'Context'}


def _var_hits(text_tokens):
    return {v for v, words in VARIABLES.items() if words & text_tokens}


def analyze_question(q: str) -> dict:
    """Step 1 — understand the question (rule-based, explainable)."""
    low = q.lower()
    raw = set(re.findall(r'[a-z0-9]+', low))
    tk = set(tokens(q)) | raw
    if re.search(r'\b(compare|comparison|versus|vs\.?|differ|difference|between .+ and )\b', low):
        qtype = 'comparison'
    elif re.search(r'\b(predict|prediction|forecast|will|would|what if|expect)\b', low):
        qtype = 'prediction'
    elif re.search(r'\b(why|how does|how do|explain|mechanism|cause|causes|effect of|affect|influence)\b', low):
        qtype = 'interpretation'
    else:
        qtype = 'fact'
    variables = sorted(_var_hits(tk))
    programs = sorted({p for k, p in PROGRAMS.items() if k in raw or k in low.replace('-', '')})
    return {'type': qtype, 'variables': variables, 'variable_labels': [LABEL[v] for v in variables], 'programs': programs,
            'topic': LABEL[variables[0]] if variables else 'general microgravity combustion',
            'required_evidence': ('findings from two or more experiments' if qtype == 'comparison' else
                                  'reported findings that explain the mechanism' if qtype == 'interpretation' else
                                  'reported findings (the sources describe past tests, not predictions)' if qtype == 'prediction' else
                                  'a reported finding or condition')}


def evaluate_evidence(analysis: dict, passages: list) -> dict:
    """Step 3 — evaluate evidence: traceability, kinds, variable coverage, report spread, coverage level."""
    kinds = {}
    reports = set()
    covered = set()
    for p in passages:
        kinds[p['kind']] = kinds.get(p['kind'], 0) + 1
        reports.add(p['report_id'])
        covered |= _var_hits(set(tokens(p['text'])) | set(re.findall(r'[a-z0-9]+', p['text'].lower())))
    missing = [v for v in analysis['variables'] if v not in covered]
    findings = kinds.get('finding', 0)
    notes = []
    if not passages:
        level = 'insufficient'
    else:
        level = 'well_supported' if findings >= 2 and not missing else 'partially_supported'
        if findings == 0:
            notes.append('No reported experimental finding matched; only conditions, methods, context or hypotheses.')
            level = 'partially_supported'
        if missing:
            notes.append('No retrieved passage mentions: ' + ', '.join(LABEL[v] for v in missing) + '.')
        if kinds.get('hypothesis'):
            notes.append(f"{kinds['hypothesis']} retrieved passage(s) state a hypothesis, not a result.")
        if len(reports) == 1:
            notes.append('All evidence comes from a single report.')
        if analysis['type'] == 'comparison' and len(reports) < 2:
            notes.append('A comparison needs evidence from more than one study; only one was found.')
            level = 'partially_supported'
        if analysis['type'] == 'prediction':
            notes.append('The sources describe completed tests. CTRL+SPACE does not predict outcomes beyond them.')
            level = 'partially_supported'
    notes.append('Conflicting findings are not detected automatically; read the passages side by side.')
    return {'level': level, 'label': {'well_supported': 'Well supported', 'partially_supported': 'Partially supported',
                                      'insufficient': 'Insufficiently supported'}[level],
            'passages': len(passages), 'reports': sorted(reports), 'kinds': kinds, 'variables_covered': sorted(covered & set(analysis['variables'])),
            'variables_missing': missing, 'notes': notes,
            'definition': 'Evidence coverage describes how much verified evidence was found. It is not a probability that an answer is correct.'}


def evidence_brief(evidence: list) -> dict:
    """Retrieval-only structured output: verified passages grouped by statement type (no generated text)."""
    groups = {'findings': [], 'conditions': [], 'hypotheses': [], 'methods_context': []}
    for e in evidence:
        key = {'finding': 'findings', 'condition': 'conditions', 'hypothesis': 'hypotheses'}.get(e['kind'], 'methods_context')
        groups[key].append(e)
    sources = {}
    for e in evidence:
        s = sources.setdefault(e['report_id'], {'report_id': e['report_id'], 'title': e['report_title'], 'source_url': e['source_url'], 'locators': []})
        if e['locator'] not in s['locators']:
            s['locators'].append(e['locator'])
    return {**groups, 'sources': list(sources.values())}


NUM = re.compile(r'(?<![A-Za-z])[-−]?\d+(?:\.\d+)?')


def _numbers(text):
    return {n.replace('−', '-').lstrip('-') for n in NUM.findall(text or '')}


def numeric_grounding(text: str, cited_texts: list) -> list:
    """Numbers in generated text that do not appear in any cited passage (possible fabrication)."""
    pool = set()
    for t in cited_texts:
        pool |= _numbers(t)
    return sorted(n for n in _numbers(text) if n not in pool)


# ---------- unit normalization (original value and unit are always kept) ----------
CONVERSIONS = {'cm/s': ('m/s', 0.01, 'divide by 100'), 'mm/s': ('m/s', 0.001, 'divide by 1000'),
               'cm length': ('m length', 0.01, 'divide by 100'), 'mm': ('m', 0.001, 'divide by 1000'), 'cm': ('m', 0.01, 'divide by 100')}


def normalize(number: dict | None):
    if not number or number.get('unit') not in CONVERSIONS:
        return None
    unit, factor, how = CONVERSIONS[number['unit']]
    return {'value': round(number['value'] * factor, 6), 'unit': unit, 'method': f"{how} (from {number['unit']})", 'original': number}


def value_type(field: dict) -> str:
    """Measured / reported / derived / estimated / missing. Every stored value is a statement quoted from a
    source, so stored values are 'reported'; CTRL+SPACE stores no derived or estimated values."""
    return 'reported' if field['state'] in ('reported', 'needs_verification') else 'missing'


# ---------- comparison levels ----------
def comparison_levels(con, exps: list, rows: list) -> dict:
    by = {r['field']: r for r in rows}
    ctx = []
    def differs(field):
        vals = [c['value'] for c in by[field]['cells'] if c['state'] in ('reported', 'needs_verification')]
        return len(set(vals)) > 1, len(vals) < len(by[field]['cells'])
    checks = [('material', 'Different materials', 'Results for different materials (e.g. PMMA vs. cotton/fiberglass fabric) are not directly comparable.'),
              ('apparatus', 'Different apparatus', 'Different test hardware changes flow, scale and boundary conditions.'),
              ('flow', 'Different flow conditions', 'Flow velocity strongly shapes flame behaviour; compare only at matched flows.'),
              ('oxygen', 'Different oxygen concentrations', 'Oxygen level changes flammability; values may also use different bases.'),
              ('size', 'Different sample scales', 'Sample size and thickness change burning behaviour; results may not scale.')]
    for f, title, why in checks:
        d, partial = differs(f)
        if d:
            ctx.append({'code': f'differs_{f}', 'title': title, 'message': why})
        elif partial:
            ctx.append({'code': f'unknown_{f}', 'title': f'{LABEL.get(f, f).capitalize()} not reported for every experiment', 'message': 'Cannot confirm the experiments match on this variable.'})
    units = {c['number']['unit'] for c in by['tests']['cells'] if c.get('number')}
    if len(units) > 1:
        ctx.append({'code': 'measurement_methods', 'title': 'Different units for reported data', 'message': f"The experiments count their data differently ({', '.join(sorted(units))}), so the counts are not comparable."})
    if len({e['platform'] for e in exps}) > 1:
        ctx.append({'code': 'platform', 'title': 'Different experimental platforms', 'message': ' vs. '.join(sorted({e['platform'] for e in exps})) + '.'})
    # Level 3: findings from the experiments' sources, labelled by statement type; relationships only as observed correlations.
    findings = []
    seen = set()
    for e in exps:
        res = by['result']['cells'][exps.index(e)]
        if res.get('source') and res['source']['passage_id'] not in seen:
            seen.add(res['source']['passage_id'])
            findings.append({'experiment': e['name'], 'passage_id': res['source']['passage_id'], 'text': res['source']['quote'],
                             'locator': res['source']['locator'], 'report_id': res['source']['report_id'],
                             'statement_type': STATEMENT.get(res['source'].get('kind'), 'Reported statement')})
    # A relationship is only reported when FINDINGS (not conditions or hypotheses) from two or more experiments
    # discuss the same condition variable together with the same outcome variable.
    CONDS, OUTS = {'oxygen', 'flow', 'pressure', 'temperature', 'gravity', 'geometry'}, {'extinction', 'spread', 'products'}
    pair_exps = {}
    for f in findings:
        if f['statement_type'] != STATEMENT['finding']:
            continue
        hits = _var_hits(set(tokens(f['text'])) | set(re.findall(r'[a-z0-9]+', f['text'].lower())))
        for c in hits & CONDS:
            for o in hits & OUTS:
                pair_exps.setdefault((c, o), set()).add(f['experiment'])
    relationships = [{'variables': [LABEL[c], LABEL[o]], 'experiments': sorted(es),
                      'type': 'Observed in reported findings of several studies (correlation, not established causation)'}
                     for (c, o), es in sorted(pair_exps.items()) if len(es) >= 2]
    return {'level1': 'Descriptive: the conditions and measurements tables.',
            'level2': ctx,
            'level3': {'findings': findings, 'relationships': relationships,
                       'statement_types': ['Observed correlation', 'Reported experimental finding', 'Hypothesis', 'Causal relationship (only when a source states it)', 'Unsupported interpretation'],
                       'rule': 'Differences between these experiments are descriptive. CTRL+SPACE does not infer that any condition caused an outcome unless a cited source states it.'}}


# ---------- corpus-scoped research gaps ----------
PROBES = [('ignition', 'ignition behaviour'), ('suppression', 'fire suppression'), ('smoke', 'smoke production'), ('nomex', 'Nomex fabric'),
          ('pressure', 'reduced-pressure tests'), ('temperature', 'ambient temperature effects'), ('detection', 'fire detection'), ('toxicity', 'toxicity of products')]


def research_gaps(con, experiments_mod) -> dict:
    exps = experiments_mod.list_experiments(con)
    details = [experiments_mod.get_experiment(con, e['id']) for e in exps]
    gaps = []
    for key, label in experiments_mod.FIELDS:
        if key in ('result', 'tests'):
            continue
        states = {}
        for d in details:
            states.setdefault(d['fields'][key]['state'], []).append(d)
        rep = len(states.get('reported', []))
        for st, kind, desc in (('not_reported', 'data_not_reported', 'not stated in the verified source passages'),
                               ('not_extracted', 'data_not_extracted', 'stated elsewhere in the source (e.g. figures) but not extracted')):
            if states.get(st):
                ds = states[st]
                gaps.append({'category': kind, 'description': f'{label}: {desc} for {len(ds)} of {len(details)} experiments.',
                             'supporting_reports': sorted({d['report_id'] for d in ds}), 'experiments': [d['name'] for d in ds],
                             'missing_variables': [label], 'evidence_coverage': f'{rep} of {len(details)} experiments report it',
                             'potential_question': f'How does {label.lower()} vary across these tests, and how does it affect flame spread and extinction?',
                             'question_note': 'Template-generated question, not a scientific finding.'})
    for word, label in PROBES:
        hits = INDEX.search(word, limit=5, verified_only=True)
        if hits['total'] == 0:
            gaps.append({'category': 'topic_not_found', 'description': f'{label.capitalize()}: no verified passage in the current corpus mentions it.',
                         'supporting_reports': [], 'experiments': [], 'missing_variables': [label], 'evidence_coverage': '0 verified passages',
                         'potential_question': f'What did NASA microgravity experiments report about {label}?',
                         'question_note': 'Absent from this corpus only. This is NOT evidence that NASA never studied it.'})
    meta = [dict(r) for r in con.execute("SELECT id, title FROM reports WHERE status='approved' AND id NOT IN (SELECT report_id FROM passages WHERE verified=1)")]
    for m in meta:
        gaps.append({'category': 'no_data_in_db', 'description': f'“{m["title"]}” is catalogued, but none of its text is in the database.',
                     'supporting_reports': [m['id']], 'experiments': [], 'missing_variables': ['all variables'], 'evidence_coverage': 'metadata only',
                     'potential_question': 'Import and verify this report to extend the evidence base.', 'question_note': 'Curation action.'})
    n_reports = con.execute("SELECT COUNT(DISTINCT report_id) FROM passages WHERE verified=1").fetchone()[0]
    n_pass = con.execute("SELECT COUNT(*) FROM passages WHERE verified=1").fetchone()[0]
    return {'gaps': gaps, 'corpus': {'reports_with_text': n_reports, 'verified_passages': n_pass, 'experiments': len(details)},
            'coverage_confidence': 'Low' if n_reports < 20 else 'Medium',
            'categories': {'no_data_in_db': 'No data in current database', 'data_not_reported': 'Data not reported (in verified passages)',
                           'data_not_extracted': 'Data not extracted', 'topic_not_found': 'Research topic not found in this corpus',
                           'verified_absence': 'Verified absence in reviewed sources (requires a full human review; none recorded yet)'},
            'scope': 'Gaps are relative to the indexed CTRL+SPACE corpus only. A failed search never proves that NASA has not investigated a topic.'}

"""Experiment catalogue and comparison (Phase 08 rules).
- A value is comparable only when every selected experiment REPORTS it.
- Numeric comparison only for single values with identical units.
- Different programs / hardware / flow configuration produce explicit warnings.
- Nothing is inferred, converted silently, or filled in."""

FIELDS = [('material', 'Material'), ('geometry', 'Geometry'), ('size', 'Sample size'), ('flowDir', 'Flow direction'),
          ('flow', 'Flow velocity'), ('oxygen', 'Oxygen concentration'), ('oxygenBasis', 'Oxygen basis'), ('pressure', 'Pressure'),
          ('temperature', 'Temperature'), ('gravity', 'Gravity condition'), ('apparatus', 'Experimental apparatus'),
          ('tests', 'Tests / data points'), ('result', 'Reported result')]
GROUP = {'tests': 'measurement', 'result': 'measurement'}
LABEL = dict(FIELDS)
STATE_LABEL = {'needs_verification': 'Needs verification', 'reported': 'Reported', 'not_reported': 'Not reported', 'unknown': 'Unknown', 'unavailable': 'Unavailable',
               'not_applicable': 'Not applicable', 'not_extracted': 'Not extracted'}


def _field_rows(con, exp_id):
    rows = con.execute(
        'SELECT f.*, p.locator, p.verified AS p_verified, p.kind AS p_kind, p.report_id AS p_report, p.text AS p_text FROM experiment_fields f '
        'LEFT JOIN passages p ON p.id = f.passage_id WHERE f.experiment_id = ?', (exp_id,)).fetchall()
    out = {}
    for r in rows:
        state = 'needs_verification' if r['state'] == 'reported' and not r['p_verified'] else r['state']
        out[r['field']] = {
            'state': state, 'state_label': STATE_LABEL[state], 'verified': bool(r['p_verified']) if r['passage_id'] else None, 'value': r['value_text'],
            'number': ({'value': r['num_value'], 'unit': r['num_unit']} if r['num_value'] is not None else None),
            'reason': r['reason'],
            'source': ({'passage_id': r['passage_id'], 'report_id': r['p_report'], 'locator': r['locator'], 'kind': r['p_kind'], 'quote': r['p_text'],
                        'source_url': f"https://ntrs.nasa.gov/citations/{r['p_report']}"} if r['passage_id'] else None)}
    from . import intelligence as intel
    for f in out.values():
        f['value_type'] = intel.value_type(f)
        f['normalized'] = intel.normalize(f['number'])
    for k, _ in FIELDS:
        out.setdefault(k, {'state': 'not_extracted', 'state_label': 'Not extracted', 'value': None, 'number': None,
                           'reason': 'No record', 'source': None, 'value_type': 'missing', 'normalized': None, 'verified': None})
    return out


def list_experiments(con, program=None, include_drafts=False):
    q = 'SELECT e.*, r.title AS report_title FROM experiments e JOIN reports r ON r.id = e.report_id WHERE r.status=\'approved\''
    args = []
    if not include_drafts:
        q += ' AND e.status = \'published\''
    if program:
        q += ' AND e.program = ?'
        args.append(program)
    out = []
    for e in con.execute(q + ' ORDER BY e.program, e.name', args).fetchall():
        f = _field_rows(con, e['id'])
        out.append({**dict(e), 'material': f['material']['value'], 'reported_fields': sum(1 for v in f.values() if v['state'] == 'reported'),
                    'summary': {k: f[k]['value'] for k in ('material', 'gravity', 'flowDir', 'apparatus', 'oxygen') if f[k]['state'] == 'reported'},
                    'measurements': sum(1 for k, _ in FIELDS if GROUP.get(k) == 'measurement' and f[k]['state'] == 'reported'),
                    'total_fields': len(FIELDS)})
    return out


def get_experiment(con, exp_id, include_drafts=False):
    e = con.execute('SELECT e.*, r.title AS report_title FROM experiments e JOIN reports r ON r.id=e.report_id WHERE e.id=?', (exp_id,)).fetchone()
    if not e or (e['status'] != 'published' and not include_drafts):
        return None
    return {**dict(e), 'fields': _field_rows(con, exp_id), 'field_order': [{'key': k, 'label': l, 'group': GROUP.get(k, 'condition')} for k, l in FIELDS]}


def compare(con, ids):
    exps = [get_experiment(con, i) for i in ids]
    missing = [i for i, e in zip(ids, exps) if e is None]
    if missing:
        return None, missing
    warnings = []
    if len({e['program'] for e in exps}) > 1:
        warnings.append({'code': 'different_programs', 'message': 'Experiments come from different programs and hardware '
                         '(e.g. the BASS-II flow tunnel in the ISS glovebox vs. Saffire aboard a Cygnus spacecraft). Scale, duct size '
                         'and atmosphere differ, so differences in results cannot be attributed to one variable.'})
    dirs = {e['fields']['flowDir']['value'].split(' ')[0] for e in exps if e['fields']['flowDir']['state'] == 'reported'}
    if len(dirs) > 1:
        warnings.append({'code': 'flow_configuration', 'message': 'Flow direction differs (opposed vs. concurrent). These are different flame-spread configurations.'})
    rows = []
    for k, label in FIELDS:
        cells = [e['fields'][k] for e in exps]
        states = {c['state'] for c in cells}
        comparable = states == {'reported'}
        nums = [c['number'] for c in cells]
        units = {n['unit'] for n in nums if n}
        numeric = all(nums) and len(units) == 1
        note = None
        if not comparable and k != 'result':
            note = 'Reported for some experiments only; not comparable across all of them.' if 'reported' in states else 'Not reported for any selected experiment.'
            warnings.append({'code': 'missing_values', 'field': k, 'message': f'{label}: {note}'})
        elif any(nums) and len(units) > 1:
            note = 'Units differ; values are not compared.'
            warnings.append({'code': 'unit_mismatch', 'field': k, 'message': f'{label}: units differ ({", ".join(sorted(units))}).'})
        rows.append({'field': k, 'label': label, 'group': GROUP.get(k, 'condition'), 'cells': cells, 'comparable': comparable, 'numeric_comparable': numeric,
                     'unit': next(iter(units)) if numeric else None, 'note': note})
    chartable = [r['field'] for r in rows if any(c['number'] for c in r['cells']) and len({c['number']['unit'] for c in r['cells'] if c['number']}) == 1
                 and sum(1 for c in r['cells'] if c['number']) >= 2]
    from . import intelligence as intel
    levels = intel.comparison_levels(con, exps, rows)
    for w in levels['level2']:
        if w['code'].startswith('differs_') or w['code'] in ('measurement_methods', 'platform'):
            warnings.append({'code': w['code'], 'message': f"{w['title']}: {w['message']}"})
    return {'levels': levels, 'experiments': [{k: e[k] for k in ('id', 'name', 'program', 'platform', 'report_id', 'report_title')} for e in exps],
            'rows': rows, 'warnings': warnings, 'chartable_fields': chartable,
            'methodology': 'Values are shown exactly as reported with their source passage. Missing values are never treated as zero. '
                           'Correlation across experiments is not causation.'}, []

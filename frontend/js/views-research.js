import {api} from './api.js';
import {landing} from './views-extra.js';
import {S, R, esc, ntrs, date, LOCKIND, header, passageCard, citeBtn, fieldCell, bar, pager, saveCmp, errorBox, opt} from './ui.js';

const EXAMPLES = ['How does microgravity affect flame behavior?', 'What factors influence flame extinction?', 'What materials were investigated in BASS-II?',
  'How do experimental conditions affect flame spread?', 'What evidence is available about spacecraft fire safety?'];
const INSUFFICIENT = 'Insufficient scientific evidence was found in the available research collection to provide a reliable answer.';
const savedSet = async () => S.user ? new Set((await api.saved()).items.map(i => i.kind + ':' + i.id)) : new Set();
const saveBtn = (saved, kind, id) => `<button class="btn ghost sm" data-act="${saved.has(kind + ':' + id) ? 'unsave' : 'save'}" data-kind="${kind}" data-id="${esc(id)}">${saved.has(kind + ':' + id) ? 'Saved ✓' : (kind === 'report' ? 'Save report' : 'Save experiment')}</button>`;
const abstractLine = r => r.abstract ? `<p class="abs">${esc(r.abstract.length > 260 ? r.abstract.slice(0, 260).replace(/\s+\S*$/, '') + '…' : r.abstract)}</p>` : '<p class="abs missing">Abstract not stored in CTRL+SPACE. It is available on the NTRS record.</p>';
const evidenceStatus = r => r.passage_count ? `${r.passage_count} verified passage${r.passage_count === 1 ? '' : 's'}` : 'Metadata only: no verified evidence yet';

/* ---------- Screen 01: Home ---------- */
export async function vHome() {
  const [s, recent] = await Promise.all([api.stats(), api.reports({sort: 'indexed', limit: 4})]);
  const cards = [[R.research(), 'Research Discovery', 'Search and filter NASA reports.'], [R.library, 'Evidence Library', 'Reports and their verified passages.'],
    [R.experiments, 'Experiment Explorer', 'Conditions and results with sources.'], [R.compare, 'Compare Experiments', 'Line up 2–4 experiments honestly.'],
    [R.assistant, 'Research Assistant', 'Ask questions answered from evidence.'], [R.workspace, 'My Research', 'Saved research, collections and notes.']];
  return `<section class="hero"><div class="hero-art" role="img" aria-label="A hand holding a flame above Earth, the CTRL+SPACE artwork"></div>
    <div class="hero-copy"><p class="welcome">${S.user ? `Welcome back, ${esc(S.user.name)}` : 'Welcome to CTRL+SPACE'}</p><h1>Explore the Science of Fire in Space</h1>
      <p class="lede">Discover NASA research, investigate combustion experiments, and explore scientific evidence from space research.</p>
      <div class="ractions hero-cta"><a class="btn fire" href="${R.research()}">Explore Research</a><a class="btn ghostlight" href="${R.compare}">Compare Experiments</a></div></div></section>
  <form class="askbox wide main-search" data-form="homesearch" novalidate><label for="hs" class="sr">Search NASA research</label>
    <input id="hs" name="q" maxlength="200" placeholder="Search NASA research, combustion experiments, materials..." autocomplete="off"><button class="btn fire">Search</button></form><p class="ferr center" id="hserr" role="alert"></p>
  ${landing()}
  <section class="quickgrid">${cards.map(([h, t, d]) => `<a class="path" href="${h}"><h3>${t}</h3><p>${d}</p></a>`).join('')}</section>
  <h2 class="sub big">Research overview</h2>
  <section class="band"><div class="stat"><b>${s.reports}</b><span>research reports available</span></div><div class="stat"><b>${s.experiments}</b><span>experiments available</span></div>
    <div class="stat"><b>${s.indexed_reports}</b><span>reports with extracted, verified evidence</span></div><div class="stat"><b>${s.verified_passages}</b><span>evidence passages</span></div></section>
  <h2 class="sub big">Recently indexed research</h2>
  <div class="rgrid">${recent.items.map(r => `<article class="rcard"><div class="rtop"><span class="prog">${esc(r.program || 'NASA report')}</span><span>${date(r.published)}</span><span class="mono">NTRS ${esc(r.id)}</span></div>
    <h3><a class="linkish" href="${R.report(r.id)}">${esc(r.title)}</a></h3>${abstractLine(r)}
    <div class="ractions"><span>Source: NASA Technical Reports Server · ${evidenceStatus(r)}</span><a class="btn ghost sm" href="${R.report(r.id)}">View details</a></div></article>`).join('')}</div>
  <p class="fine">Data retrieved from NTRS on ${esc(s.retrieved_at)}.</p>`;
}

/* ---------- Screen 02: Research Discovery ---------- */
export async function vResearch() {
  const D = S.disc; const params = {...D, limit: 10}; if (!D.q && D.sort === 'relevance') params.sort = 'date';
  const [s, res, saved] = await Promise.all([api.stats(), api.reports(params), savedSet()]);
  const filters = D.category || D.material || D.year_from || D.year_to || D.evidence;
  return header('Research Discovery', 'Find NASA Technical Reports Server records on combustion and fire in space.') + `
    <form class="filters" data-form="disc" novalidate><input name="q" value="${esc(D.q)}" maxlength="200" placeholder="Keyword, e.g. flame spread oxygen" aria-label="Search reports">
      <button class="btn fire">Search</button><button type="button" class="btn ghost" data-act="discclear">Clear</button>
      <div class="frow"><label>Category<select name="category">${opt('', D.category, 'All categories')}${s.categories.map(c => opt(c, D.category)).join('')}</select></label>
      <label>Material<input name="material" value="${esc(D.material)}" maxlength="60" placeholder="e.g. PMMA"></label>
      <label>From year<input name="year_from" value="${esc(D.year_from)}" inputmode="numeric" pattern="(19|20)[0-9]{2}" maxlength="4" placeholder="2010"></label>
      <label>To year<input name="year_to" value="${esc(D.year_to)}" inputmode="numeric" pattern="(19|20)[0-9]{2}" maxlength="4" placeholder="2024"></label>
      <label>Evidence<select name="evidence">${opt('', D.evidence, 'Any')}${opt('verified', D.evidence, 'Has verified passages')}${opt('pages', D.evidence, 'Has extracted pages')}${opt('metadata_only', D.evidence, 'Metadata only')}</select></label>
      <label>Sort<select name="sort">${D.q ? opt('relevance', D.sort || 'relevance', 'Most relevant') : ''}${opt('date', D.sort, 'Newest')}${opt('oldest', D.sort, 'Oldest')}${opt('title', D.sort, 'Alphabetical')}</select></label></div></form>
    <p class="count" aria-live="polite">${res.total} report${res.total === 1 ? '' : 's'}${D.q ? ` for “${esc(D.q)}”` : ''}${filters ? ' with filters applied' : ''}</p>
    ${res.items.length ? `<div class="rlist">${res.items.map(r => `<article class="rcard"><div class="rtop"><span class="mono">NTRS ${esc(r.id)}</span><span>${date(r.published)}</span><span>${esc(r.doc_type)}</span></div>
      <h3><a class="linkish" href="${R.report(r.id)}">${esc(r.title)}</a></h3><p class="auth">${esc(r.authors || 'Authors not captured')}</p>${abstractLine(r)}
      ${r.categories.length ? `<div class="cats">${r.categories.map(c => `<span class="catchip">${esc(c)}</span>`).join('')}</div>` : ''}
      <p class="status-line"><span>Source: ${r.pdf_url ? 'NTRS record and original PDF' : 'NTRS record'}</span><span>Evidence: ${evidenceStatus(r)}</span></p>
      <div class="ractions"><a class="btn sm" href="${R.report(r.id)}">Open report</a>${saveBtn(saved, 'report', r.id)}<a class="btn ghost sm" href="${ntrs(r.id)}" target="_blank" rel="noopener">View original NASA source</a></div></article>`).join('')}</div>${pager('discpage', res)}`
      : `<div class="empty"><p>No reports match. Try fewer filters or another keyword.</p><button class="btn ghost" data-act="discclear">Clear search and filters</button></div>`}
    <p class="fine">Categories are assigned by the CTRL+SPACE team from each report’s verified passages; they are not NASA subject categories. Material filters reports by the materials of their experiments.</p>`;
}

/* ---------- Screen 03: Evidence Library ---------- */
export async function vLibrary() {
  const L = S.lib;
  const tabs = `<div class="tabs" role="tablist"><button role="tab" aria-selected="${L.tab === 'reports'}" data-act="libtab" data-tab="reports">Source reports</button><button role="tab" aria-selected="${L.tab === 'passages'}" data-act="libtab" data-tab="passages">Search inside passages</button></div>`;
  if (L.tab === 'passages') {
    let out = '<p class="empty">Search the verified, word-for-word passages. Each result shows its report and page.</p>';
    if (L.pq.length >= 2) {
      const res = await api.search({q: L.pq, kind: L.pkind, limit: 10, offset: L.poffset});
      out = `<p class="count">${res.total} passage${res.total === 1 ? '' : 's'} for “${esc(L.pq)}”</p>` + (res.items.length ? res.items.map(p => passageCard({...p, report_title: p.title}, S.user?.role === 'admin')).join('') + pager('libppage', res) : '<p class="empty">No verified passage matches.</p>');
    }
    return header('Scientific Evidence Library', 'Explore verified source reports and their available extracted passages.') + tabs + `
      <form class="filters" data-form="libp"><input name="q" value="${esc(L.pq)}" maxlength="300" placeholder="e.g. radiative quenching low flow" aria-label="Search passages">
      <select name="kind" aria-label="Passage type">${opt('', L.pkind, 'All passage types')}${['finding', 'condition', 'method', 'hypothesis', 'context'].map(k => opt(k, L.pkind, {finding: 'Reported findings', condition: 'Test conditions', method: 'Methods', hypothesis: 'Hypotheses', context: 'Context'}[k])).join('')}</select><button class="btn">Search passages</button></form>${out}`;
  }
  const [s, res, saved] = await Promise.all([api.stats(), api.reports({q: L.q, category: L.category, year_from: L.year_from, year_to: L.year_to, evidence: L.evidence, sort: L.q ? 'relevance' : L.sort, limit: 10, offset: L.offset}), savedSet()]);
  return header('Scientific Evidence Library', 'Explore verified source reports and their available extracted passages.') + tabs + `
    <form class="filters" data-form="lib" novalidate><input name="q" value="${esc(L.q)}" maxlength="200" placeholder="Search reports" aria-label="Search reports"><button class="btn">Search</button><button type="button" class="btn ghost" data-act="libclear">Clear filters</button>
      <div class="frow"><label>Category<select name="category">${opt('', L.category, 'All')}${s.categories.map(c => opt(c, L.category)).join('')}</select></label>
      <label>From year<input name="year_from" value="${esc(L.year_from)}" inputmode="numeric" maxlength="4" placeholder="2010"></label><label>To year<input name="year_to" value="${esc(L.year_to)}" inputmode="numeric" maxlength="4" placeholder="2024"></label>
      <label>Show<select name="evidence">${opt('', L.evidence, 'All reports')}${opt('verified', L.evidence, 'Only reports with extracted evidence')}${opt('pages', L.evidence, 'Only reports with extracted pages')}</select></label></div></form>
    <p class="count">${res.total} report${res.total === 1 ? '' : 's'}</p>
    ${res.items.length ? `<div class="rlist">${res.items.map(r => `<article class="rcard"><div class="rtop"><span class="mono">NTRS ${esc(r.id)}</span><span>${date(r.published)}</span></div>
      <h3><a class="linkish" href="${R.report(r.id)}">${esc(r.title)}</a></h3><p class="auth">${esc(r.authors || 'Authors not captured')}</p>
      <p class="status-line"><span>Extracted pages: ${r.page_count}</span><span>Evidence processing: ${r.passage_count ? `verified (${r.passage_count} passages)` : 'not processed yet'}</span></p>
      <div class="ractions"><a class="btn sm" href="${R.report(r.id)}">Open details</a><a class="btn ghost sm" href="${ntrs(r.id)}" target="_blank" rel="noopener">Open original source</a><button class="btn ghost sm" data-act="collect" data-kind="report" data-id="${esc(r.id)}">Save to collection</button>${saveBtn(saved, 'report', r.id)}</div></article>`).join('')}</div>${pager('libpage', res)}`
      : '<div class="empty"><p>No reports match these filters.</p><button class="btn ghost" data-act="libclear">Clear filters</button></div>'}`;
}

/* ---------- Screen 04: Report Details ---------- */
export async function vReport(id, tab = 'evidence') {
  const [r, saved] = await Promise.all([api.report(id), savedSet()]);
  let body;
  if (tab === 'pages') {
    const pg = await api.pages(id, {limit: 50});
    body = pg.items.length ? pg.items.map(p => `<article class="pagebox"><h4>Original page ${p.page_number}${p.needs_ocr ? ' <span class="tag t-hypothesis">Needs OCR</span>' : ''}</h4>${p.is_empty ? '<p class="missing">No text on this page.</p>' : `<pre>${esc(p.text)}</pre>`}</article>`).join('')
      : `<p class="empty">No extracted page text is stored for this report. Page text is created when an administrator imports the original PDF; the verified passages are on the Evidence tab.</p>`;
  } else body = r.passages.length ? r.passages.map(p => passageCard({...p, report_id: r.id, report_title: r.title}, S.user?.role === 'admin')).join('') : `<p class="empty">This report’s text hasn’t been verified yet, so it can’t support answers. Its metadata comes from the public NTRS record.</p>`;
  return `<a class="back" href="${R.library}">Back to Evidence Library</a><article class="rdetail"><div class="rtop"><span class="mono">NTRS ${esc(r.id)}</span><span>${date(r.published)}</span><span>${r.pdf_url ? 'Original PDF available' : 'NTRS record only'}</span></div>
    <h2>${esc(r.title)}</h2><p class="auth">${esc(r.authors || 'Authors not captured')}</p>
    <section class="panel"><h3>Abstract</h3>${r.abstract ? `<p>${esc(r.abstract)}</p><p class="fine">From the NTRS record, retrieved ${esc(r.retrieved_at)}.</p>` : '<p class="missing">Not stored in CTRL+SPACE. Read it on the original NTRS record.</p>'}</section>
    <dl class="meta"><dt>Report type</dt><dd>${esc(r.doc_type || '—')}</dd><dt>Report number</dt><dd>${esc(r.report_number || '—')}</dd><dt>Published</dt><dd>${date(r.published)}</dd><dt>Center</dt><dd>${esc(r.center || '—')}</dd>
      <dt>Keywords</dt><dd>${r.keywords.length ? esc(r.keywords.join(', ')) : '<span class="missing">Not captured</span>'}</dd><dt>Research category</dt><dd>${esc(r.categories.join(', ') || 'Not categorized')}</dd>
      <dt>Rights</dt><dd>${esc(r.rights || '—')}</dd><dt>Citations by</dt><dd>${esc(LOCKIND[r.loc_kind])}</dd><dt>Original NASA URL</dt><dd><a href="${esc(r.source_url)}" target="_blank" rel="noopener">${esc(r.source_url)}</a></dd></dl>
    <div class="ractions"><a class="btn fire" href="${esc(r.source_url)}" target="_blank" rel="noopener">Open original NASA source</a>${r.pdf_url ? `<a class="btn ghost" href="${esc(r.pdf_url)}" target="_blank" rel="noopener">Original PDF</a>` : ''}
      ${saveBtn(saved, 'report', r.id)}<button class="btn ghost" data-act="collect" data-kind="report" data-id="${esc(r.id)}">Add to collection</button><button class="btn ghost" data-act="share" data-kind="report" data-id="${esc(r.id)}">Share in community</button></div>
    ${r.experiments.length ? `<h3 class="sub">Related experiment records</h3><p>${r.experiments.map(e => `<a href="${R.experiment(e.id)}">${esc(e.name)}</a>`).join(' · ')}</p>` : ''}
    ${S.user ? `<form class="notes" data-form="note" data-id="${esc(r.id)}"><label for="note">Your research notes</label><textarea id="note" name="text" rows="3" maxlength="5000">${esc(r.my_note || '')}</textarea><button class="btn ghost sm">Save note</button></form>` : `<p class="fine"><a href="${R.login}">Sign in</a> to keep research notes on this report.</p>`}
    <div class="tabs" role="tablist"><button role="tab" aria-selected="${tab === 'evidence'}" data-act="rtab" data-tab="evidence" data-id="${esc(r.id)}">Evidence passages (${r.passages.length})</button><button role="tab" aria-selected="${tab === 'pages'}" data-act="rtab" data-tab="pages" data-id="${esc(r.id)}">Extracted pages (${r.page_count})</button></div>
    ${body}</article>`;
}

/* ---------- Screen 05: Research Assistant ---------- */
const COV = {well_supported: 'cov-good', partially_supported: 'cov-part', insufficient: 'cov-none'};
const QTYPE = {fact: 'fact question', comparison: 'comparison question', interpretation: 'interpretation question', prediction: 'prediction question'};
function coverageBox(r) {
  const c = r.coverage, a = r.analysis;
  return `<section class="panel coverage"><div class="covhead"><span class="covbadge ${COV[c.level]}">${esc(c.label)}</span>
    <span>Evidence coverage: ${c.passages} verified passage${c.passages === 1 ? '' : 's'} from ${c.reports.length} report${c.reports.length === 1 ? '' : 's'}</span></div>
    <p class="fine">Understood as a <b>${QTYPE[a.type]}</b>${a.variable_labels.length ? ` about ${esc(a.variable_labels.join(', '))}` : ''}${a.programs.length ? ` in ${esc(a.programs.join(', '))}` : ''}. Needs: ${esc(a.required_evidence)}.</p>
    ${c.notes.length ? `<ul class="covnotes">${c.notes.map(n => `<li>${esc(n)}</li>`).join('')}</ul>` : ''}<p class="fine">${esc(c.definition)}</p></section>`;
}
const item = i => `<li><p>${esc(i.text)}${i.ungrounded_numbers?.length ? ` <span class="tag t-hypothesis" title="Not found in the cited passages">Check number: ${esc(i.ungrounded_numbers.join(', '))}</span>` : ''}</p><div class="cites">${i.citations.map(citeBtn).join('')}</div></li>`;
function briefGroups(b) {
  const g = (title, list, note) => list.length ? `<h3 class="sub">${title}</h3>${note ? `<p class="fine">${note}</p>` : ''}${list.map(e => passageCard(e)).join('')}` : '';
  return g('Experimental evidence (reported findings)', b.findings) + g('Experimental conditions', b.conditions) + g('Hypotheses', b.hypotheses, 'Stated by the authors as hypotheses, not results.') + g('Methods and context', b.methods_context)
    + `<h3 class="sub">Source references</h3><ul class="srcs">${b.sources.map(s => `<li><a href="${R.report(s.report_id)}">${esc(s.title)}</a> — ${esc(s.locators.join(', '))} · <a href="${esc(s.source_url)}" target="_blank" rel="noopener">NTRS ${esc(s.report_id)}</a></li>`).join('')}</ul>`;
}
export function askResult(r) {
  if (!r) return '';
  if (r.loading) return `<div class="loading"><span class="orbit"></span>Understanding the question, retrieving and evaluating evidence…</div>`;
  if (r.error) return `<div class="err" role="alert"><h3>The research service is temporarily unavailable</h3><p>${esc(r.error.message)}</p><button class="btn" data-act="askretry">Try again</button></div>`;
  const briefBtn = `<div class="ractions"><button class="btn ghost" data-act="askbrief">Download research brief</button></div>`;
  if (r.status === 'insufficient_evidence') return `<div class="insuff"><h3>Insufficient evidence</h3><p>${INSUFFICIENT}</p><p class="fine">Detail: ${esc(r.reason)}</p></div>${coverageBox(r)}
    ${r.evidence.length ? `<h3 class="sub">Related sources</h3>${r.evidence.map(e => passageCard(e)).join('')}` : ''}`;
  if (r.status === 'evidence_only') return `<div class="note mode"><b>Retrieval-only mode.</b> ${r.error_code === 'not_configured' ? 'No AI provider is configured, so no answer is generated.' : esc(r.reason)} Below is the verified evidence, organized by type. Nothing on this page is AI-generated.</div>
    ${coverageBox(r)}${briefGroups(r.brief)}${briefBtn}`;
  const s = r.sections;
  return `<div class="answer"><h3 class="sub">Direct answer <span class="tag">AI-generated</span></h3><p class="summary">${esc(s.direct_answer[0].text)}</p><div class="cites">${s.direct_answer[0].citations.map(citeBtn).join('')}</div>
    ${s.explanation.length ? `<h3 class="sub">Scientific explanation</h3><ol class="points">${s.explanation.map(item).join('')}</ol>` : ''}
    ${s.evidence.length ? `<h3 class="sub">Experimental evidence</h3><ol class="points">${s.evidence.map(item).join('')}</ol>` : ''}
    ${s.conditions.length ? `<h3 class="sub">Experimental conditions</h3><ol class="points">${s.conditions.map(item).join('')}</ol>` : ''}
    <h3 class="sub">Limitations</h3><p class="limits">${esc(s.limitations || 'Not stated by the model; see the evidence notes below.')}</p>
    ${r.warnings.map(w => `<p class="limits warn">${esc(w)}</p>`).join('')}<p class="fine">${esc(r.disclaimer)} Provider: ${esc(r.provider)}.</p></div>
    ${coverageBox(r)}<h3 class="sub">Source passages used</h3>${r.evidence.map(e => passageCard(e)).join('')}${briefBtn}`;
}
export function vAssistant() {
  return header('CTRL+SPACE Research Assistant', 'Ask scientific questions and investigate findings using available NASA research evidence.') + `
    <form class="form wide askform" data-form="ask" novalidate><label for="aq" class="sr">Your question</label>
      <textarea id="aq" name="q" rows="3" maxlength="400" placeholder="Ask a question about combustion, flame spread, microgravity, or spacecraft fire safety...">${esc(S.ask?.question || '')}</textarea>
      <span class="ferr" id="askerr" role="alert"></span><button class="btn fire" ${S.busy ? 'disabled' : ''}>${S.busy ? 'Working…' : 'Ask'}</button></form>
    <div class="tries">Examples: ${EXAMPLES.map(t => `<button class="chip dark" data-act="try" data-q="${esc(t)}">${esc(t)}</button>`).join('')}</div>
    <div id="askout" aria-live="polite">${askResult(S.ask)}</div>`;
}

/* ---------- Screen 06: Experiment Explorer ---------- */
export async function vExperiments() {
  const res = await api.experiments(); const F = S.exp;
  const materials = [...new Set(res.items.flatMap(e => (e.summary.material || '').match(/PMMA|SIBAL|Nomex|cotton|fiberglass/gi) || []).map(m => m.toUpperCase() === 'PMMA' ? 'PMMA' : m[0].toUpperCase() + m.slice(1).toLowerCase()))].sort();
  const gravities = [...new Set(res.items.map(e => e.summary.gravity).filter(Boolean))];
  const programs = [...new Set(res.items.map(e => e.program))];
  const q = F.q.toLowerCase();
  const list = res.items.filter(e => (!q || `${e.name} ${e.summary.material || ''} ${e.report_title}`.toLowerCase().includes(q))
    && (!F.material || (e.summary.material || '').toLowerCase().includes(F.material.toLowerCase())) && (!F.gravity || e.summary.gravity === F.gravity) && (!F.program || e.program === F.program));
  return header('Experiment Explorer', 'Explore scientific experiments and their reported environmental conditions and measurements.') + `
    <form class="filters" data-form="expf"><input name="q" value="${esc(F.q)}" maxlength="100" placeholder="Search by name, material or report" aria-label="Search experiments">
      <select name="material" aria-label="Material">${opt('', F.material, 'All materials')}${materials.map(m => opt(m, F.material)).join('')}</select>
      <select name="gravity" aria-label="Gravity condition">${opt('', F.gravity, 'All gravity conditions')}${gravities.map(g => opt(g, F.gravity)).join('')}</select>
      <select name="program" aria-label="Experiment program">${opt('', F.program, 'All programs')}${programs.map(p => opt(p, F.program)).join('')}</select><button class="btn">Apply</button></form>
    <p class="count">${list.length} of ${res.items.length} experiments</p>
    ${list.length ? `<div class="egrid">${list.map(e => `<article class="ecard"><div class="rtop"><span class="prog">${esc(e.program)}</span><span>${esc(e.platform)}</span></div>
      <h3><a class="linkish" href="${R.experiment(e.id)}">${esc(e.name)}</a></h3>
      <dl class="mini"><dt>Report</dt><dd><a href="${R.report(e.report_id)}">${esc(e.report_title)}</a></dd><dt>Material</dt><dd>${esc(e.summary.material || 'Not extracted')}</dd>
      <dt>Gravity</dt><dd>${esc(e.summary.gravity || 'Not extracted')}</dd><dt>Environment</dt><dd>${esc(e.summary.flowDir ? e.summary.flowDir + ' flow' : 'Not extracted')}</dd><dt>Measurements</dt><dd>${e.measurements} reported</dd></dl>
      ${bar(e.reported_fields / e.total_fields, 'meter')}<small>${e.reported_fields} of ${e.total_fields} fields reported in the source</small>
      <div class="ractions"><a class="btn sm" href="${R.experiment(e.id)}">Details</a><label class="pick"><input type="checkbox" data-act="cmpbox" data-id="${esc(e.id)}" ${S.cmp.includes(e.id) ? 'checked' : ''} ${!S.cmp.includes(e.id) && S.cmp.length >= 4 ? 'disabled' : ''}> Compare</label></div></article>`).join('')}</div>`
      : '<div class="empty"><p>No experiment matches these filters.</p><button class="btn ghost" data-act="expclear">Clear filters</button></div>'}
    ${S.cmp.length ? `<div class="tray">${S.cmp.length} of 4 selected <a class="btn fire sm" href="${R.compare}">Compare</a></div>` : ''}`;
}

/* ---------- Screen 07: Experiment Details ---------- */
const verif = f => f.state === 'reported' ? 'Verified passage' : f.state === 'needs_verification' ? 'Needs verification' : '—';
export async function vExperiment(id) {
  const [e, saved, note] = await Promise.all([api.experiment(id), savedSet(), S.user ? api.expNote(id) : Promise.resolve(null)]);
  const cond = e.field_order.filter(f => f.group === 'condition'), meas = e.field_order.filter(f => f.group === 'measurement');
  const firstSrc = Object.values(e.fields).find(f => f.source)?.source;
  return `<a class="back" href="${R.experiments}">Back to Experiment Explorer</a><article class="rdetail"><div class="rtop"><span class="prog">${esc(e.program)}</span><span class="mono">ID ${esc(e.id)}</span></div>
    <h2>${esc(e.name)}</h2><dl class="meta"><dt>Associated NASA report</dt><dd><a href="${R.report(e.report_id)}">${esc(e.report_title)}</a> (NTRS ${esc(e.report_id)})</dd><dt>Experiment source</dt><dd>${esc(e.platform)}</dd><dt>Investigation lead</dt><dd>${esc(e.lead)} (as named in the source)</dd></dl>
    <h3 class="sub">Experimental conditions</h3><div class="scroll"><table class="dt"><tbody>${cond.map(f => `<tr><th scope="row">${esc(f.label)}</th><td>${fieldCell(e.fields[f.key])}</td></tr>`).join('')}</tbody></table></div>
    <h3 class="sub">Measurements and results</h3><div class="scroll"><table class="dt"><thead><tr><th>Measurement</th><th>Original value</th><th>Unit</th><th>Value type</th><th>Context</th><th>Source page</th><th>Verification</th></tr></thead><tbody>
      ${meas.map(m => { const f = e.fields[m.key]; const has = f.state === 'reported' || f.state === 'needs_verification';
        return `<tr><th scope="row">${esc(m.label)}</th><td>${has ? esc(f.value) : `<span class="missing">${esc(f.state_label)}</span>`}</td><td>${f.number ? esc(f.number.unit) : has ? 'As written in source' : '—'}</td><td>${esc(f.value_type || '—')}</td>
        <td>${esc(f.reason || (has ? e.platform : '—'))}</td><td>${f.source ? citeBtn({report_id: f.source.report_id, locator: f.source.locator, text: f.source.quote, kind: f.source.kind}) : '—'}</td><td>${verif(f)}</td></tr>`; }).join('')}</tbody></table></div>
    <p class="fine">Missing values are never shown as zero. States: Not reported (source doesn’t state it), Not extracted (stated elsewhere, e.g. only in a figure), Needs verification (its passage is under review).</p>
    <div class="ractions"><a class="btn ghost" href="${R.report(e.report_id)}">View source report</a>${firstSrc ? `<a class="btn ghost" href="${ntrs(firstSrc.report_id)}" target="_blank" rel="noopener">Open evidence on NTRS</a>` : ''}
      <button class="btn fire" data-act="addcmp" data-id="${esc(e.id)}">${S.cmp.includes(e.id) ? 'In comparison' : 'Add to comparison'}</button>${saveBtn(saved, 'experiment', e.id)}<button class="btn ghost" data-act="collect" data-kind="experiment" data-id="${esc(e.id)}">Add to collection</button><button class="btn ghost" data-act="share" data-kind="experiment" data-id="${esc(e.id)}">Share</button></div>
    ${S.user ? `<form class="notes" data-form="expnote" data-id="${esc(e.id)}"><label for="enote">Your research notes</label><textarea id="enote" name="text" rows="3" maxlength="5000">${esc(note.text)}</textarea><button class="btn ghost sm">Save note</button></form>` : ''}</article>`;
}

/* ---------- Screen 08: Compare ---------- */
export async function vCompare() {
  const all = await api.experiments();
  S.cmp = S.cmp.filter(id => all.items.some(e => e.id === id)); saveCmp();
  const f = S.cmpFilter.toLowerCase();
  const pick = all.items.filter(e => !f || `${e.name} ${e.report_title} ${e.material}`.toLowerCase().includes(f));
  const head = header('Compare Scientific Experiments', 'Investigate similarities and differences between reported experimental conditions and measurements.') + `
    <div class="selector"><div class="selhead"><input data-input="cmpfilter" value="${esc(S.cmpFilter)}" placeholder="Search experiments" aria-label="Search experiments"><b aria-live="polite">${S.cmp.length} of 4 selected</b></div>
    <div class="picker">${pick.map(e => `<label class="pick"><input type="checkbox" data-act="cmpbox" data-id="${esc(e.id)}" ${S.cmp.includes(e.id) ? 'checked' : ''} ${!S.cmp.includes(e.id) && S.cmp.length >= 4 ? 'disabled' : ''}> <span>${esc(e.name)}<small>${esc(e.report_title)}</small></span></label>`).join('')}</div></div>`;
  if (S.cmp.length < 2) return head + `<p class="note">${S.cmp.length === 1 ? 'Select at least one more experiment to compare.' : 'Select 2 to 4 experiments to compare.'}</p>`;
  const c = await api.compare(S.cmp);
  const table = grp => `<div class="scroll"><table class="dt cmp"><thead><tr><th scope="col">Field</th>${c.experiments.map(e => `<th scope="col"><a class="linkish" href="${R.experiment(e.id)}">${esc(e.name)}</a><small>${esc(e.program)}</small></th>`).join('')}</tr></thead>
    <tbody>${c.rows.filter(r => r.group === grp).map(r => `<tr><th scope="row">${esc(r.label)}</th>${r.cells.map(x => `<td>${fieldCell(x)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
  const same = c.rows.filter(r => r.comparable && new Set(r.cells.map(x => x.value)).size === 1).map(r => `${r.label}: ${r.cells[0].value}`);
  const missing = c.rows.filter(r => r.cells.some(x => x.state !== 'reported')).map(r => `${r.label} (${c.experiments.filter((_, i) => r.cells[i].state !== 'reported').map(e => e.name).join(', ')})`);
  const field = c.chartable_fields.includes(S.chart) ? S.chart : c.chartable_fields[0];
  let chart = '<p class="note">No chart: no field has a single number in the same unit for two or more of these experiments.</p>';
  if (field) {
    const row = c.rows.find(r => r.field === field); const max = Math.max(...row.cells.filter(x => x.number).map(x => x.number.value)); const unit = row.cells.find(x => x.number).number.unit;
    chart = `<div class="chartctl"><label>Chart <select data-act="chartfield">${c.chartable_fields.map(k => opt(k, field, c.rows.find(r => r.field === k).label)).join('')}</select></label></div>
      <figure class="chart"><figcaption>${esc(row.label)} (${esc(unit)})</figcaption>${row.cells.map((x, i) => `<div class="bar"><span class="bl">${esc(c.experiments[i].name)}</span>${x.number ? `<span class="bt">${bar(x.number.value / max, 'bt-in')}</span><b class="mono">${x.number.value}</b>` : `<span class="missing">${x.state === 'reported' ? 'A range or text, not a single number: not charted' : esc(x.state_label) + ': not charted'}</span>`}</div>`).join('')}</figure>`;
  }
  const L = c.levels;
  const lv = `<section class="levels"><h3 class="sub">Level 2 — Context: why these results are hard to compare</h3>
      ${L.level2.length ? `<ul class="ctxlist">${L.level2.map(w => `<li><b>${esc(w.title)}.</b> ${esc(w.message)}</li>`).join('')}</ul>` : '<p>No differences detected in material, apparatus, flow, oxygen, scale or platform.</p>'}
    <h3 class="sub">Level 3 — Evidence-based interpretation</h3>
      ${L.level3.findings.map(f => `<div class="finding"><span class="tag ${f.statement_type.startsWith('Reported experimental') ? 't-finding' : 't-condition'}">${esc(f.statement_type)}</span> <b>${esc(f.experiment)}:</b> “${esc(f.text)}” ${citeBtn({report_id: f.report_id, locator: f.locator, text: f.text, kind: 'finding'})}</div>`).join('') || '<p class="missing">No reported result is linked to these experiments.</p>'}
      ${L.level3.relationships.length ? L.level3.relationships.map(x => `<p class="note"><b>${esc(x.type)}:</b> ${esc(x.variables.join(' and '))} — ${esc(x.experiments.join(', '))}</p>`).join('') : '<p class="fine">No relationship is supported by reported findings from two or more of these experiments.</p>'}
      <p class="rule">${esc(L.level3.rule)}</p><p class="fine">Statement types used: ${esc(L.level3.statement_types.join(' · '))}.</p></section>`;
  return head + `<p class="fine">Level 1 — Descriptive: conditions and measurements as reported.</p><h3 class="sub">Conditions</h3>${table('condition')}<h3 class="sub">Measurements and results</h3>${table('measurement')}
    <h3 class="sub">Chart</h3>${chart}${lv}
    <div class="warnbox"><h3>Scientific comparison notes</h3>
      ${same.length ? `<p><b>Similarities:</b> ${esc(same.join('; '))}.</p>` : '<p><b>Similarities:</b> no field has identical reported values across all selected experiments.</p>'}
      <p><b>Differences and limitations:</b></p><ul>${c.warnings.filter(w => w.code !== 'missing_values').map(w => `<li>${esc(w.message)}</li>`).join('') || '<li>No program or configuration differences detected.</li>'}</ul>
      ${missing.length ? `<p><b>Missing values:</b> ${esc(missing.join('; '))}.</p>` : ''}<p class="fine">${esc(c.methodology)} Sources are linked in every cell.</p></div>
    <div class="ractions"><button class="btn ghost" data-act="exportcmp">Export comparison (Markdown)</button><button class="btn" data-act="cmpbrief">Generate research brief</button></div>`;
}

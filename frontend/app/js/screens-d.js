import {api, S, R, esc, ic, head, backbar, sec, empty, needSignIn, cover, passage, cite, dl, ntrs, date, ago, refHref} from './core.js';
import {CATEGORIES} from './screens-a.js';

/* ---------- 08 Search results ---------- */
export async function vSearch() {
  const q = new URLSearchParams(location.search).get('q') || S.q.research; S.q.research = q;
  const Q = S.q, res = await api.reports({q, category: Q.cat, evidence: Q.evidence, material: Q.material, sort: Q.sort || 'relevance', limit: 30});
  const chips = [[Q.cat, 'cat'], [Q.evidence && {verified: 'Has verified passages', pages: 'Has pages', metadata_only: 'Metadata only'}[Q.evidence], 'evidence'], [Q.material && `Material: ${Q.material}`, 'material'], [Q.sort && `Sort: ${Q.sort}`, 'sort']].filter(c => c[0]);
  return `${backbar(R.research, `<button class="iconbtn" data-act="filters" aria-label="Filters">${ic('filter')}</button>`)}${head('RESULTS', `${res.total} for “${esc(q)}”`)}
    <form class="searchbar" data-form="rsearch">${ic('search', 20)}<input name="q" value="${esc(q)}" maxlength="200" aria-label="Search"></form>
    ${chips.length ? `<div class="chips">${chips.map(([l]) => `<span class="chip on">${esc(l)}</span>`).join('')}<button class="chip" data-act="rclear">Clear all</button></div>` : ''}
    ${res.items.length ? `<div class="stack">${res.items.map(r => `<article class="panel res">${cover(r.id, r.program || 'NASA', date(r.published))}<h3><a href="${R.report(r.id)}">${esc(r.title)}</a></h3><p class="meta">NTRS ${esc(r.id)} · ${esc(r.doc_type || '')}</p>
      <p class="muted">${esc(r.abstract ? r.abstract.slice(0, 170) + '…' : r.passage_count ? `${r.passage_count} verified passages on ${r.categories.join(', ')}` : 'Metadata only')}</p>
      <div class="row wrap"><a class="btn primary sm" href="${R.report(r.id)}">Open</a><button class="btn ghost sm" data-act="save" data-kind="report" data-id="${esc(r.id)}">${ic('bookmark', 16)} Save</button><button class="btn ghost sm" data-act="share" data-title="${esc(r.title)}" aria-label="Share">${ic('share', 16)}</button><a class="btn ghost sm" href="${ntrs(r.id)}" target="_blank" rel="noopener">Source ↗</a></div></article>`).join('')}</div>`
      : empty('No results. Try fewer words, a material such as PMMA, or a program such as Saffire.', '<button class="btn ghost" data-act="rclear">Clear filters</button>')}`;
}

/* ---------- 11 AI research analysis ---------- */
export async function vAnalysis() {
  const A = S.analysis; const [reports, exps] = await Promise.all([api.reports({limit: 30}), api.experiments()]);
  const picker = `<form class="panel" data-form="analysis"><h3>What do you want to analyze?</h3><div class="chips">${reports.items.filter(r => r.passage_count).map(r => `<button type="button" class="chip ${A?.id === r.id ? 'on' : ''}" data-act="analyze" data-kind="report" data-id="${esc(r.id)}" data-title="${esc(r.title)}">${ic('doc', 14)} ${esc(r.title.slice(0, 34))}…</button>`).join('')}${exps.items.map(e => `<button type="button" class="chip ${A?.id === e.id ? 'on' : ''}" data-act="analyze" data-kind="experiment" data-id="${esc(e.id)}" data-title="${esc(e.name)}">${ic('flask', 14)} ${esc(e.name)}</button>`).join('')}</div>
    <div class="inline"><input name="q" maxlength="300" placeholder="…or type a research question" aria-label="Research question"><button class="btn primary sm">Analyze</button></div></form>`;
  if (!A) return `${backbar(R.assistant)}${head('ANALYSIS', 'Structured AI research analysis')}${picker}`;
  let q = A.title, rid = null, overview = '';
  if (A.kind === 'report') { const r = await api.report(A.id); rid = r.id; q = `Key findings, variables and limitations of ${r.title}`; overview = `<p><b>${esc(r.title)}</b></p><p class="meta">NTRS ${esc(r.id)} · ${date(r.published)} · ${esc(r.doc_type)}</p>${r.abstract ? `<p class="muted">${esc(r.abstract.slice(0, 300))}…</p>` : ''}`; }
  if (A.kind === 'experiment') { const e = await api.experiment(A.id); rid = e.report_id; q = `${e.fields.result.value || e.name} ${e.fields.material.value || ''} ${e.fields.flow.value || ''}`; overview = `<p><b>${esc(e.name)}</b> · ${esc(e.program)}</p><p class="meta">${esc(e.platform)} · source: ${esc(e.report_title)}</p>`; }
  if (A.kind === 'question') overview = `<p><b>${esc(A.title)}</b></p>`;
  const a = await api.assistantAsk(q.slice(0, 400), null, rid);
  const cov = a.coverage, b = a.brief || {findings: [], conditions: [], hypotheses: [], sources: []};
  const implications = a.status === 'answered' ? a.sections.explanation.map(i => `<p>${esc(i.text)} ${i.citations.map(cite).join('')}</p>`).join('') || '<p class="muted">None stated.</p>' : `<p class="muted">${a.status === 'evidence_only' ? 'Scientific implications need an AI provider (retrieval-only mode). The verified findings are listed above.' : 'Not enough evidence to state implications.'}</p>`;
  return `${backbar(R.assistant, `<button class="iconbtn" data-act="analyze" data-kind="" data-id="" aria-label="New analysis">${ic('plus')}</button>`)}${head('ANALYSIS', a.mode === 'ai' ? 'AI-generated from cited evidence' : 'Retrieval-only (no AI provider)')}
    <section class="panel"><h3>Research overview</h3>${overview}</section>
    <section class="panel"><h3>Key findings</h3>${b.findings.length ? b.findings.map(e => `<p>“${esc(e.text)}” ${cite(e)}</p>`).join('') : '<p class="muted">No reported finding matched.</p>'}</section>
    <section class="panel"><h3>Important variables</h3><div class="chips">${(a.analysis?.variable_labels || []).map(v => `<span class="chip on">${esc(v)}</span>`).join('') || '<span class="muted">None detected</span>'}</div>${cov?.variables_missing?.length ? `<p class="small">Not covered by the evidence: ${esc(cov.variables_missing.join(', '))}</p>` : ''}${b.conditions.map(e => `<p class="small">Condition: “${esc(e.text)}” ${cite(e)}</p>`).join('')}</section>
    <section class="panel"><h3>Scientific implications</h3>${implications}</section>
    <section class="panel"><h3>Evidence quality</h3>${cov ? `<p><span class="cov ${{well_supported: 'good', partially_supported: 'part', insufficient: 'none'}[cov.level]}">${esc(cov.label)}</span> ${cov.passages} passages from ${cov.reports.length} report(s)</p><p class="small">${esc(cov.definition)}</p>` : ''}</section>
    <section class="panel"><h3>Limitations</h3><ul>${(cov?.notes || []).map(n => `<li>${esc(n)}</li>`).join('')}${a.status === 'answered' && a.sections.limitations ? `<li>${esc(a.sections.limitations)}</li>` : ''}${b.hypotheses.length ? '<li>Some passages are hypotheses, not results.</li>' : ''}</ul></section>
    <section class="panel"><h3>Related sources</h3>${(b.sources || []).map(s => `<a class="menuitem" href="${R.report(s.report_id)}">${ic('doc', 18)}<span>${esc(s.title)}<small>${esc(s.locators.join(', '))}</small></span>${ic('chev', 16)}</a>`).join('') || '<p class="muted">None.</p>'}</section>
    ${S.user && a.conversation_id ? `<button class="btn ghost block" data-act="exportconvid" data-id="${a.conversation_id}">${ic('export', 16)} Export analysis</button>` : '<p class="small center">Sign in to save and export analyses.</p>'}`;
}

/* ---------- 12 Scientific Visualization Lab ---------- */
function bars(rows, fmt = String) {
  if (!rows.length) return '<p class="muted pad">No data.</p>';
  const max = Math.max(...rows.map(r => r[1]));
  return `<figure role="img">${rows.map(([l, v]) => `<div class="hb"><span>${esc(l)}</span><i data-w="${Math.max(3, v / max * 100)}"></i><b>${esc(fmt(v))}</b></div>`).join('')}</figure>`;
}
function countBy(items, key) {
  const m = {}; items.forEach(x => { const k = x[key] || 'Unknown'; m[k] = (m[k] || 0) + 1; });
  return Object.entries(m).sort((a, b) => b[1] - a[1]);
}
const VAR_LABEL = {oxygen: 'Oxygen concentration', temperature: 'Temperature', flow: 'Flow velocity', pressure: 'Pressure'};
function varChart(exps, key) {
  const nums = exps.map(e => ({name: e.name, n: e.fields[key].number})).filter(x => x.n);
  if (!nums.length) return '';
  const counts = {}; nums.forEach(x => counts[x.n.unit] = (counts[x.n.unit] || 0) + 1);
  const unit = Object.entries(counts).sort((a, b) => b[1] - a[1])[0][0];
  const rows = nums.filter(x => x.n.unit === unit); const other = nums.length - rows.length, missing = exps.length - nums.length;
  return `<section class="panel"><h3>${esc(VAR_LABEL[key])} (${esc(unit)})</h3>${bars(rows.map(x => [x.name, x.n.value]), v => `${v} ${unit}`)}
    <p class="chartcap">Values as reported in the source passage; not measured or derived by CTRL+SPACE.${missing ? ` ${missing} experiment${missing === 1 ? '' : 's'} not reported.` : ''}${other ? ` ${other} reported in a different unit, not charted here.` : ''}</p></section>`;
}
export async function vViz() {
  const p = S.tab.program || '';
  const [reports, exps] = await Promise.all([api.reports({limit: 100}), api.experiments()]);
  const full = await Promise.all(exps.items.map(e => api.experiment(e.id)));
  const programs = [...new Set(exps.items.map(e => e.program))];
  const repsF = p ? reports.items.filter(r => r.program === p) : reports.items;
  const expsF = p ? full.filter(e => e.program === p) : full;
  const years = countBy(repsF.map(r => ({y: (r.published || '').slice(0, 4) || 'Unknown'})), 'y').sort((a, b) => a[0].localeCompare(b[0]));
  return `${head('VISUALIZATION LAB', 'Explore the whole corpus')}
    <div class="chips">${['', ...programs].map(x => `<button class="chip ${x === p ? 'on' : ''}" data-act="prog" data-p="${esc(x)}">${x || 'All'}</button>`).join('')}</div>
    <section class="panel"><h3>Reports by program</h3>${bars(countBy(repsF, 'program'))}</section>
    <section class="panel"><h3>Experiments by program</h3>${bars(countBy(expsF, 'program'))}</section>
    <section class="panel"><h3>Verified passages per report</h3>${bars(repsF.map(r => [r.title.slice(0, 28), r.passage_count]).sort((a, b) => b[1] - a[1]))}</section>
    <section class="panel"><h3>Evidence completeness per experiment</h3>${bars(expsF.map(e => [e.name, Math.round(e.reported_fields / e.total_fields * 100)]), v => `${v}%`)}</section>
    <section class="panel"><h3>Report timeline</h3>${bars(years)}<p class="chartcap">By publication year, from indexed report metadata.</p></section>
    ${varChart(expsF, 'oxygen')}${varChart(expsF, 'temperature')}${varChart(expsF, 'flow')}${varChart(expsF, 'pressure')}
    <p class="muted pad">All charts use only ingested, human-verified NASA data. Missing values are never shown as zero.</p>`;
}

/* ---------- 13 Collection detail ---------- */
export async function vCollection(id) {
  if (!S.user) return backbar(R.library) + needSignIn('see collections');
  const c = await api.collection(id); const f = (S.colFilter || '').toLowerCase(); const items = c.items.filter(i => !f || i.title.toLowerCase().includes(f));
  return `${backbar(R.library, `<button class="iconbtn" data-act="delcol" data-id="${c.id}" data-name="${esc(c.name)}" aria-label="Delete collection">${ic('trash')}</button>`)}${head(esc(c.name.toUpperCase()), `${c.items.length} resource${c.items.length === 1 ? '' : 's'}`)}
    <form class="panel" data-form="editcol" data-id="${c.id}"><label class="fld"><span>Name</span><input name="name" value="${esc(c.name)}" maxlength="80" required></label><label class="fld"><span>Description</span><textarea name="description" rows="2" maxlength="300">${esc(c.description || '')}</textarea></label><button class="btn primary sm">Save</button></form>
    ${items.length ? `<ul class="list big">${items.map(i => `<li><a href="${refHref(i.kind, i.id)}">${ic(i.kind === 'report' ? 'doc' : 'flask', 18)}<span><b>${esc(i.title)}</b><small>${i.kind} · added ${ago(i.added_at)}${i.kind === 'report' && dl.has(i.id) ? ' · offline' : ''}</small></span></a><button class="iconbtn sm" data-act="rmitem" data-c="${c.id}" data-kind="${i.kind}" data-id="${esc(i.id)}" aria-label="Remove">${ic('x', 16)}</button></li>`).join('')}</ul>` : empty('Empty. Use “Add to collection” on a report or experiment.')}
    <button class="btn ghost block" data-act="exportcol" data-id="${c.id}" data-name="${esc(c.name)}">${ic('download', 16)} Export collection</button>`;
}

/* ---------- 19 Research notes editor (autosaves) ---------- */
export async function vNoteEditor(kind, id) {
  if (!S.user) return backbar(R.workspace) + needSignIn('write notes');
  const item = kind === 'report' ? await api.report(id) : await api.experiment(id);
  const text = kind === 'report' ? item.my_note : (await api.expNote(id)).text;
  setTimeout(() => {                                              // autosave 1.2 s after typing stops
    const ta = document.getElementById('noteed'), st = document.getElementById('notest'); if (!ta) return; let t;
    ta.addEventListener('input', () => { st.textContent = 'Unsaved changes…'; clearTimeout(t); t = setTimeout(async () => {
      try { await (kind === 'report' ? api.saveNote(id, ta.value) : api.saveExpNote(id, ta.value)); st.textContent = `Saved ${new Date().toLocaleTimeString()}`; } catch (e) { st.textContent = `Not saved: ${e.message}`; } }, 1200); });
  }, 0);
  return `${backbar(R.workspace)}${head('NOTE', kind === 'report' ? 'Report note' : 'Experiment note')}<section class="panel"><p class="small">Reference</p><a href="${refHref(kind, id)}"><b>${esc(item.title || item.name)}</b></a>${kind === 'report' ? `<p class="small"><a href="${ntrs(id)}" target="_blank" rel="noopener">NTRS ${esc(id)} ↗</a></p>` : ''}</section>
    <textarea id="noteed" class="editor" maxlength="5000" aria-label="Note text" placeholder="Write your research note… It saves automatically.">${esc(text || '')}</textarea><p class="small" id="notest" aria-live="polite">${text ? 'Saved' : 'Empty note'}</p>
    <p class="muted pad">Plain text. Clearing the note and waiting deletes it.</p>`;
}

/* ---------- 23 Edit profile ---------- */
export async function vEditProfile() {
  if (!S.user) return backbar(R.profile) + needSignIn('edit your profile');
  const p = await api.myProfile();
  return `${backbar(R.profile)}${head('EDIT PROFILE', 'Public name, bio and interests')}<div class="profilehead"><div class="avatar xl">${esc(p.user.name[0]).toUpperCase()}</div><p class="small">Avatar shows your initial (photo upload is not supported).</p></div>
    <form class="panel" data-form="editprofile" novalidate><p class="formerr" role="alert"></p><label class="fld"><span>Full name</span><input name="name" value="${esc(p.user.name)}" maxlength="60" required><em class="ferr" data-for="name"></em></label>
      <label class="fld"><span>Short biography</span><textarea name="bio" rows="3" maxlength="500">${esc(p.user.bio || '')}</textarea><em class="ferr" data-for="bio"></em></label>
      <label class="fld"><span>I am a…</span></label>
      <div class="picker" role="radiogroup" aria-label="I am a…">${CATEGORIES.map(([v, icon, label, desc]) => `<label class="pickrow"><input type="radio" name="category" value="${v}" ${p.user.category === v ? 'checked' : ''}>${ic(icon, 20)}<span><b>${label}</b><small>${desc}</small></span></label>`).join('')}</div>
      <em class="ferr" data-for="category"></em>
      <label class="fld"><span>Institution or university (optional)</span><input name="institution" value="${esc(p.user.institution || '')}" maxlength="120"><em class="ferr" data-for="institution"></em></label>
      <label class="fld"><span>Research interests (comma separated)</span><input name="interests" value="${esc((p.user.interests || []).join(', '))}" maxlength="320"><em class="ferr" data-for="interests"></em></label>
      <div class="row"><a class="btn ghost" href="${R.profile}">Cancel</a><button class="btn primary">Save</button></div></form>`;
}

/* ---------- 27 About ---------- */
export async function vAbout() {
  const h = await api.health().catch(() => null);
  return `${backbar(R.profile)}<div class="about"><div class="aboutlogo"></div><h1>ctrl <b>+</b> space</h1><p class="tag2">Explore. Research. Discover.</p></div>
    <section class="panel"><h3>Mission</h3><p>Make NASA’s research on fire in space easier to search, compare and understand, while keeping every statement traceable to its source.</p></section>
    <section class="panel"><h3>Vision</h3><p>Evidence-first AI: researchers and students see exactly which verified passage supports each answer, and where the evidence ends.</p></section>
    <section class="panel"><h3>Scientific purpose</h3><p>Built for the NASA Space Apps Challenge 2026 “Flame in Freefall”: microgravity combustion, flame spread, extinction limits and spacecraft fire safety.</p></section>
    <section class="panel"><h3>Technology</h3><p>Python (Flask) API with SQLite · BM25 retrieval over human-verified passages · optional AI provider (Anthropic, OpenAI or local Ollama) with citation and number checks · installable mobile app with offline reading.</p></section>
    <section class="panel"><h3>Data sources</h3><p>NASA Technical Reports Server (ntrs.nasa.gov) for reports and passages; NASA Image and Video Library (images.nasa.gov) for imagery. Each item links to its original record.</p></section>
    <section class="panel"><h3>Privacy</h3><p>Your account stores your name, email, password hash, saved research, notes, conversations and preferences. Analytics are daily counts with no personal data. You can download or delete your data in Settings.</p></section>
    <section class="panel"><h3>Scientific limitations</h3><p>CTRL+SPACE is a research exploration and decision-support platform. It is not a validated spacecraft fire-prediction system or a NASA safety-certification tool.</p></section>
    <section class="panel"><h3>Source compliance</h3><p class="small">NASA does not endorse any non-U.S. Government entity and is not responsible for information contained on non-U.S. Government websites. For non-U.S. Government websites, participants must comply with any data use parameters of that specific website.</p></section>
    <p class="center small">Version ${esc(h?.version || '—')} · Independent student project, not affiliated with or endorsed by NASA.</p>`;
}

/* ---------- 28 Help ---------- */
const FAQ = [
  ['Why does the assistant say “retrieval-only”?', 'No AI provider is configured on the server, or it is unreachable. You still get the verified evidence, grouped by type. An administrator can set one in .env.'],
  ['What does “Partially supported” mean?', 'Evidence coverage describes how much verified evidence was found (for example, only one report, or a hypothesis rather than a result). It is not a probability that an answer is correct.'],
  ['Why is a value “Not reported”?', 'The verified source passage doesn’t state it. CTRL+SPACE never fills missing values or treats them as zero.'],
  ['How do I install the app?', 'Android (Chrome): menu ⋮ → Install app. iPhone (Safari): Share → Add to Home Screen. The server address must use HTTPS.'],
  ['What works offline?', 'Reports you downloaded or opened, saved lists, and notes you write (they sync when you reconnect). AI answers, new image searches and posting need a connection.'],
  ['I forgot my password', 'Use “Forgot password” on the sign-in screen. There is no email service, so an administrator receives your request and gives you a one-time link.'],
];
export function vHelp() {
  return `${backbar(R.profile)}${head('HELP', 'Guides & troubleshooting')}
    <section class="panel"><h3>Research guide</h3><p>Search in <b>Research</b>, open a report, read its verified citations, then tap <b>Ask about this report</b> or <b>Download for offline</b>.</p></section>
    <section class="panel"><h3>AI Assistant guide</h3><p>Ask specific questions (material, condition, program). Tap a citation to read the exact passage. Follow-up questions reuse your previous question for retrieval.</p></section>
    <section class="panel"><h3>Comparing experiments</h3><p>Tick 2–4 experiments, then read the <b>Notes</b> tab: it lists why results may not be comparable.</p></section>
    ${sec('Frequently asked questions')}${FAQ.map(([q, a]) => `<details class="panel faq"><summary>${esc(q)}</summary><p>${esc(a)}</p></details>`).join('')}
    <section class="panel"><h3>Troubleshooting</h3><ul><li>Red “offline” bar: check Wi-Fi; the app shows saved research meanwhile.</li><li>“Research service unavailable”: the server isn’t running or reachable.</li><li>Images don’t load: the NASA Image Library needs internet.</li></ul></section>
    <p class="muted pad">Support contact: not configured. Ask your CTRL+SPACE administrator.</p>`;
}

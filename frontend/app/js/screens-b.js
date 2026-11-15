import {lang} from './i18n.js';
import {CONN} from './core.js';
import {api, S, R, esc, ic, head, backbar, sec, seg, empty, skel, needSignIn, cover, passage, cite, field, dl, date, ago, saveCmp} from './core.js';
import {reportCard, mediaTile} from './screens-a.js';

/* ---------- 07 AI research assistant ---------- */
const EXAMPLES = ['How does oxygen affect flame spread in microgravity?', 'What happens to flames at very low airflow?', 'What is the oxygen margin of safety for PMMA rods?', 'How efficient is combustion in microgravity?'];
const COV = {well_supported: 'good', partially_supported: 'part', insufficient: 'none'};
const FOLLOW = {oxygen: ['What oxygen levels were tested?', 'How does oxygen affect flame spread in microgravity?'], flow: ['What happens to flames at very low airflow?', 'What airflow was used in the Saffire VI tests?'],
  extinction: ['What extinction limits were reported?', 'What happens to flames at very low airflow?'], spread: ['How does sample diameter affect flame spread?', 'How does oxygen affect flame spread in microgravity?'],
  products: ['How much carbon monoxide did the flames produce?', 'How efficient is combustion in microgravity?'], gravity: ['How do 1g and microgravity results differ?', 'Why are long-duration microgravity tests needed?'],
  material: ['Which materials were tested in BASS-II?', 'What is the oxygen margin of safety for PMMA rods?'], geometry: ['How does sample thickness matter?', 'How does sample diameter affect flame spread?']};
const GENERAL = ['Under what conditions were these results reported?', 'How do 1g and microgravity results differ?'];
function followUps(a) {
  const vars = [...(a.coverage?.variables_missing || []), ...(a.analysis?.variables || [])];
  const qs = [...new Set([...vars.flatMap(v => FOLLOW[v] || []), ...GENERAL])].filter(q => q.toLowerCase() !== String(a.question || '').toLowerCase()).slice(0, 3);
  return qs.length ? `<div class="fu"><small>Suggested follow-ups</small>${qs.map(q => `<button class="chip" data-act="ask" data-q="${esc(q)}">${esc(q)}</button>`).join('')}</div>` : '';
}
const factions = a => `<div class="fact" role="group" aria-label="Follow-up actions">${a.brief?.findings?.length || a.points?.length ? `<button class="chip" data-act="fexplain" data-q="${esc((a.brief?.findings?.[0]?.text || a.points?.[0]?.text || '').slice(0, 300))}">${ic('spark', 14)} Explain this finding</button>` : ''}
  <button class="chip" data-act="fevidence">${ic('doc', 14)} Show evidence</button><button class="chip" data-act="fcompare" data-reports="${esc([...new Set((a.evidence || []).map(e => e.report_id))].join(','))}">${ic('compare', 14)} Compare experiments</button>
  <button class="chip" data-act="flimits" data-json="${esc(JSON.stringify({notes: a.coverage?.notes || [], limits: a.sections?.limitations || a.limits || '', missing: a.coverage?.variables_missing || []}))}">${ic('filter', 14)} Find limitations</button>
  <button class="chip" data-act="fquestions" data-json="${esc(JSON.stringify({vars: a.analysis?.variable_labels || [], missing: a.coverage?.variables_missing || [], reports: [...new Set((a.evidence || []).map(e => e.report_id))]}))}">${ic('learn', 14)} Generate research questions</button>
  ${a.message_id ? `<button class="chip" data-act="saveans" data-mid="${a.message_id}">${ic('bookmark', 14)} Save to workspace</button>` : ''}</div>`;
const actions = (a, text) => `<div class="aact"><button class="iconbtn sm" data-act="copyans" data-text="${esc(text)}" aria-label="Copy answer">${ic('doc', 16)}</button><button class="iconbtn sm" data-act="shareans" data-text="${esc(text)}" aria-label="Share answer">${ic('share', 16)}</button><button class="iconbtn sm" data-act="regen" aria-label="Regenerate">${ic('clock', 16)}</button>${a.message_id ? `<span class="fb"><button class="iconbtn sm" data-act="feedback" data-mid="${a.message_id}" data-r="up" aria-label="Helpful">${ic('check', 16)}</button><button class="iconbtn sm" data-act="feedback" data-mid="${a.message_id}" data-r="down" aria-label="Not helpful">${ic('x', 16)}</button></span>` : ''}</div>`;
function answerCard(a) {
  const cov = a.coverage ? `<span class="cov ${COV[a.coverage.level]}">${esc(a.coverage.label)}</span>` : '';
  const ctx = a.context_used?.follow_up ? `<p class="ctx">${ic('clock', 13)} Follow-up: retrieved together with “${esc(a.context_used.previous_question)}”</p>` : '';
  const scope = a.report_scope ? `<p class="ctx">${ic('doc', 13)} Scoped to report NTRS ${esc(a.report_scope)}</p>` : '';
  const ev = `<details class="evd"><summary>${ic('doc', 15)} ${a.evidence.length} source passage${a.evidence.length === 1 ? '' : 's'}</summary>${a.evidence.map(passage).join('')}</details>`;
  if (a.status === 'insufficient_evidence') return `<div class="msg ai">${cov}${ctx}<p><b>Insufficient evidence.</b> Insufficient scientific evidence was found in the available research collection to provide a reliable answer.</p><p class="small">${esc(a.reason)}</p>${a.evidence.length ? ev : ''}</div>`;
  if (a.status === 'stopped') return `<div class="msg ai stopped">${ic('x', 14)} Stopped. No answer was shown for this question.</div>`;
  if (a.status === 'evidence_only') {
    const b = a.brief, grp = (t, l) => l.length ? `<h4>${t}</h4>${l.map(e => `<p class="q">“${esc(e.text)}” ${cite(e)}</p>`).join('')}` : '';
    return `<div class="msg ai"><span class="mode">${ic('offline', 13)} Retrieval-only · no AI provider${a.error_code && a.error_code !== 'not_configured' ? ' (provider unavailable)' : ''}</span>${cov}${ctx}${scope}
      <span class="evtag src">Original NASA evidence</span><p class="small">Nothing below is AI-generated: these are the verified passages that match, grouped by type.</p>${grp('Reported findings', b.findings)}${grp('Test conditions', b.conditions)}${grp('Hypotheses (not results)', b.hypotheses)}${grp('Methods and context', b.methods_context)}${actions(a, b.findings.concat(b.conditions).map(e => e.text).join('\n'))}${factions(a)}${followUps(a)}</div>`;
  }
  const s = a.sections, list = (t, l) => l.length ? `<h4>${t}</h4>${l.map(i => `<p>${esc(i.text)}${i.ungrounded_numbers?.length ? ` <span class="tag warn">Check number ${esc(i.ungrounded_numbers.join(', '))}</span>` : ''} ${i.citations.map(cite).join('')}</p>`).join('')}` : '';
  return `<div class="msg ai"><span class="mode">${ic('spark', 13)} AI · ${esc(a.provider)}</span>${cov}${ctx}${scope}<span class="evtag gen">AI-generated explanation</span><p class="lead">${esc(s.direct_answer[0].text)}</p>${s.direct_answer[0].citations.map(cite).join('')}
    ${list('Scientific explanation', s.explanation)}<span class="evtag src">Cited NASA evidence</span>${list('Experimental evidence', s.evidence)}${list('Experimental conditions', s.conditions)}${s.limitations ? `<h4>Limitations</h4><p>${esc(s.limitations)}</p>` : ''}
    ${a.warnings.map(w => `<p class="small warn">${esc(w)}</p>`).join('')}${ev}<p class="small">${esc(a.disclaimer)}</p>${actions(a, s.direct_answer[0].text)}${factions(a)}${followUps(a)}</div>`;
}
export function vAssistant() {
  const msgs = S.msgs;
  return `<section class="chat"><div class="chathead"><a class="iconbtn" href="${R.history}" aria-label="Conversation history">${ic('clock')}</a><div><h1>AI ASSISTANT</h1><p><span class="aistatus ${S.ai !== 'none' && S.conn === 'online' ? 'ai' : ''}" role="status"><i></i>${S.conn !== 'online' ? CONN[S.conn] : S.ai !== 'none' ? `AI answers · ${esc(S.ai)}` : 'Retrieval-only · verified evidence'}</span>${S.conv ? ` · ${esc(S.conv.title)}` : ''}</p></div>
      <div class="row">${S.conv && S.user ? `<button class="iconbtn" data-act="exportconv" aria-label="Export conversation">${ic('export')}</button>` : ''}<button class="iconbtn" data-act="newchat" aria-label="New conversation">${ic('plus')}</button></div></div>
    <div class="msgs" id="msgs">${msgs.length ? msgs.map(m => m.role === 'user' ? `<div class="msg me">${esc(m.content)}</div>` : answerCard(m.content)).join('') : `<div class="chatempty"><div class="orb">${ic('spark', 42)}</div><h2>Ask the evidence</h2><p>Answers come only from verified NASA passages. ${S.online ? '' : '<b>You are offline: questions need a connection.</b>'}</p>
      <div class="sugg">${EXAMPLES.map(q => `<button class="chip" data-act="ask" data-q="${esc(q)}">${esc(q)}</button>`).join('')}</div>${S.user ? '' : '<p class="small">Guest mode: sign in to keep your conversation history.</p>'}${lang() === 'ar' ? '<p class="note-inline">Questions are matched against English NASA sources: ask in English.</p>' : ''}</div>`}
      ${S.busy ? `<div class="msg ai typing"><span></span><span></span><span></span> Retrieving and checking evidence…</div>` : ''}</div>
    <form class="composer" data-form="chat">${S.scope ? `<span class="scope">${ic('doc', 14)} ${esc(S.scope.title.slice(0, 38))}… <button type="button" data-act="unscope" aria-label="Remove report scope">${ic('x', 14)}</button></span>` : ''}
      <textarea name="q" rows="1" maxlength="400" placeholder="${S.online ? 'Ask about combustion, flame spread, microgravity…' : 'Offline: connect to ask'}" aria-label="Your question"></textarea>${S.busy ? `<button type="button" class="stopbtn" data-act="stopgen" aria-label="Stop generating">${ic('x', 20)}</button>` : `<button class="send" ${!S.online ? 'disabled' : ''} aria-label="Send">${ic('send', 20)}</button>`}</form></section>`;
}
export async function vHistory() {
  if (!S.user) return backbar(R.assistant) + head('HISTORY', 'Conversations') + needSignIn('keep your conversation history');
  const c = await api.conversations();
  return `${backbar(R.assistant)}${head('HISTORY', `${c.items.length} conversation${c.items.length === 1 ? '' : 's'}`)}${c.items.length ? `<ul class="list big">${c.items.map(x => `<li><a href="${R.chat(x.id)}">${ic('chat', 18)}<span><b>${esc(x.title)}</b><small>${x.questions} question${x.questions === 1 ? '' : 's'} · ${ago(x.updated_at)}${x.report_id ? ` · report ${esc(x.report_id)}` : ''}</small></span></a><button class="iconbtn sm" data-act="exportconvid" data-id="${x.id}" aria-label="Export">${ic('export', 16)}</button><button class="iconbtn sm" data-act="delconv" data-id="${x.id}" aria-label="Delete">${ic('trash', 16)}</button></li>`).join('')}</ul>` : empty('No conversations yet.', `<a class="btn primary" href="${R.assistant}">Ask a question</a>`)}`;
}

/* ---------- 08 Evidence library ---------- */
export async function vLibrary() {
  const t = S.tab.library || 'saved'; let body = '';
  if (t === 'saved') body = !S.user ? needSignIn('save research') : await (async () => { const s = await api.saved(); return s.items.length ? `<ul class="list big">${s.items.map(i => `<li><a href="${i.kind === 'report' ? R.report(i.id) : R.experiment(i.id)}">${ic(i.kind === 'report' ? 'doc' : 'flask', 18)}<span><b>${esc(i.title)}</b><small>${i.kind} · saved ${ago(i.saved_at)}${dl.has(i.id) ? ' · offline' : ''}</small></span></a></li>`).join('')}</ul>` : empty('Nothing saved yet. Tap the bookmark on a report or experiment.'); })();
  if (t === 'reports') { const r = await api.reports({limit: 30}); body = `<div class="grid2">${r.items.map(x => reportCard(x)).join('')}</div>`; }
  if (t === 'images') body = `<form class="searchbar" data-form="media">${ic('image', 20)}<input name="q" value="${esc(S.mediaQ)}" maxlength="80" aria-label="Search NASA images"><button class="btn sm primary">Search</button></form>
    <p class="muted pad">Official NASA Image and Video Library. Results are cached on the server for offline viewing.</p><div class="grid2" id="medgrid">${skel(4)}</div>`;
  if (t === 'collections') body = !S.user ? needSignIn('organize collections') : await (async () => { const c = await api.collections();
    return `<form class="inline" data-form="newcol"><input name="name" maxlength="80" placeholder="New collection" aria-label="New collection name" required><button class="btn primary sm">${ic('plus', 16)}</button></form>${c.items.map(x => `<article class="panel"><h3><a href="/app/collection/${x.id}">${esc(x.name)}</a></h3><p class="small">${x.items.length} item${x.items.length === 1 ? '' : 's'}</p>${x.items.map(i => `<a class="chip" href="${i.kind === 'report' ? R.report(i.id) : R.experiment(i.id)}">${esc(i.title.slice(0, 40))}</a>`).join('')}<div class="row"><button class="btn ghost sm" data-act="exportcol" data-id="${x.id}" data-name="${esc(x.name)}">${ic('download', 16)} Download</button></div></article>`).join('') || empty('No collections yet.')}`; })();
  if (t === 'downloads') { const d = dl.list(); body = d.length ? `<ul class="list big">${d.map(x => `<li><a href="${R.report(x.id)}">${ic('download', 18)}<span><b>${esc(x.title)}</b><small>Saved ${ago(x.saved_at)} · available offline</small></span></a></li>`).join('')}</ul>` : empty('No downloads. Use “Download for offline” on a report.'); }
  return `${head('LIBRARY', 'Evidence & media')}${seg('library', [['saved', 'Saved'], ['reports', 'Documents'], ['images', 'Images'], ['collections', 'Collections'], ['downloads', 'Downloads']], t)}${body}`;
}
export function loadMedia() {
  const el = document.getElementById('medgrid'); if (!el) return;
  api.media(S.mediaQ).then(m => { el.innerHTML = m.items.length ? m.items.map(mediaTile).join('') + `<p class="muted span2">${esc(m.source)} · retrieved ${esc(m.retrieved_at.slice(0, 10))}${m.stale ? ' · offline copy' : ''}. ${esc(m.usage)}</p>` : empty('No NASA images found.'); })
    .catch(e => { el.innerHTML = `<div class="note-inline span2">${ic('offline', 16)} ${esc(e.message)}</div>`; });
}

/* ---------- 09 Experiment explorer + 19 results ---------- */
export async function vExperiments() {
  const res = await api.experiments(); const p = S.tab.program || '';
  const list = res.items.filter(e => !p || e.program === p);
  return `${head('EXPERIMENTS', 'Microgravity combustion', `<a class="iconbtn" href="/app/viz" aria-label="Visualization Lab">${ic('chart')}</a>`)}<div class="chips">${['', ...new Set(res.items.map(e => e.program))].map(x => `<button class="chip ${x === p ? 'on' : ''}" data-act="prog" data-p="${esc(x)}">${x || 'All'}</button>`).join('')}</div>
    <div class="stack">${list.map(e => `<article class="ecard"><a href="${R.experiment(e.id)}">${cover(e.id + 'x', e.program, e.platform.split(',')[0])}</a><div class="cb"><a href="${R.experiment(e.id)}"><h3>${esc(e.name)}</h3></a>
      <p class="meta">${esc(e.summary.material || 'Material not extracted')}</p><div class="meter"><i data-w="${Math.round(e.reported_fields / e.total_fields * 100)}"></i></div><p class="meta">${e.reported_fields}/${e.total_fields} fields reported · ${e.measurements} results</p>
      <label class="tog"><input type="checkbox" data-act="cmp" data-id="${esc(e.id)}" ${S.cmp.includes(e.id) ? 'checked' : ''} ${!S.cmp.includes(e.id) && S.cmp.length >= 4 ? 'disabled' : ''}> Compare</label></div></article>`).join('')}</div>
    ${S.cmp.length ? `<a class="fab" href="${R.compare}">${ic('compare', 18)} Compare ${S.cmp.length}</a>` : ''}`;
}
export async function vExperiment(id) {
  const e = await api.experiment(id); const f = e.fields; const groups = {condition: e.field_order.filter(x => x.group === 'condition'), measurement: e.field_order.filter(x => x.group === 'measurement')};
  const method = ['apparatus', 'flowDir', 'gravity'].map(k => e.field_order.find(x => x.key === k));
  const params = groups.condition.filter(x => !['apparatus', 'flowDir', 'gravity'].includes(x.key));
  const states = {}; Object.values(f).forEach(x => { const k = x.state === 'needs_verification' ? 'reported' : x.state; states[k] = (states[k] || 0) + 1; });
  const total = Object.values(states).reduce((a, b) => a + b, 0);
  const objective = e.program === 'BASS-II' ? `<p>${esc('Program objective (BASS-II): study the ignition, flame growth, flame spread, and extinction limits for solid fuels burning in low-velocity forced flows in microgravity.')}</p>${cite({report_id: '20160000593', locator: 'Objectives', text: 'Study the ignition, flame growth, flame spread, and extinction limits for solid fuels burning in low-velocity forced flows in microgravity.', kind: 'context'})}` : '<p class="missing">Experiment-level objective not extracted from the indexed passages.</p>';
  return `<article class="detail">${backbar(R.experiments, `<button class="iconbtn" data-act="save" data-kind="experiment" data-id="${esc(e.id)}" aria-label="Save">${ic('bookmark')}</button>`)}${cover(e.id + 'x', e.program, e.platform)}
    <h1 class="dt">${esc(e.name)}</h1><p class="meta">Lead: ${esc(e.lead)} · <a href="${R.report(e.report_id)}">${esc(e.report_title)}</a></p>
    <div class="row wrap"><button class="btn primary" data-act="addcmp" data-id="${esc(e.id)}">${ic('compare', 18)} ${S.cmp.includes(e.id) ? 'In comparison' : 'Add to comparison'}</button><button class="btn ghost" data-act="analyze" data-kind="experiment" data-id="${esc(e.id)}" data-title="${esc(e.name)}">${ic('spark', 18)} Analyze with AI</button><button class="btn ghost" data-act="addtocol" data-kind="experiment" data-id="${esc(e.id)}">${ic('library', 18)} Add to collection</button><a class="btn ghost" href="${'https://ntrs.nasa.gov/citations/' + e.report_id}" target="_blank" rel="noopener">Source ↗</a>${e.psi_accession ? `<a class="btn ghost" href="/app/combustion/psi/${esc(e.psi_accession)}">${ic('flask', 18)} ${esc(e.psi_accession)} on NASA PSI</a>` : ''}</div>
    <section class="panel"><h3>Objective</h3>${objective}</section>
    <section class="panel"><h3>Scientific parameters</h3><dl class="kv">${params.map(x => `<dt>${esc(x.label)}</dt><dd>${field(f[x.key])}</dd>`).join('')}</dl></section>
    <section class="panel"><h3>Methodology</h3><dl class="kv">${method.map(x => `<dt>${esc(x.label)}</dt><dd>${field(f[x.key])}</dd>`).join('')}</dl></section>
    <section class="panel"><h3>Results</h3><dl class="kv">${groups.measurement.map(x => `<dt>${esc(x.label)}</dt><dd>${field(f[x.key])}<small>Value type: ${esc(f[x.key].value_type)}</small></dd>`).join('')}</dl></section>
    <section class="panel"><h3>Data completeness</h3><div class="sbar">${Object.entries(states).map(([k, n]) => `<i class="s-${k}" data-w="${n / total * 100}" title="${k}: ${n}"></i>`).join('')}</div>
      <p class="legend">${Object.entries(states).map(([k, n]) => `<span class="s-${k}">${n} ${k.replace('_', ' ')}</span>`).join('')}</p><p class="small">Missing values are never shown as zero. Charts of results appear in Compare only when units match.</p></section>
    ${sec('Related NASA images')}<p class="muted pad">From a NASA Image Library search for “${esc(e.program || 'microgravity combustion')}” and may not be from this exact experiment.</p><div class="rail" id="relmedia" data-q="${esc((e.program || 'microgravity') + ' microgravity')}">${skel(2)}</div>
    ${S.user ? `<form class="panel" data-form="expnote" data-id="${esc(e.id)}"><h3>My notes</h3><textarea name="text" rows="3" maxlength="5000" aria-label="Notes"></textarea><button class="btn ghost sm">Save note</button></form>` : ''}</article>`;
}

/* ---------- 10 Experiment comparison ---------- */
export async function vCompare() {
  const all = await api.experiments(); S.cmp = S.cmp.filter(id => all.items.some(e => e.id === id)); saveCmp();
  const pick = `<div class="picker">${all.items.map(e => `<label class="pickrow"><input type="checkbox" data-act="cmp" data-id="${esc(e.id)}" ${S.cmp.includes(e.id) ? 'checked' : ''} ${!S.cmp.includes(e.id) && S.cmp.length >= 4 ? 'disabled' : ''}><span><b>${esc(e.name)}</b><small>${esc(e.program)} · ${esc(e.platform.split(',')[0])}</small></span></label>`).join('')}</div>`;
  const h = head('COMPARE', `${S.cmp.length} of 4 selected`);
  if (S.cmp.length < 2) return h + `<p class="note-inline">${ic('compare', 16)} ${S.cmp.length === 1 ? 'Select one more experiment.' : 'Select 2 to 4 experiments.'}</p>` + pick;
  const c = await api.compare(S.cmp); const t = S.tab.compare || 'parameters';
  const cards = grp => { const rows = c.rows.filter(r => r.group === grp);
    return `<p class="small">Swipe between experiments. <b class="warn">Differs</b> = reported values differ; <b class="cyan">missing</b> = not reported or not extracted.</p><div class="swipe" id="swipe" aria-label="Experiments, swipe to compare">${c.experiments.map((e, i) => `<article class="xcard" aria-label="${esc(e.name)}"><span class="prog">${esc(e.program)} · ${i + 1}/${c.experiments.length}</span><h3>${esc(e.name)}</h3>
      ${rows.map(r => { const cell = r.cells[i]; const vals = r.cells.filter(x => x.state === 'reported').map(x => x.value); const differs = vals.length > 1 && new Set(vals).size > 1 && cell.state === 'reported'; const miss = cell.state !== 'reported';
        return `<div class="var ${differs ? 'diff' : ''} ${miss ? 'miss' : ''}"><b>${esc(r.label)}</b>${field(cell)}</div>`; }).join('')}</article>`).join('')}</div>
      <div class="sdots">${c.experiments.map((_, i) => `<i class="${i ? '' : 'on'}"></i>`).join('')}</div>`; };
  let body = '';
  if (t === 'parameters') body = cards('condition');
  if (t === 'outcomes') { const field_ = c.chartable_fields[0]; let chart = '';
    if (field_) { const row = c.rows.find(r => r.field === field_), max = Math.max(...row.cells.filter(x => x.number).map(x => x.number.value)), unit = row.cells.find(x => x.number).number.unit;
      const desc = row.cells.map((x, i) => `${c.experiments[i].name}: ${x.number ? x.number.value + ' ' + unit : x.state_label}`).join('; ');
      chart = `<section class="panel"><h3>${esc(row.label)} (${esc(unit)})</h3><figure role="img" aria-label="${esc(row.label + ' — ' + desc)}">${row.cells.map((x, i) => `<div class="hb"><span>${esc(c.experiments[i].name)}</span>${x.number ? `<i data-w="${x.number.value / max * 100}"></i><b>${x.number.value} ${esc(unit)}</b>` : `<em>${esc(x.state === 'reported' ? 'not a single number' : x.state_label)}</em>`}</div>`).join('')}</figure>
        <p class="chartcap">Values: reported (as stated in the source passage, not measured or derived by CTRL+SPACE). Sources: ${row.cells.filter(x => x.source).map(x => `NTRS ${esc(x.source.report_id)} ${esc(x.source.locator)}`).join('; ')}.</p></section>`; }
    body = cards('measurement') + (chart || '<p class="muted pad">No chart: no shared single-number field with matching units.</p>'); }
  if (t === 'notes') { const L = c.levels;
    body = `<section class="panel"><h3>Why these are hard to compare</h3><ul>${L.level2.map(w => `<li><b>${esc(w.title)}.</b> ${esc(w.message)}</li>`).join('') || '<li>No differences detected.</li>'}</ul></section>
      <section class="panel"><h3>What the sources report</h3>${L.level3.findings.map(x => `<p><span class="tag">${esc(x.statement_type)}</span> <b>${esc(x.experiment)}:</b> “${esc(x.text)}” ${cite({report_id: x.report_id, locator: x.locator, text: x.text, kind: 'finding'})}</p>`).join('')}<p class="rule">${esc(L.level3.rule)}</p></section>`; }
  if (t === 'ai') body = `<div id="cmpai">${skel(2)}</div>`;
  return `${h}${pick}${seg('compare', [['parameters', 'Parameters'], ['outcomes', 'Outcomes'], ['notes', 'Notes'], ['ai', 'AI summary']], t)}${body}
    <div class="row wrap"><button class="btn ghost" data-act="exportcmp">${ic('download', 18)} Export</button><button class="btn ghost" data-act="cmpbrief">${ic('doc', 18)} Research brief</button></div>`;
}
export function loadCompareAi() {
  const el = document.getElementById('cmpai'); if (!el) return;
  api.compareAi(S.cmp).then(r => {
    if (r.status !== 'answered') { el.innerHTML = `<div class="msg ai"><span class="mode">${ic('offline', 13)} Retrieval-only</span><p>${esc(r.reason)}</p><h4>Context warnings</h4>${r.context_warnings.map(w => `<p>• <b>${esc(w.title)}.</b> ${esc(w.message)}</p>`).join('')}<details class="evd"><summary>${r.evidence.length} source passages</summary>${r.evidence.map(passage).join('')}</details></div>`; return; }
    const s = r.sections; el.innerHTML = `<div class="msg ai"><span class="mode">${ic('spark', 13)} AI · ${esc(r.provider)}</span><p class="lead">${esc(s.direct_answer[0].text)}</p>${s.direct_answer[0].citations.map(cite).join('')}${['explanation', 'evidence', 'conditions'].map(k => s[k].map(i => `<p>${esc(i.text)} ${i.citations.map(cite).join('')}</p>`).join('')).join('')}${s.limitations ? `<h4>Limitations</h4><p>${esc(s.limitations)}</p>` : ''}<p class="small">${esc(r.disclaimer)} ${esc(r.rule)}</p></div>`;
  }).catch(e => { el.innerHTML = `<div class="note-inline">${ic('offline', 16)} ${esc(e.message)}</div>`; });
}

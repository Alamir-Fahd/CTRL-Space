import {ApiError} from './api.js';

export const $ = (s, el = document) => el.querySelector(s);
export const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const ntrs = id => `https://ntrs.nasa.gov/citations/${encodeURIComponent(id)}`;
export const KIND = {finding:'Reported finding', method:'Method', condition:'Test conditions', hypothesis:'Hypothesis (not a result)', context:'Context', unreviewed:'Unreviewed'};
export const LOCKIND = {page:'Printed page number', section:'Poster section heading (the source has no page breaks)', slide:'Printed slide number', abstract:'NTRS record abstract'};
export const date = s => s ? esc(String(s).slice(0, 10)) : '—';
export const when = s => { if (!s) return ''; const d = new Date(s); return isNaN(d) ? esc(s) : esc(d.toLocaleString(undefined, {dateStyle: 'medium', timeStyle: 'short'})); };

/* Routes (spec PART 2): one place that builds every in-app URL. */
export const R = {
  home: '/', research: (q) => '/research' + (q ? '?q=' + encodeURIComponent(q) : ''), library: '/library',
  report: id => '/library/' + encodeURIComponent(id), assistant: '/assistant', experiments: '/experiments',
  experiment: id => '/experiments/' + encodeURIComponent(id), compare: '/compare', workspace: '/my-research',
  studio: '/studio', lesson: id => '/studio/' + encodeURIComponent(id), challenges: '/challenges',
  challenge: id => '/challenges/' + encodeURIComponent(id), community: '/community', room: id => '/community/' + encodeURIComponent(id),
  post: id => '/community/post/' + encodeURIComponent(id), gaps: '/gaps', demo: '/demo', profile: '/profile', settings: '/settings', admin: '/admin', login: '/login', register: '/register',
};
export const refHref = (kind, id) => kind === 'report' ? R.report(id) : R.experiment(id);

export const S = {
  user: null, prefs: {theme: localStorage.getItem('cs.theme') || 'system', history: true},
  cmp: JSON.parse(sessionStorage.getItem('cs.cmp') || '[]'), chart: null, cmpFilter: '',
  disc: {q: '', category: '', material: '', year_from: '', year_to: '', evidence: '', sort: '', offset: 0},
  lib: {q: '', category: '', year_from: '', year_to: '', evidence: '', sort: 'date', offset: 0, tab: 'reports', pq: '', pkind: '', poffset: 0},
  exp: {q: '', material: '', gravity: '', program: ''},
  ask: null, busy: false, adminTab: 'overview', wsTab: 'saved', attempt: null, share: null, editing: null, health: null,
};
export const saveCmp = () => sessionStorage.setItem('cs.cmp', JSON.stringify(S.cmp));

export function applyTheme(t) {
  S.prefs.theme = t;
  if (t === 'system') delete document.documentElement.dataset.theme; else document.documentElement.dataset.theme = t;
  try { localStorage.setItem('cs.theme', t); } catch { /* private mode */ }
}

export function toast(msg) { const t = $('#toast'); t.textContent = msg; t.classList.add('on'); clearTimeout(t._h); t._h = setTimeout(() => t.classList.remove('on'), 3400); }

export function errorBox(e, retry = true) {
  if (e instanceof ApiError && e.code === 'network') $('#offline').hidden = false;
  const msg = e instanceof ApiError ? e.message : 'Something unexpected happened in the page.';
  const title = e.status === 404 ? 'Not found' : e.status === 403 ? 'Permission denied' : e.status === 401 ? 'Sign in required' : 'This didn’t load';
  return `<div class="err" role="alert"><h3>${title}</h3><p>${esc(msg)}</p>${e.status === 401 ? `<a class="btn" href="${R.login}">Sign in</a>` : retry ? '<button class="btn" data-act="retry">Retry</button>' : ''}</div>`;
}
export const skeleton = (n = 3) => Array.from({length: n}, () => '<div class="skel" aria-hidden="true"></div>').join('') + '<span class="sr">Loading…</span>';
export const bar = (frac, cls = 'bars') => `<span class="${cls}"><svg viewBox="0 0 100 12" preserveAspectRatio="none" aria-hidden="true"><rect class="bg" width="100" height="12" rx="3"/><rect class="fg" width="${Math.max(1, Math.min(100, frac * 100)).toFixed(1)}" height="12" rx="3"/></svg></span>`;
export const header = (title, sub = '') => `<header class="vh"><h2>${title}</h2>${sub ? `<p>${sub}</p>` : ''}</header>`;
export const signInPrompt = what => `<div class="empty"><p>Sign in to ${what}.</p><div class="ractions"><a class="btn fire" href="${R.login}">Sign in</a><a class="btn ghost" href="${R.register}">Create an account</a></div></div>`;
export const pager = (act, res) => res.total > res.limit ? `<div class="pager"><button class="btn ghost sm" data-act="${act}" data-d="-1" ${res.offset === 0 ? 'disabled' : ''}>Previous</button><span>Page ${Math.floor(res.offset / res.limit) + 1} of ${Math.ceil(res.total / res.limit)} · ${res.total} results</span><button class="btn ghost sm" data-act="${act}" data-d="1" ${res.offset + res.limit >= res.total ? 'disabled' : ''}>Next</button></div>` : '';
export const opt = (v, cur, label) => `<option value="${esc(v)}" ${String(v) === String(cur) ? 'selected' : ''}>${esc(label ?? v)}</option>`;

export function citeBtn(c) { return `<button class="cite" data-act="passage" data-json="${esc(JSON.stringify(c))}" title="${esc(c.report_title || '')}"><span class="mono">${esc(c.report_id)}</span> ${esc(c.locator)}</button>`; }
export function passageCard(p, admin = false) {
  return `<article class="passage ${p.kind === 'hypothesis' ? 'hyp' : ''}"><div class="pmeta"><span class="tag t-${esc(p.kind)}">${KIND[p.kind] || esc(p.kind)}</span><span>${esc(p.locator)}</span>${p.id ? `<span class="mono">${esc(p.id)}</span>` : ''}</div>
    <blockquote>${esc(p.text)}</blockquote>
    <div class="psrc">${p.report_title ? `<a href="${R.report(p.report_id)}">${esc(p.report_title)}</a>` : ''}<a href="${ntrs(p.report_id)}" target="_blank" rel="noopener">Open NASA source (NTRS ${esc(p.report_id)})</a>${admin && p.id ? `<button class="btn ghost sm" data-act="flag" data-id="${esc(p.id)}">Flag extraction</button>` : ''}</div></article>`;
}
export function fieldCell(f) {
  if (f.state === 'reported' || f.state === 'needs_verification') return `<span>${esc(f.value)}</span>${f.normalized ? `<small class="norm">Normalized: ${esc(f.normalized.value)} ${esc(f.normalized.unit)} (${esc(f.normalized.method)}; original kept)</small>` : ''}${f.state === 'needs_verification' ? ' <span class="tag t-hypothesis">Needs verification</span>' : ''} ${f.source ? citeBtn({report_id: f.source.report_id, locator: f.source.locator, text: f.source.quote, kind: f.source.kind}) : ''}`;
  return `<span class="missing">${esc(f.state_label)}</span>${f.reason && f.reason !== f.state_label ? `<small>${esc(f.reason)}</small>` : ''}`;
}
export const refLink = r => r ? `<a class="refchip" href="${refHref(r.kind, r.id)}">${r.kind === 'report' ? 'Report' : 'Experiment'}: ${esc(r.title || r.id)}</a>` : '';
export function download(name, text, type = 'text/markdown') {
  const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([text], {type})); a.download = name;
  document.body.append(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(a.href), 10000);
}

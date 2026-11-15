/* CTRL+SPACE mobile app — shared core: state, routes, icons, UI primitives, offline downloads, sync outbox. */
import {api, ApiError} from '/js/api.js';
export {api, ApiError};

export const $ = (s, el = document) => el.querySelector(s);
export const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
export const enc = encodeURIComponent;
export const ntrs = id => `https://ntrs.nasa.gov/citations/${enc(id)}`;
export const date = s => s ? esc(String(s).slice(0, 10)) : '—';
export const ago = s => { const d = (Date.now() - new Date(s)) / 1000; if (isNaN(d)) return ''; if (d < 60) return 'just now'; if (d < 3600) return `${Math.floor(d / 60)} min ago`; if (d < 86400) return `${Math.floor(d / 3600)} h ago`; return `${Math.floor(d / 86400)} d ago`; };
export const KIND = {finding: 'Reported finding', method: 'Method', condition: 'Test conditions', hypothesis: 'Hypothesis', context: 'Context'};

export const R = {
  home: '/app', welcome: '/app/welcome', login: '/app/login', register: '/app/register', forgot: '/app/forgot', research: '/app/research',
  report: id => `/app/report/${enc(id)}`, assistant: '/app/assistant', chat: id => `/app/assistant/${id}`, history: '/app/history', library: '/app/library',
  experiments: '/app/experiments', experiment: id => `/app/experiments/${enc(id)}`, compare: '/app/compare', workspace: '/app/workspace',
  learn: '/app/learn', lesson: id => `/app/learn/${enc(id)}`, challenge: id => `/app/challenge/${enc(id)}`, community: '/app/community',
  room: id => `/app/community/${enc(id)}`, post: id => `/app/community/post/${id}`, user: id => `/app/user/${id}`, profile: '/app/profile',
  settings: '/app/settings', offline: '/app/offline', notifications: '/app/notifications', demo: '/app/demo',
};
export const refHref = (k, id) => k === 'report' ? R.report(id) : R.experiment(id);

export const S = {
  user: null, prefs: {}, unread: 0, online: navigator.onLine, conn: navigator.onLine ? 'online' : 'offline', ai: 'none', ctl: null, busy: false, conv: null, msgs: [], scope: null,
  cmp: JSON.parse(sessionStorage.getItem('cs.cmp') || '[]'), tab: {}, q: {research: '', cat: '', evidence: '', sort: '', material: ''}, mediaQ: 'microgravity combustion', psiQ: 'combustion',
};
export const saveCmp = () => sessionStorage.setItem('cs.cmp', JSON.stringify(S.cmp));

const P = {
  home: '<path d="M3 11l9-8 9 8v9a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/>', search: '<circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/>',
  spark: '<path d="M12 3l2.2 5.8L20 11l-5.8 2.2L12 19l-2.2-5.8L4 11l5.8-2.2z"/>', flask: '<path d="M9 3h6M10 3v6L4.2 19a1.4 1.4 0 0 0 1.2 2h13.2a1.4 1.4 0 0 0 1.2-2L14 9V3M7 15h10"/>',
  library: '<rect x="3" y="4" width="4" height="16" rx="1"/><rect x="9" y="4" width="4" height="16" rx="1"/><path d="M15.5 5.5l3.8-1 3 15-3.8 1z"/>',
  bell: '<path d="M6 8a6 6 0 1 1 12 0c0 7 3 9 3 9H3s3-2 3-9M10 21a2 2 0 0 0 4 0"/>', back: '<path d="M15 18l-6-6 6-6"/>',
  share: '<circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="M8.6 13.5l6.8 4M15.4 6.5l-6.8 4"/>',
  bookmark: '<path d="M6 3h12v18l-6-4-6 4z"/>', download: '<path d="M12 3v12M7 10l5 5 5-5M5 21h14"/>', user: '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
  compare: '<path d="M7 3v18M17 3v18M3 8h8M13 16h8"/>', offline: '<path d="M2 2l20 20M8.5 16.5a5 5 0 0 1 7 0M5 12.5a10 10 0 0 1 5-2.8M19 12.5a10 10 0 0 0-3-2.2M12 20h.01"/>',
  gear: '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9L7 7M17 17l2.1 2.1M4.9 19.1L7 17M17 7l2.1-2.1"/>',
  chat: '<path d="M21 12a8 8 0 0 1-11.6 7.1L3 21l1.9-6.4A8 8 0 1 1 21 12z"/>', learn: '<path d="M4 4h7a3 3 0 0 1 3 3v13a2 2 0 0 0-2-2H4zM20 4h-5a3 3 0 0 0-3 3v13a2 2 0 0 1 2-2h6z"/>',
  users: '<circle cx="9" cy="8" r="3.5"/><path d="M2 20a7 7 0 0 1 14 0M16 4.5a3.5 3.5 0 0 1 0 7M18 13.5a6 6 0 0 1 4 6"/>', chev: '<path d="M9 6l6 6-6 6"/>',
  send: '<path d="M4 12l16-8-6 16-2-7z"/>', plus: '<path d="M12 5v14M5 12h14"/>', image: '<rect x="3" y="3" width="18" height="18" rx="3"/><circle cx="9" cy="9" r="2"/><path d="M21 16l-5-5-9 9"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>', check: '<path d="M5 12l5 5 9-10"/>', x: '<path d="M6 6l12 12M18 6L6 18"/>',
  trash: '<path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13"/>', filter: '<path d="M3 5h18l-7 8v6l-4 2v-8z"/>', export: '<path d="M12 15V3M7 8l5-5 5 5M5 13v7h14v-7"/>',
  wifi: '<path d="M2 8.5a15 15 0 0 1 20 0M5 12.5a10 10 0 0 1 14 0M8.5 16.5a5 5 0 0 1 7 0M12 20h.01"/>', play: '<path d="M7 4l13 8-13 8z"/>', doc: '<path d="M6 2h9l5 5v15H6zM14 2v6h6M9 13h8M9 17h6"/>',
  chart: '<path d="M4 20V11M10 20V4M16 20v-8M22 20H2"/>',
  rocket: '<path d="M12 2c2.2 2.1 3.8 5.3 3.8 8.8 0 2.3-.6 4.3-1.6 5.9l-2.2 3.3-2.2-3.3c-1-1.6-1.6-3.6-1.6-5.9C8.2 7.3 9.8 4.1 12 2z"/><circle cx="12" cy="9.3" r="1.6"/><path d="M8.6 13.8c-1.6.2-3 1.4-3.3 3.8M15.4 13.8c1.6.2 3 1.4 3.3 3.8M10 19l-.8 3M14 19l.8 3"/>',
};
export const ic = (n, s = 22) => `<svg class="ic" width="${s}" height="${s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${P[n] || ''}</svg>`;

/* ---------- UI primitives ---------- */
export const head = (title, sub, right = '') => `<header class="ah"><div><h1>${title}</h1>${sub ? `<p>${sub}</p>` : ''}</div>${right}</header>`;
export const backbar = (href, right = '') => `<div class="topbar"><a class="iconbtn" href="${href}" data-back aria-label="Back">${ic('back')}</a><span class="sp"></span>${right}</div>`;
export const sec = (title, link) => `<div class="sech"><h2>${title}</h2>${link ? `<a href="${link[0]}">${link[1]} ${ic('chev', 14)}</a>` : ''}</div>`;
export const seg = (key, opts, cur) => `<div class="seg" role="tablist">${opts.map(([k, l]) => `<button role="tab" aria-selected="${k === cur}" data-act="seg" data-key="${key}" data-v="${k}">${l}</button>`).join('')}</div>`;
export const empty = (msg, cta = '') => `<div class="empty">${ic('spark', 28)}<p>${msg}</p>${cta}</div>`;
export const skel = (n = 3) => Array.from({length: n}, () => '<div class="skel"></div>').join('');
export const needSignIn = what => `<div class="empty">${ic('user', 28)}<p>Sign in to ${what}.</p><div class="row"><a class="btn primary" href="${R.login}">Sign in</a><a class="btn ghost" href="${R.register}">Create account</a></div></div>`;
export function errBox(e) {
  const offline = e instanceof ApiError && (e.code === 'network' || e.code === 'requires_internet');
  return `<div class="errbox">${ic(offline ? 'offline' : 'x', 26)}<h3>${offline ? 'Needs an internet connection' : e.status === 404 ? 'Not found' : e.status === 403 ? 'Permission denied' : 'Something went wrong'}</h3><p>${esc(e.message || 'Unexpected error.')}</p><button class="btn ghost" data-act="retry">Try again</button></div>`;
}
const PAL = [['#1B3B8F', '#22D3EE'], ['#3B1E8F', '#8B5CF6'], ['#0E4C6B', '#2F7BFF'], ['#4A1D6E', '#22D3EE'], ['#13306B', '#8B5CF6']];
// Real NASA Image and Video Library photos, one set per research program actually present in this corpus
// (verified relevant by title/description before use here — never a generic/unrelated stock photo).
const PROGRAM_PHOTOS = {
  'BASS-II': ['iss040e011004', 'iss040e011006', 'iss040e011008', 'iss040e088800'],   // astronaut at the Microgravity Science Glovebox during a BASS session
  'Saffire': ['jsc2023e046377', 'iss051e039882'],                                    // Saffire VI hardware loaded into Cygnus; Saffire-II in Cygnus during cargo ops
  'SAME': ['iss024e008351', 'iss015e27411'],                                         // Walker working SAME in the MSG during Expedition 24; Anderson with SAME hardware during Expedition 15
  'FLEX': ['iss043e190395', 'iss035e017702'],                                        // Virts preparing MDCA for Flame Extinguishment runs; Cassidy replacing an MDCA fuel reservoir
};
const photoUrl = id => `https://images-assets.nasa.gov/image/${id}/${id}~medium.jpg`;
export function cover(seed, label, sub = '') {
  let h = 0; for (const c of String(seed)) h = (h * 31 + c.charCodeAt(0)) >>> 0;
  const [a, b] = PAL[h % PAL.length]; const x = 20 + h % 60, y = 15 + (h >> 3) % 50;
  const ids = PROGRAM_PHOTOS[label]; const photo = ids ? photoUrl(ids[h % ids.length]) : null;
  return `<div class="cover" role="img" aria-label="${esc(label)}">${photo ? `<i class="cover-photo" data-img="${esc(photo)}"></i>` : ''}<svg viewBox="0 0 100 60" preserveAspectRatio="xMidYMid slice"><defs><radialGradient id="g${h}" cx="${x}%" cy="${y}%" r="85%"><stop offset="0" stop-color="${b}"/><stop offset=".55" stop-color="${a}"/><stop offset="1" stop-color="#050B1A"/></radialGradient></defs><rect width="100" height="60" fill="url(#g${h})"/>${Array.from({length: 14}, (_, i) => `<circle cx="${(h * (i + 3) * 7) % 100}" cy="${(h * (i + 5) * 3) % 60}" r="${(i % 3) * .25 + .25}" fill="#fff" opacity=".7"/>`).join('')}</svg><span>${esc(label)}</span>${sub ? `<small>${esc(sub)}</small>` : ''}</div>`;
}
export function toast(msg) { const t = $('#toast'); t.textContent = msg; t.classList.add('on'); clearTimeout(t._h); t._h = setTimeout(() => t.classList.remove('on'), 3000); }
export function sheet(html) { $('#sheet-body').innerHTML = html; $('#sheet').showModal(); }
export const closeSheet = () => $('#sheet').open && $('#sheet').close();
export function cite(e) { return `<button class="cite" data-act="passage" data-json="${esc(JSON.stringify(e))}">${ic('doc', 13)} NTRS ${esc(e.report_id)} · ${esc(e.locator)}</button>`; }
export function passage(e) {
  return `<article class="psg ${e.kind === 'hypothesis' ? 'hyp' : ''}"><div class="pm"><span class="tag k-${esc(e.kind)}">${KIND[e.kind] || esc(e.kind)}</span><span>${esc(e.locator)}</span></div>
    <blockquote>${esc(e.text)}</blockquote><div class="ps">${e.report_title ? `<a href="${R.report(e.report_id)}">${esc(e.report_title)}</a>` : ''}<a href="${ntrs(e.report_id)}" target="_blank" rel="noopener">NASA source ↗</a></div></article>`;
}
export function field(f) {
  if (f.state === 'reported' || f.state === 'needs_verification') return `<span>${esc(f.value)}</span>${f.normalized ? `<small class="norm">= ${esc(f.normalized.value)} ${esc(f.normalized.unit)} (original kept)</small>` : ''}${f.state === 'needs_verification' ? '<span class="tag warn">Needs verification</span>' : ''}${f.source ? cite({report_id: f.source.report_id, locator: f.source.locator, text: f.source.quote, kind: f.source.kind}) : ''}`;
  return `<span class="missing">${esc(f.state_label)}</span>${f.reason && f.reason !== f.state_label ? `<small>${esc(f.reason)}</small>` : ''}`;
}
export function download(name, text, type = 'text/markdown') {
  const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([text], {type})); a.download = name; document.body.append(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(a.href), 10000);
}

/* ---------- offline downloads: IndexedDB (no library), with an in-memory index for synchronous checks ---------- */
const IDB = {db: null,
  open() { return this.db ? Promise.resolve(this.db) : new Promise((res, rej) => { const r = indexedDB.open('ctrlspace', 1);
    r.onupgradeneeded = () => r.result.createObjectStore('downloads', {keyPath: 'id'}); r.onsuccess = () => { this.db = r.result; res(r.result); }; r.onerror = () => rej(r.error); }); },
  async tx(mode, fn) { const db = await this.open(); return new Promise((res, rej) => { const t = db.transaction('downloads', mode); const st = t.objectStore('downloads'); const out = fn(st); t.oncomplete = () => res(out && out.result); t.onerror = () => rej(t.error); }); },
};
const INDEX = new Map();
export const dl = {
  async init() {                                            // load index; migrate older localStorage downloads once
    try {
      for (const k of Object.keys(localStorage).filter(k => k.startsWith('cs.dl.'))) { try { await IDB.tx('readwrite', st => st.put(JSON.parse(localStorage.getItem(k)))); } catch { /* skip corrupt */ } localStorage.removeItem(k); }
      const all = await IDB.tx('readonly', st => st.getAll());
      INDEX.clear(); (all || []).forEach(r => INDEX.set(r.id, {id: r.id, title: r.title, saved_at: r.saved_at, bytes: JSON.stringify(r).length * 2}));
    } catch { /* IndexedDB unavailable (e.g. private mode): downloads disabled */ }
  },
  list: () => [...INDEX.values()].sort((a, b) => b.saved_at.localeCompare(a.saved_at)),
  has: id => INDEX.has(id), meta: id => INDEX.get(id),
  get: id => IDB.tx('readonly', st => st.get(id)),
  async save(id) {
    const [report, pages] = await Promise.all([api.report(id), api.pages(id, {limit: 100})]);
    const rec = {id, title: report.title, report, pages: pages.items, saved_at: new Date().toISOString()};
    await IDB.tx('readwrite', st => st.put(rec)); INDEX.set(id, {id, title: rec.title, saved_at: rec.saved_at, bytes: JSON.stringify(rec).length * 2}); return rec;
  },
  async remove(id) { await IDB.tx('readwrite', st => st.delete(id)); INDEX.delete(id); },
  bytes: () => [...INDEX.values()].reduce((n, r) => n + r.bytes, 0),
};

/* ---------- connectivity: internet vs. research server ---------- */
export const CONN = {online: 'Online', server_down: 'Server unreachable', offline: 'Offline'};
export async function checkServer() {
  if (!navigator.onLine) return (S.conn = 'offline');
  try { const h = await api.health(); S.conn = h.status === 'ok' ? 'online' : 'server_down'; S.ai = h.ai_provider; }
  catch { S.conn = 'server_down'; }
  S.online = S.conn === 'online'; return S.conn;
}

/* ---------- client error monitoring (first-party) ---------- */
let sent = 0;
export function reportError(kind, message, source = '') {
  if (sent >= 10 || !navigator.onLine) return; sent++;
  api.clientError({kind, message: String(message).slice(0, 500), source: String(source).slice(0, 300), route: location.pathname}).catch(() => {});
}

/* ---------- sync outbox: actions taken offline are replayed on reconnection ---------- */
const OB = 'cs.outbox';
export const outbox = {
  all: () => JSON.parse(localStorage.getItem(OB) || '[]'),
  add(op) { const a = outbox.all(); a.push({...op, at: new Date().toISOString()}); localStorage.setItem(OB, JSON.stringify(a)); },
  async flush() {
    const ops = outbox.all(); if (!ops.length) return 0; const left = []; let done = 0;
    for (const op of ops) {
      try { if (op.type === 'save') await api.save(op.kind, op.id); else if (op.type === 'note') await api.saveNote(op.id, op.text); done++; }
      catch (e) { if (e instanceof ApiError && e.code === 'network') left.push(op); else done++; }
    }
    localStorage.setItem(OB, JSON.stringify(left)); localStorage.setItem('cs.lastsync', new Date().toISOString()); return done;
  },
};
/* Run an action now, or queue it when offline. */
export async function orQueue(op, fn) {
  try { return await fn(); }
  catch (e) { if (e instanceof ApiError && e.code === 'network') { outbox.add(op); toast('Offline: saved on this device, will sync when you reconnect'); return 'queued'; } throw e; }
}

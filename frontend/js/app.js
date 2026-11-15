import {api, ApiError} from './api.js';
import {$, S, R, esc, toast, errorBox, skeleton, passageCard, saveCmp, applyTheme, KIND, download} from './ui.js';
import {vHome, vResearch, vLibrary, vReport, vAssistant, vExperiments, vExperiment, vCompare} from './views-research.js';
import {vGaps, vDemo} from './views-extra.js';
import {vWorkspace, vStudio, vLesson, vChallenges, vChallenge, vCommunity, vRoom, vPost, vProfile, vSettings, vAuth, vAdmin} from './views-platform.js';

const main = () => $('#main');
let renderSeq = 0;
const reportTab = {};
const TITLES = {home: 'Dashboard', research: 'Research Discovery', library: 'Evidence Library', report: 'Report', assistant: 'Research Assistant', experiments: 'Experiment Explorer',
  experiment: 'Experiment', compare: 'Compare Experiments', workspace: 'My Research', studio: 'Learning Studio', lesson: 'Lesson', challenges: 'Challenges', challenge: 'Challenge',
  community: 'Community', room: 'Research room', post: 'Discussion', profile: 'Profile', settings: 'Settings', admin: 'Admin', login: 'Sign in', register: 'Create account', notfound: 'Not found', gaps: 'Research gaps', demo: 'Demo mode'};
const NAV = {report: '/library', experiment: '/experiments', lesson: '/studio', challenge: '/challenges', room: '/community', post: '/community'};

/* ---------- router (History API; the server returns index.html for every non-API path) ---------- */
function route() {
  const p = decodeURIComponent(location.pathname).replace(/\/+$/, '') || '/';
  const simple = {'/': 'home', '/research': 'research', '/library': 'library', '/assistant': 'assistant', '/experiments': 'experiments', '/compare': 'compare',
    '/my-research': 'workspace', '/studio': 'studio', '/challenges': 'challenges', '/community': 'community', '/profile': 'profile', '/settings': 'settings',
    '/admin': 'admin', '/login': 'login', '/register': 'register', '/gaps': 'gaps', '/demo': 'demo'}[p];
  if (simple) return {name: simple};
  let m;
  if ((m = p.match(/^\/library\/([^/]+)$/))) return {name: 'report', id: m[1]};
  if ((m = p.match(/^\/experiments\/([^/]+)$/))) return {name: 'experiment', id: m[1]};
  if ((m = p.match(/^\/studio\/([^/]+)$/))) return {name: 'lesson', id: m[1]};
  if ((m = p.match(/^\/challenges\/([^/]+)$/))) return {name: 'challenge', id: m[1]};
  if ((m = p.match(/^\/community\/post\/(\d+)$/))) return {name: 'post', id: m[1]};
  if ((m = p.match(/^\/community\/([^/]+)$/))) return {name: 'room', id: m[1]};
  return {name: 'notfound'};
}
export function go(url, replace = false) { history[replace ? 'replaceState' : 'pushState']({}, '', url); render(true); window.scrollTo(0, 0); }
/* Soft refreshes keep anything the user typed in the meantime (and their focus), so a refresh never wipes input. */
const fieldKey = e => `${e.form?.dataset.form || ''}|${e.form?.dataset.id || ''}|${e.name || e.dataset.input || ''}`;
function snapshotFields() {
  const typed = [...main().querySelectorAll('input, textarea, select')].filter(e => e.type !== 'radio' && e.type !== 'checkbox' && (e.name || e.dataset.input) && e.value !== e.defaultValue && !(e.tagName === 'SELECT'))
    .map(e => [fieldKey(e), e.value]);
  const f = document.activeElement && main().contains(document.activeElement) ? fieldKey(document.activeElement) : null;
  return {typed, f};
}
function restoreFields({typed, f}) {
  for (const [k, v] of typed) { const e = [...main().querySelectorAll('input, textarea')].find(x => fieldKey(x) === k); if (e) e.value = v; }
  if (f) { const e = [...main().querySelectorAll('input, textarea, select')].find(x => fieldKey(x) === f); if (e) e.focus({preventScroll: true}); }
}
async function guard(seq, fn, keepY) {
  try {
    const html = await fn();
    if (seq === renderSeq) {
      const snap = keepY !== null ? snapshotFields() : null;
      main().innerHTML = `<div class="view">${html}</div>`;
      if (keepY !== null) { restoreFields(snap); window.scrollTo(0, keepY); }
    }
  }
  catch (e) { if (seq === renderSeq) main().innerHTML = `<div class="view"><div class="vh"></div>${errorBox(e)}</div>`; if (!(e instanceof ApiError)) console.error(e); }
}
/* hard = navigation (skeleton, top of page); soft = in-page update (keep content and scroll until the new view is ready) */
function render(hard = false) {
  const r = route(); const seq = ++renderSeq; const nav = NAV[r.name] || location.pathname.replace(/\/+$/, '') || '/';
  document.title = `${TITLES[r.name]} · CTRL+SPACE`;
  document.querySelectorAll('.side nav a, .tabbar a').forEach(a => a.setAttribute('aria-current', a.getAttribute('href') === nav ? 'page' : 'false'));
  document.body.classList.remove('nav-open');
  if (r.name === 'research') { const q = new URLSearchParams(location.search).get('q'); if (q !== null && q !== S.disc.q) S.disc = {...S.disc, q, sort: 'relevance', offset: 0}; }
  const sync = {assistant: vAssistant, login: () => vAuth('login'), register: () => vAuth('register'),
    notfound: () => `<header class="vh"><h2>Page not found</h2></header><p class="empty">That page doesn’t exist. <a href="${R.home}">Go to the dashboard</a>.</p>`}[r.name];
  const keepY = hard ? null : window.scrollY;
  if (sync) { main().innerHTML = `<div class="view">${sync()}</div>`; if (keepY !== null) window.scrollTo(0, keepY); return; }
  if (hard) main().innerHTML = `<div class="view"><div class="vh"></div>${skeleton()}</div>`;
  const fn = {home: vHome, research: vResearch, library: vLibrary, experiments: vExperiments, compare: vCompare, workspace: vWorkspace, studio: vStudio,
    challenges: vChallenges, community: vCommunity, gaps: vGaps, demo: vDemo, profile: vProfile, settings: vSettings, admin: vAdmin,
    report: () => vReport(r.id, reportTab[r.id] || 'evidence'), experiment: () => vExperiment(r.id), lesson: () => vLesson(r.id),
    challenge: () => vChallenge(r.id), room: () => vRoom(r.id), post: () => vPost(r.id)}[r.name];
  guard(seq, fn, keepY);
}
function renderAccount() {
  $('#acct').innerHTML = S.user ? `<a href="${R.profile}" class="who">${esc(S.user.name)}</a><button class="btn ghost sm" data-act="logout">Sign out</button>` : `<a class="btn ghost sm" href="${R.login}">Sign in</a><a class="btn fire sm" href="${R.register}">Join</a>`;
  document.querySelectorAll('[data-admin]').forEach(el => { el.hidden = !(S.user && S.user.role === 'admin'); });
}
window.addEventListener('popstate', () => render(true));
document.addEventListener('click', e => {           // in-app links use the History API
  const a = e.target.closest('a[href]');
  if (!a || e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || a.target || a.hasAttribute('download')) return;
  const url = new URL(a.href, location.href);
  if (url.origin !== location.origin || url.pathname.startsWith('/api/') || /\.[a-z0-9]+$/i.test(url.pathname)) return;
  e.preventDefault(); go(url.pathname + url.search);
});

/* ---------- actions ---------- */
async function runAsk(q) {
  q = (q || '').trim(); const err = $('#askerr');
  if (q.length < 3) { if (err) err.textContent = 'Enter at least 3 characters.'; else toast('Enter at least 3 characters.'); return; }
  if (S.busy) return;                                          // no duplicate requests
  S.busy = true; S.ask = {question: q, loading: true};
  if (location.pathname !== R.assistant) go(R.assistant); else render();
  try { S.ask = {question: q, ...(await api.ask(q))}; } catch (e) { S.ask = {question: q, error: e}; }
  S.busy = false; if (location.pathname === R.assistant) render();
}
async function pickCollection(kind, id) {
  if (!S.user) { toast('Sign in to organize research.'); go(R.login); return; }
  const cols = (await api.collections()).items;
  $('#dlg-body').innerHTML = `<h3 class="sub">Add to collection</h3>${cols.length ? cols.map(c => `<button class="btn ghost" data-act="additem" data-c="${c.id}" data-kind="${kind}" data-id="${esc(id)}">${esc(c.name)}</button> `).join('') : '<p>You have no collections yet.</p>'}
    <form class="inline" data-form="quickcol" data-kind="${kind}" data-id="${esc(id)}"><input name="name" maxlength="80" placeholder="New collection" aria-label="New collection name" required><button class="btn">Create and add</button></form>`;
  $('#dlg').showModal();
}
function askReason(title, act, id) {
  $('#dlg-body').innerHTML = `<h3 class="sub">${title}</h3><form class="form" data-form="${act}" data-id="${esc(id)}"><label>Reason<textarea name="reason" rows="3" minlength="3" maxlength="300" required></textarea></label><button class="btn">Confirm</button></form>`;
  $('#dlg').showModal();
}
function fieldErrors(f, err) {
  const fe = f.querySelector('.formerr'); if (fe) fe.textContent = err.message;
  for (const [k, m] of Object.entries(err.details || {})) { const s = f.querySelector(`[data-for="${k}"]`); if (s) { s.textContent = typeof m === 'string' && m.length > 9 ? m : 'Check this field.'; f.querySelector(`[name="${k}"]`)?.setAttribute('aria-invalid', 'true'); } }
}
function clearErrors(f) { f.querySelectorAll('.ferr').forEach(x => x.textContent = ''); f.querySelectorAll('[aria-invalid]').forEach(x => x.removeAttribute('aria-invalid')); const fe = f.querySelector('.formerr'); if (fe) fe.textContent = ''; }
const EMPTY_DISC = {q: '', category: '', material: '', year_from: '', year_to: '', evidence: '', sort: '', offset: 0};

document.addEventListener('click', async e => {
  const b = e.target.closest('[data-act]'); if (!b || b.tagName === 'INPUT' || b.tagName === 'SELECT') return;
  const d = b.dataset;
  try {
    switch (d.act) {
      case 'retry': render(); break;
      case 'menu': document.body.classList.toggle('nav-open'); break;
      case 'try': runAsk(d.q); break;
      case 'askretry': runAsk(S.ask?.question); break;
      case 'askbrief': b.disabled = true; download('ctrl-space-research-brief.md', await api.brief(S.ask.question)); toast('Research brief downloaded'); b.disabled = false; break;
      case 'cmpbrief': b.disabled = true; download('ctrl-space-research-brief.md', await api.brief(null, S.cmp)); toast('Research brief downloaded'); b.disabled = false; break;
      case 'demobrief': b.disabled = true; download('ctrl-space-research-brief.md', await api.brief('What is the oxygen margin of safety for PMMA rods?', ['bass2-smmrf', 'saffire6-3'])); toast('Research brief downloaded'); b.disabled = false; break;
      case 'democmp': S.cmp = ['bass2-smmrf', 'saffire6-3']; saveCmp(); go(R.compare); break;
      case 'gapcat': S.gapCat = d.c; render(); break;
      case 'aicheck': { b.disabled = true; const r = await api.admin.aiCheck(); S.aiCheck = r; toast(`AI provider: ${r.status}`); render(); break; }
      case 'passage': { const c = JSON.parse(d.json); $('#dlg-body').innerHTML = passageCard({...c, kind: KIND[c.kind] ? c.kind : 'context'}) + `<p class="fine">Open the NASA source to read ${esc(c.locator)} in the original document.</p>`; $('#dlg').showModal(); break; }
      case 'discpage': S.disc.offset = Math.max(0, S.disc.offset + Number(d.d) * 10); render(); break;
      case 'discclear': S.disc = {...EMPTY_DISC}; go(R.research(), true); break;
      case 'libpage': S.lib.offset = Math.max(0, S.lib.offset + Number(d.d) * 10); render(); break;
      case 'libppage': S.lib.poffset = Math.max(0, S.lib.poffset + Number(d.d) * 10); render(); break;
      case 'libtab': S.lib.tab = d.tab; render(); break;
      case 'libclear': S.lib = {...S.lib, q: '', category: '', year_from: '', year_to: '', evidence: '', offset: 0}; render(); break;
      case 'expclear': S.exp = {q: '', material: '', gravity: '', program: ''}; render(); break;
      case 'roompage': S.roomOffset = Math.max(0, (S.roomOffset || 0) + Number(d.d) * 20); render(); break;
      case 'topic': S.topic = d.t; render(); break;
      case 'rtab': reportTab[d.id] = d.tab; render(); break;
      case 'save': if (!S.user) { toast('Sign in to save research.'); go(R.login); break; } await api.save(d.kind, d.id); toast(d.kind === 'report' ? 'Report saved' : 'Experiment saved'); render(); break;
      case 'unsave': await api.unsave(d.kind, d.id); toast('Removed from saved'); render(); break;
      case 'collect': await pickCollection(d.kind, d.id); break;
      case 'additem': await api.addItem(d.c, d.kind, d.id); $('#dlg').close(); toast('Added to collection'); break;
      case 'share': if (!S.user) { toast('Sign in to share in the community.'); go(R.login); break; }
        $('#dlg-body').innerHTML = `<h3 class="sub">Share in which room?</h3>${(await api.rooms()).items.map(r => `<button class="btn ghost" data-act="shareroom" data-room="${esc(r.id)}" data-kind="${d.kind}" data-id="${esc(d.id)}">${esc(r.name)}</button> `).join('')}`;
        $('#dlg').showModal(); break;
      case 'shareroom': S.share = {kind: d.kind, id: d.id}; $('#dlg').close(); go(R.room(d.room)); break;
      case 'unshare': S.share = null; render(); break;
      case 'rmitem': await api.removeItem(d.c, d.kind, d.id); toast('Removed'); render(); break;
      case 'delcol': if (confirm(`Delete the collection “${d.name}”? This can’t be undone.`)) { await api.deleteCollection(d.c); toast('Collection deleted'); render(); } break;
      case 'export': download(`ctrl-space-${d.name.replace(/[^\w-]+/g, '-')}.md`, await api.exportCollection(d.c)); toast('Export downloaded'); break;
      case 'exportcmp': download('ctrl-space-comparison.md', await api.exportCompare(S.cmp)); toast('Comparison exported'); break;
      case 'exportme': download('ctrl-space-my-data.json', JSON.stringify(await api.exportMyData(), null, 1), 'application/json'); toast('Your data downloaded'); break;
      case 'addcmp': if (!S.cmp.includes(d.id)) { if (S.cmp.length >= 4) { toast('You can compare up to 4 experiments.'); break; } S.cmp.push(d.id); saveCmp(); } toast('Added to comparison'); render(); break;
      case 'wstab': S.wsTab = d.tab; render(); break;
      case 'delnote': if (confirm('Delete this note?')) { await (d.kind === 'report' ? api.saveNote(d.id, '') : api.saveExpNote(d.id, '')); toast('Note deleted'); render(); } break;
      case 'clearact': if (confirm('Clear your research history?')) { await api.clearActivity(); toast('History cleared'); render(); } break;
      case 'complete': await api.completeLesson(d.id); toast('Lesson completed'); render(); break;
      case 'retake': S.attempt = null; render(); break;
      case 'editpost': S.editing = Number(d.id); render(); break;
      case 'canceledit': S.editing = null; render(); break;
      case 'delpost': if (confirm('Delete this post?')) { await api.deletePost(d.id); toast('Post deleted'); render(); } break;
      case 'reportpost':
        $('#dlg-body').innerHTML = `<h3 class="sub">Report this post</h3><form class="form" data-form="reportpost" data-id="${esc(d.id)}"><label>Reason<select name="reason" required><option value="">Choose…</option><option value="spam">Spam</option><option value="harassment">Harassment</option><option value="misinformation">Scientific misinformation</option><option value="off_topic">Off topic</option><option value="other">Other</option></select></label><button class="btn">Send report</button></form>`;
        $('#dlg').showModal(); break;
      case 'theme': applyTheme(d.t); if (S.user) await api.updateProfile({prefs: {theme: d.t}}); toast('Theme updated'); render(); break;
      case 'revoke': await api.revokeSession(d.id); toast('Session signed out'); render(); break;
      case 'install': if (S.installEvt) { S.installEvt.prompt(); const c = await S.installEvt.userChoice; S.installEvt = null; toast(c.outcome === 'accepted' ? 'CTRL+SPACE installed' : 'Install cancelled'); render(); } break;
      case 'logout': navigator.serviceWorker?.controller?.postMessage('clear-data'); await api.logout(); S.user = null; renderAccount(); toast('Signed out'); go(R.home); break;
      case 'tab': S.adminTab = d.tab; render(); break;
      case 'checkntrs': b.disabled = true; S.health = await api.admin.health(true); toast(`NTRS: ${S.health.ntrs.replace('_', ' ')}`); render(); break;
      case 'reindex': { const r = await api.admin.reindex(); toast(`Search index rebuilt: ${r.indexed_passages} passages`); break; }
      case 'reprocess': { toast('Reprocessing… this respects NASA’s rate limit.'); const r = await api.admin.ingest(d.id); toast(`Reprocessed ${r.report_id}: ${r.pages} pages`); render(); break; }
      case 'flag': askReason('Flag this extraction', 'flagform', d.id); break;
      case 'verify': { const k = $(`[data-kindfor="${CSS.escape(d.id)}"]`).value; if (!k) { toast('Choose the passage type first.'); break; } await api.admin.review(d.id, 'verify', k); toast('Evidence approved'); render(); break; }
      case 'rejectp': await api.admin.review(d.id, 'reject'); toast('Passage rejected'); render(); break;
      case 'expstatus': await api.admin.experimentStatus(d.id, d.s); toast('Experiment approved and published'); render(); break;
      case 'rejectexp': askReason('Reject this experiment record', 'rejectexpform', d.id); break;
      case 'moderate': await api.admin.moderate(d.id, d.a); toast({hide: 'Post hidden', restore: 'Post restored', dismiss: 'Reports dismissed'}[d.a]); render(); break;
      case 'setrole': await api.admin.manageUser(d.id, {role: d.r}); toast('Role updated'); render(); break;
      case 'setdisabled': await api.admin.manageUser(d.id, {disabled: d.v === '1'}); toast(d.v === '1' ? 'Account disabled' : 'Account enabled'); render(); break;
    }
  } catch (err) { toast(err instanceof ApiError ? err.message : 'That action failed.'); }
});
document.addEventListener('change', async e => {
  const t = e.target;
  try {
    if (t.dataset.act === 'cmpbox') { const id = t.dataset.id; S.cmp = t.checked ? [...new Set([...S.cmp, id])].slice(0, 4) : S.cmp.filter(x => x !== id); saveCmp(); render(); }
    if (t.dataset.act === 'chartfield') { S.chart = t.value; render(); }
    if (t.dataset.act === 'history') { await api.updateProfile({prefs: {history: t.checked}}); S.prefs.history = t.checked; toast(t.checked ? 'History is on' : 'History turned off and deleted'); }
    if (t.dataset.draft) { const k = 'cs.draft.' + t.dataset.draft; const dft = JSON.parse(localStorage.getItem(k) || '{}'); dft[t.name] = Number(t.value); localStorage.setItem(k, JSON.stringify(dft)); }
    if (t.dataset.statusfor) { await api.admin.setStatus(t.dataset.statusfor, t.value); toast(`Report ${t.value}`); render(); }
  } catch (err) { toast(err instanceof ApiError ? err.message : 'That action failed.'); }
});
document.addEventListener('input', e => { if (e.target.dataset.input === 'cmpfilter') { S.cmpFilter = e.target.value; clearTimeout(S._ft); S._ft = setTimeout(() => { render(); setTimeout(() => { const i = $('[data-input=cmpfilter]'); if (i) { i.focus(); i.setSelectionRange(i.value.length, i.value.length); } }, 50); }, 250); } });
document.addEventListener('submit', async e => {
  const f = e.target.closest('form[data-form]'); if (!f) return; e.preventDefault();
  const v = Object.fromEntries(new FormData(f)); const kind = f.dataset.form; const btn = f.querySelector('button:not([type=button])');
  if (kind === 'ask') return runAsk(v.q);
  if (kind === 'homesearch') { const q = (v.q || '').trim(); if (q.length < 2) { $('#hserr').textContent = 'Enter at least 2 characters to search.'; return; } S.disc = {...EMPTY_DISC, q, sort: 'relevance'}; return go(R.research(q)); }
  if (kind === 'disc') {
    for (const k of ['year_from', 'year_to']) if (v[k] && !/^(19|20)\d\d$/.test(v[k])) { toast('Years must have 4 digits, e.g. 2015.'); return; }
    S.disc = {...v, q: (v.q || '').trim(), offset: 0}; return go(R.research(S.disc.q), true);
  }
  if (kind === 'lib') { for (const k of ['year_from', 'year_to']) if (v[k] && !/^(19|20)\d\d$/.test(v[k])) { toast('Years must have 4 digits, e.g. 2015.'); return; } S.lib = {...S.lib, ...v, q: (v.q || '').trim(), offset: 0}; return render(); }
  if (kind === 'libp') { if ((v.q || '').trim().length < 2) { toast('Type at least 2 characters.'); return; } S.lib = {...S.lib, pq: v.q.trim(), pkind: v.kind, poffset: 0}; return render(); }
  if (kind === 'expf') { S.exp = {q: (v.q || '').trim(), material: v.material, gravity: v.gravity, program: v.program}; return render(); }
  if (kind === 'delete' && !confirm('Permanently delete your account and everything in it?')) return;
  if (btn) btn.disabled = true; clearErrors(f);
  try {
    if (kind === 'login' || kind === 'register') {
      const r = kind === 'login' ? await api.login(v.email, v.password) : await api.register(v.name, v.email, v.password);
      S.user = r.user; await loadPrefs(); renderAccount(); toast(kind === 'login' ? `Signed in as ${r.user.name}` : 'Account created');
      go(r.user.role === 'admin' ? R.admin : R.home);
    }
    if (kind === 'note') { await api.saveNote(f.dataset.id, v.text || ''); toast('Note saved'); }
    if (kind === 'expnote') { await api.saveExpNote(f.dataset.id, v.text || ''); toast('Note saved'); }
    if (kind === 'newcol') { await api.createCollection(v.name || ''); toast('Collection created'); render(); }
    if (kind === 'quickcol') { const c = await api.createCollection(v.name || ''); await api.addItem(c.id, f.dataset.kind, f.dataset.id); $('#dlg').close(); toast(`Added to “${c.name}”`); }
    if (kind === 'attempt') {
      const qs = f.querySelectorAll('fieldset.q'); const answers = {};
      qs.forEach(fs => { const c = fs.querySelector('input:checked'); if (c) answers[c.name] = Number(c.value); });
      if (Object.keys(answers).length < qs.length) { toast('Answer every question first.'); return; }
      S.attempt = {id: f.dataset.id, result: await api.attempt(f.dataset.id, answers)}; localStorage.removeItem('cs.draft.' + f.dataset.id); render(true); window.scrollTo(0, 0);
    }
    if (kind === 'newpost') { await api.createPost(f.dataset.room, {title: v.title, body: v.body, ...(S.share ? {ref_kind: S.share.kind, ref_id: S.share.id} : {})}); S.share = null; toast('Discussion posted'); render(); }
    if (kind === 'editpost') { await api.editPost(f.dataset.id, v.title !== undefined ? {title: v.title, body: v.body} : {body: v.body}); S.editing = null; toast('Post updated'); render(); }
    if (kind === 'reply') { await api.reply(f.dataset.id, {body: v.body}); toast('Reply posted'); render(); }
    if (kind === 'reportpost') { if (!v.reason) { toast('Choose a reason.'); return; } await api.reportPost(f.dataset.id, v.reason); $('#dlg').close(); toast('Thanks. A moderator will review it.'); render(); }
    if (kind === 'flagform') { await api.admin.flag(f.dataset.id, v.reason || ''); $('#dlg').close(); toast('Extraction flagged and sent back to review'); render(); }
    if (kind === 'rejectexpform') { await api.admin.rejectExperiment(f.dataset.id, v.reason || ''); $('#dlg').close(); toast('Experiment rejected and unpublished'); render(); }
    if (kind === 'profile') { const p = await api.updateProfile({name: v.name}); S.user = {...S.user, name: p.user.name}; renderAccount(); toast('Profile saved'); }
    if (kind === 'password') { await api.changePassword(v.current_password, v.new_password); f.reset(); toast('Password changed. Other sessions were signed out.'); render(); }
    if (kind === 'delete') { await api.deleteAccount(v.password); S.user = null; renderAccount(); toast('Account deleted'); go(R.home); }
    if (kind === 'ingest') {
      $('#ingestout').innerHTML = '<div class="loading"><span class="orbit"></span>Contacting NASA NTRS… this respects NASA’s rate limit and can take a minute.</div>';
      try { const r = await api.admin.ingest((v.id || '').trim()); $('#ingestout').innerHTML = `<p class="note">Imported <b>${esc(r.report_id)}</b>: ${r.pages} pages, ${r.passages} passages to review. ${esc(r.message || '')}</p>`; }
      catch (err) { $('#ingestout').innerHTML = errorBox(err, false); }
    }
  } catch (err) { if (f.querySelector('.formerr')) fieldErrors(f, err); else toast(err instanceof ApiError ? err.message : 'That action failed.'); }
  finally { if (btn && document.body.contains(btn)) btn.disabled = false; }
});
$('#dlg-close').addEventListener('click', () => $('#dlg').close());

async function loadPrefs() {
  if (!S.user) return;
  try { const p = await api.myProfile(); applyTheme(p.prefs.theme || 'system'); S.prefs.history = p.prefs.history !== false; } catch { /* keep local theme */ }
}

/* ---------- Application launch: logo → configuration → backend check → public data → dashboard ---------- */
async function launch() {
  const el = $('#splash'), status = $('#splash-status');
  const minTime = new Promise(r => setTimeout(r, matchMedia('(prefers-reduced-motion: reduce)').matches ? 200 : 900));
  applyTheme(S.prefs.theme);
  status.textContent = 'Checking the research service…';
  let health = null;
  try { health = await api.health(); } catch { /* handled below */ }
  if ((!health || health.status !== 'ok') && navigator.serviceWorker?.controller) {
    status.textContent = 'Offline: opening saved research…';            // installed app with cached data
    $('#offline').hidden = false;
  } else if (!health || health.status !== 'ok') {
    status.innerHTML = 'The research service can’t be reached. You can retry, or continue and try again later. <button class="btn sm" data-act="relaunch">Retry</button> <button class="btn ghost sm" data-act="continue">Continue</button>';
    await new Promise(res => el.addEventListener('click', ev => { const a = ev.target.closest('[data-act]'); if (a?.dataset.act === 'relaunch') location.reload(); if (a?.dataset.act === 'continue') res(); }));
  } else {
    status.textContent = 'Loading research data…';
    try { S.user = (await api.me()).user; await loadPrefs(); } catch { /* views show errors */ }
  }
  await minTime;
  renderAccount(); render(true);
  el.classList.add('out'); setTimeout(() => el.remove(), 400);
}
/* ---------- installable mobile app ---------- */
if ('serviceWorker' in navigator) addEventListener('load', () => navigator.serviceWorker.register('/sw.js').catch(() => { /* app still works online */ }));
addEventListener('beforeinstallprompt', e => { e.preventDefault(); S.installEvt = e; document.body.classList.add('can-install'); });
addEventListener('appinstalled', () => { S.installEvt = null; document.body.classList.remove('can-install'); });
addEventListener('online', () => { $('#offline').hidden = true; });
addEventListener('offline', () => { $('#offline').hidden = false; });
if (matchMedia('(display-mode: standalone)').matches || navigator.standalone) document.body.classList.add('standalone');
launch();

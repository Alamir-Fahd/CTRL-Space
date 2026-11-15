import {api, ApiError, $, S, R, esc, ic, toast, sheet, closeSheet, passage, errBox, skel, download, dl, outbox, orQueue, saveCmp, checkServer, reportError, CONN} from './core.js';
import {vWelcome, vLogin, vRegister, vForgot, vReset, vHome, vResearch, filtersSheet, vReport, vNotifications} from './screens-a.js';
import {vAssistant, vHistory, vLibrary, loadMedia, vExperiments, vExperiment, vCompare, loadCompareAi} from './screens-b.js';
import {vWorkspace, vLearn, vLesson, vChallenge, vCommunity, vRoom, vPost, vUser, vProfile, vSettings, vOffline, vDemo} from './screens-c.js';
import {applyLang, setLang} from './i18n.js';
import {vSearch, vAnalysis, vCollection, vNoteEditor, vEditProfile, vAbout, vHelp, vViz} from './screens-d.js';
import {vCombustionHub, vCase, vPsi, vPsiDetail, vImpact, vJudge} from './screens-e.js';

const main = () => $('#view');
let seq = 0;
const ROUTES = [
  [/^\/app\/?$/, 'home', vHome], [/^\/app\/welcome$/, 'welcome', vWelcome], [/^\/app\/login$/, 'login', vLogin], [/^\/app\/register$/, 'register', vRegister],
  [/^\/app\/forgot$/, 'forgot', vForgot], [/^\/app\/reset$/, 'reset', vReset], [/^\/app\/research$/, 'research', vResearch], [/^\/app\/search$/, 'research', vSearch],
  [/^\/app\/report\/([^/]+)$/, 'research', id => vReport(id)], [/^\/app\/analysis$/, 'assistant', vAnalysis], [/^\/app\/assistant$/, 'assistant', vAssistant],
  [/^\/app\/assistant\/(\d+)$/, 'assistant', id => openConv(id)], [/^\/app\/history$/, 'assistant', vHistory], [/^\/app\/library$/, 'workspace', vLibrary],
  [/^\/app\/collection\/(\d+)$/, 'workspace', id => vCollection(id)], [/^\/app\/experiments$/, 'experiments', vExperiments],
  [/^\/app\/experiments\/([^/]+)$/, 'experiments', id => vExperiment(id)], [/^\/app\/compare$/, 'experiments', vCompare], [/^\/app\/viz$/, 'experiments', vViz], [/^\/app\/workspace$/, 'workspace', vWorkspace],
  [/^\/app\/note\/(report|experiment)\/([^/]+)$/, 'workspace', (k, id) => vNoteEditor(k, id)], [/^\/app\/learn$/, 'profile', vLearn],
  [/^\/app\/learn\/([^/]+)$/, 'profile', id => vLesson(id)], [/^\/app\/challenge\/([^/]+)$/, 'profile', id => vChallenge(id)], [/^\/app\/community$/, 'profile', vCommunity],
  [/^\/app\/community\/post\/(\d+)$/, 'profile', id => vPost(id)], [/^\/app\/community\/([^/]+)$/, 'profile', id => vRoom(id)], [/^\/app\/user\/(\d+)$/, 'profile', id => vUser(id)],
  [/^\/app\/profile$/, 'profile', vProfile], [/^\/app\/profile\/edit$/, 'profile', vEditProfile], [/^\/app\/settings$/, 'profile', vSettings],
  [/^\/app\/offline$/, 'profile', vOffline], [/^\/app\/notifications$/, 'home', vNotifications], [/^\/app\/demo$/, 'profile', vDemo],
  [/^\/app\/about$/, 'profile', vAbout], [/^\/app\/help$/, 'profile', vHelp],
  [/^\/app\/combustion$/, 'experiments', vCombustionHub], [/^\/app\/combustion\/case\/([^/]+)$/, 'experiments', id => vCase(id)],
  [/^\/app\/combustion\/psi$/, 'experiments', vPsi], [/^\/app\/combustion\/psi\/([^/]+)$/, 'experiments', id => vPsiDetail(id)],
  [/^\/app\/impact$/, 'profile', vImpact], [/^\/app\/judge$/, 'profile', vJudge],
];
async function openConv(id) {
  if (!S.conv || S.conv.id !== Number(id)) { const c = await api.conversation(id); S.conv = {id: c.id, title: c.title}; S.msgs = c.messages; S.scope = c.report_id ? {id: c.report_id, title: `Report ${c.report_id}`} : null; }
  return vAssistant();
}
export function go(url, replace = false) { history[replace ? 'replaceState' : 'pushState']({}, '', url); render(true); }
async function render(top = false) {
  const path = decodeURIComponent(location.pathname).replace(/\/+$/, '') || '/app';
  const hit = ROUTES.find(([re]) => re.test(path)); const my = ++seq;
  const [re, tab, fn] = hit || [null, '', () => `<div class="empty">${ic('x', 28)}<p>That screen doesn’t exist.</p><a class="btn primary" href="${R.home}">Home</a></div>`];
  document.querySelectorAll('.tabbar a').forEach(a => a.setAttribute('aria-current', a.dataset.tab === tab ? 'page' : 'false'));
  document.body.dataset.screen = tab; document.body.classList.toggle('notabs', ['welcome', 'login', 'register', 'forgot', 'reset'].some(k => path.endsWith(k) || path.includes('/reset')));
  const y = top ? 0 : scrollY; if (top) main().innerHTML = `<div class="pad">${skel(3)}</div>`;
  try {
    const args = re ? path.match(re).slice(1) : [];
    const html = await fn(...args);
    if (my !== seq) return;
    main().innerHTML = html; scrollTo(0, y); if (top) { main().classList.remove('enter'); void main().offsetWidth; main().classList.add('enter'); } after();
  } catch (e) { if (my === seq) main().innerHTML = errBox(e); if (!(e instanceof ApiError)) console.error(e); }
}
function after() {                                           // post-render hooks (CSP-safe sizing, lazy panels)
  document.querySelectorAll('[data-w]').forEach(el => { el.style.width = Math.max(1, Math.min(100, Number(el.dataset.w))) + '%'; });
  document.querySelectorAll('.cover-photo[data-img]').forEach(el => {                 // real NASA photo, honest gradient fallback if it fails or is offline
    const img = new Image(); img.onload = () => { el.style.backgroundImage = `url(${el.dataset.img})`; }; img.src = el.dataset.img;
  });
  loadMedia(); loadCompareAi();
  const rel = document.getElementById('relmedia');
  if (rel) api.media(rel.dataset.q).then(m => { rel.innerHTML = m.items.length ? m.items.slice(0, 8).map(x => `<button class="tile" data-act="media" data-json="${esc(JSON.stringify(x))}"><img src="${esc(x.thumb)}" alt="${esc(x.title)}" loading="lazy"><span>${esc(x.title)}</span></button>`).join('') : '<p class="muted pad">No NASA images found.</p>'; })
    .catch(() => { rel.innerHTML = `<div class="note-inline">${ic('offline', 16)} NASA Image Library needs an internet connection.</div>`; });
  const sl = document.getElementById('slides');
  if (sl) sl.addEventListener('scroll', () => { const i = Math.round(sl.scrollLeft / sl.clientWidth); document.querySelectorAll('.dots i').forEach((d, k) => d.classList.toggle('on', k === i)); $('#onbnext').textContent = i === 3 ? 'Get started' : 'Next'; }, {passive: true});
  const sw = document.getElementById('swipe');
  if (sw) { const cards = [...sw.querySelectorAll('.xcard')];
    const upd = () => { const c = sw.scrollLeft + sw.clientWidth / 2; let best = 0, bestD = Infinity; cards.forEach((el, k) => { const d = Math.abs(el.offsetLeft + el.offsetWidth / 2 - c); if (d < bestD) { bestD = d; best = k; } }); document.querySelectorAll('.sdots i').forEach((d, k) => d.classList.toggle('on', k === best)); };
    sw.addEventListener('scroll', upd, {passive: true}); upd(); }
  const m = $('#msgs'); if (m) m.scrollTop = m.scrollHeight;
  const ta = document.querySelector('.composer textarea'); if (ta) ta.addEventListener('input', () => { ta.style.height = 'auto'; ta.style.height = Math.min(ta.scrollHeight, 140) + 'px'; });
}
addEventListener('popstate', () => render(true));
document.addEventListener('click', e => {                    // in-app links: History API, no reloads
  const a = e.target.closest('a[href]'); if (!a || e.defaultPrevented || a.target || a.hasAttribute('download') || e.button) return;
  const u = new URL(a.href, location.href); if (u.origin !== location.origin || !u.pathname.startsWith('/app')) return;
  e.preventDefault(); if (a.dataset.act) return; go(u.pathname + u.search);
});

/* ---------- account / prefs ---------- */
const sysDark = matchMedia('(prefers-color-scheme: dark)');
function applyTheme(t) { localStorage.setItem('cs.mtheme', t); document.documentElement.dataset.theme = t === 'system' ? (sysDark.matches ? 'dark' : 'light') : t === 'light' ? 'light' : 'dark'; }
sysDark.addEventListener?.('change', () => { if (localStorage.getItem('cs.mtheme') === 'system') applyTheme('system'); });
async function loadUser() {
  try { S.user = (await api.me()).user; } catch { S.user = null; }
  if (S.user) { try { const p = await api.myProfile(); S.prefs = p.prefs; if (!localStorage.getItem('cs.mtheme')) applyTheme(p.prefs.theme === 'light' ? 'light' : 'dark'); const n = await api.notifications(); S.unread = n.unread; } catch { /* offline */ } }
  updateBadge();
}
const updateBadge = () => { const b = $('#tabbadge'); if (b) { b.textContent = S.unread || ''; b.hidden = !S.unread; } };

/* ---------- AI ---------- */
async function ask(q) {
  q = (q || '').trim(); if (q.length < 3) { toast('Ask a question of at least 3 characters.'); return; }
  if (!S.online) { toast('You’re offline. AI answers need a connection.'); return; }
  if (S.busy) return;
  S.busy = true; S.msgs.push({role: 'user', content: q});
  if (!location.pathname.startsWith('/app/assistant')) go(S.conv ? R.chat(S.conv.id) : R.assistant); else render();
  S.ctl = new AbortController();
  try {
    const r = await api.assistantAsk(q, S.conv?.id, S.scope?.id, S.ctl.signal);
    if (r.conversation_id && !S.conv) { S.conv = {id: r.conversation_id, title: q.slice(0, 80)}; history.replaceState({}, '', R.chat(r.conversation_id)); }
    S.msgs.push({role: 'assistant', content: r});
  } catch (e) { S.msgs.push({role: 'assistant', content: e.code === 'cancelled' ? {status: 'stopped', evidence: []} : {status: 'insufficient_evidence', reason: e.message, evidence: [], coverage: null, error: true}}); }
  S.busy = false; S.ctl = null; render();
}
export {ask};

/* ---------- actions ---------- */
const nextSlide = () => { const sl = $('#slides'); const i = Math.round(sl.scrollLeft / sl.clientWidth); if (i >= 3) return finishOnboarding(); sl.scrollTo({left: (i + 1) * sl.clientWidth, behavior: 'smooth'}); };
function finishOnboarding() { localStorage.setItem('cs.onboarded', '1'); if (S.user) api.updateProfile({prefs: {onboarded: true}}).catch(() => {}); go(R.home, true); }
document.addEventListener('click', async e => {
  const b = e.target.closest('[data-act]'); if (!b || ['INPUT', 'SELECT'].includes(b.tagName)) return;
  const d = b.dataset; if (b.tagName === 'A') e.preventDefault();
  try {
    switch (d.act) {
      case 'retry': render(true); break;
      case 'onbnext': nextSlide(); break;
      case 'onbskip': finishOnboarding(); break;
      case 'seg': S.tab[d.key] = d.v; render(); break;
      case 'cat': S.q.cat = d.c; render(); break;
      case 'prog': S.tab.program = d.p; render(); break;
      case 'filters': sheet(filtersSheet()); break;
      case 'rclear': S.q = {research: '', cat: '', evidence: '', sort: '', material: ''}; closeSheet(); render(); break;
      case 'save': if (!S.user) { toast('Sign in to save research.'); go(R.login); break; } if (await orQueue({type: 'save', kind: d.kind, id: d.id}, () => api.save(d.kind, d.id)) !== 'queued') toast('Saved'); render(); break;
      case 'unsave': await api.unsave(d.kind, d.id); toast('Removed from saved'); render(); break;
      case 'share': { const data = {title: d.title || document.title, url: location.href}; if (navigator.share) await navigator.share(data).catch(() => {}); else { await navigator.clipboard?.writeText(location.href); toast('Link copied'); } break; }
      case 'askreport': S.scope = {id: d.id, title: d.title}; S.conv = null; S.msgs = []; go(R.assistant); break;
      case 'unscope': S.scope = null; render(); break;
      case 'dl': b.disabled = true; await dl.save(d.id); toast('Saved for offline reading'); render(); break;
      case 'undl': await dl.remove(d.id); toast('Offline copy removed'); render(); break;
      case 'cleardl': if (confirm('Remove all downloaded reports from this device?')) { for (const x of dl.list()) await dl.remove(x.id); toast('Downloads removed'); render(); } break;
      case 'clearcache': navigator.serviceWorker?.controller?.postMessage('clear-data'); toast('Cached research data cleared'); render(); break;
      case 'sync': { const n = await outbox.flush(); toast(n ? `Synced ${n} change${n === 1 ? '' : 's'}` : 'Nothing to sync'); render(); break; }
      case 'media': { const m = JSON.parse(d.json); sheet(`<img class="sheetimg" src="${esc(m.thumb)}" alt="${esc(m.title)}"><h2 class="sh">${esc(m.title)}</h2><p>${esc(m.description || 'No description.')}</p><dl class="kv"><dt>NASA ID</dt><dd>${esc(m.nasa_id)}</dd><dt>Date</dt><dd>${esc(m.date_created || '—')}</dd><dt>Center</dt><dd>${esc(m.center || '—')}</dd><dt>Source</dt><dd>NASA Image and Video Library</dd></dl><a class="btn primary block" href="${esc(m.details_url)}" target="_blank" rel="noopener">Open on images.nasa.gov ↗</a><p class="small">Use of NASA imagery does not imply NASA endorsement.</p>`); break; }
      case 'passage': sheet(passage(JSON.parse(d.json))); break;
      case 'readall': await api.readNotifications('all'); S.unread = 0; updateBadge(); render(); break;
      case 'notif': await api.readNotifications([Number(d.id)]); S.unread = Math.max(0, S.unread - 1); updateBadge(); if (d.link) go(d.link.startsWith('/app') ? d.link : R.profile); else render(); break;
      case 'ask': ask(d.q); break;
      case 'newchat': S.conv = null; S.msgs = []; S.scope = null; go(R.assistant); break;
      case 'regen': { const q = [...S.msgs].reverse().find(m => m.role === 'user')?.content; if (q) ask(q); break; }
      case 'copyans': await navigator.clipboard?.writeText(d.text); toast('Answer copied'); break;
      case 'shareans': if (navigator.share) await navigator.share({title: 'CTRL+SPACE answer', text: d.text}).catch(() => {}); else { await navigator.clipboard?.writeText(d.text); toast('Answer copied'); } break;
      case 'feedback': if (!S.user) { toast('Sign in to send feedback.'); break; } await api.feedback(Number(d.mid), d.r); toast('Thanks for the feedback'); b.closest('.fb').innerHTML = '<small>Feedback recorded</small>'; break;
      case 'exportconv': download('ctrl-space-conversation.md', await api.exportConversation(S.conv.id)); toast('Conversation exported'); break;
      case 'exportconvid': download('ctrl-space-conversation.md', await api.exportConversation(d.id)); toast('Conversation exported'); break;
      case 'delconv': if (confirm('Delete this conversation?')) { await api.deleteConversation(d.id); if (S.conv?.id === Number(d.id)) { S.conv = null; S.msgs = []; } toast('Deleted'); render(); } break;
      case 'addcmp': if (!S.cmp.includes(d.id)) { if (S.cmp.length >= 4) { toast('Up to 4 experiments.'); break; } S.cmp.push(d.id); saveCmp(); } toast('Added to comparison'); render(); break;
      case 'exportcmp': download('ctrl-space-comparison.md', await api.exportCompare(S.cmp)); toast('Comparison exported'); break;
      case 'cmpbrief': b.disabled = true; download('ctrl-space-research-brief.md', await api.brief(null, S.cmp)); toast('Research brief downloaded'); b.disabled = false; break;
      case 'demobrief': b.disabled = true; download('ctrl-space-research-brief.md', await api.brief('What is the oxygen margin of safety for PMMA rods?', S.cmp.length >= 2 ? S.cmp : ['bass2-smmrf', 'saffire6-3'])); toast('Research brief downloaded'); b.disabled = false; break;
      case 'exportcol': download(`ctrl-space-${d.name.replace(/[^\w-]+/g, '-')}.md`, await api.exportCollection(d.id)); toast('Downloaded'); break;
      case 'delcol': if (confirm(`Delete “${d.name}”? This can’t be undone.`)) { await api.deleteCollection(d.id); toast('Deleted'); if (location.pathname.startsWith('/app/collection')) go(R.library); else render(); } break;
      case 'rmitem': await api.removeItem(d.c, d.kind, d.id); toast('Removed'); render(); break;
      case 'addtocol': { if (!S.user) { toast('Sign in first.'); go(R.login); break; } const cols = (await api.collections()).items;
        sheet(`<h2 class="sh">Add to collection</h2>${cols.map(c => `<button class="menuitem" data-act="additem" data-c="${c.id}" data-kind="${d.kind}" data-id="${esc(d.id)}">${ic('library', 18)}<span>${esc(c.name)}</span></button>`).join('') || '<p class="muted">No collections yet.</p>'}<form class="inline" data-form="quickcol" data-kind="${d.kind}" data-id="${esc(d.id)}"><input name="name" maxlength="80" placeholder="New collection" aria-label="New collection" required><button class="btn primary sm">Create</button></form>`); break; }
      case 'additem': await api.addItem(d.c, d.kind, d.id); closeSheet(); toast('Added to collection'); break;
      case 'exportme': download('ctrl-space-my-data.json', JSON.stringify(await api.exportMyData(), null, 1), 'application/json'); toast('Your data downloaded'); break;
      case 'complete': await api.completeLesson(d.id); toast('Module completed'); render(); break;
      case 'retake': S.attempt = null; render(); break;
      case 'report': sheet(`<h2 class="sh">Report post</h2><form data-form="reportpost" data-id="${esc(d.id)}">${['spam', 'harassment', 'misinformation', 'off_topic', 'other'].map(r => `<label class="opt"><input type="radio" name="reason" value="${r}" required> ${r.replace('_', ' ')}</label>`).join('')}<button class="btn primary block">Send to moderators</button></form>`); break;
      case 'delpost': if (confirm('Delete this post?')) { await api.deletePost(d.id); toast('Deleted'); render(); } break;
      case 'theme': applyTheme(d.t); if (S.user) await api.updateProfile({prefs: {theme: d.t}}); render(); break;
      case 'revoke': await api.revokeSession(d.id); toast('Session signed out'); render(); break;
      case 'togglepw': { const i = b.parentElement.querySelector('input'); i.type = i.type === 'password' ? 'text' : 'password'; b.setAttribute('aria-pressed', i.type === 'text'); b.innerHTML = ic(i.type === 'text' ? 'x' : 'search', 18); break; }
      case 'demo': if (d.a.startsWith('ask:')) ask(d.a.slice(4)); else if (d.a === 'cmp') { S.cmp = ['bass2-smmrf', 'saffire6-3']; saveCmp(); go(R.compare); } else if (d.a === 'brief') { download('ctrl-space-research-brief.md', await api.brief('What is the oxygen margin of safety for PMMA rods?', ['bass2-smmrf', 'saffire6-3'])); toast('Research brief downloaded'); } break;
      case 'logout': navigator.serviceWorker?.controller?.postMessage('clear-data'); await api.logout(); S.user = null; S.msgs = []; S.conv = null; S.unread = 0; updateBadge(); toast('Signed out'); go(R.home); break;
      case 'lang': setLang(d.l); break;
      case 'copydemo': await navigator.clipboard?.writeText(d.v); toast('Copied'); break;
      case 'exploredemo': b.disabled = true; try { const r = await api.login('demo.student@ctrlspace.local', 'Demo@12345'); S.user = r.user; await loadUser(); toast('Signed in to the demo account'); go(R.home, true); } catch (e) { b.disabled = false; toast(e instanceof ApiError ? e.message : 'Demo sign-in failed.'); } break;
      case 'stopgen': S.ctl?.abort(); break;
      case 'saveans': if (!S.user) { toast('Sign in first.'); go(R.login); break; } await api.saveAnswer(Number(d.mid)); toast('Saved to My Research'); break;
      case 'unsaveans': await api.unsaveAnswer(Number(d.mid)); toast('Removed'); render(); break;
      case 'fexplain': ask(`Explain this finding: ${d.q}`.slice(0, 400)); break;
      case 'fevidence': { const det = b.closest('.msg')?.querySelector('details.evd'); if (det) { det.open = true; det.scrollIntoView({behavior: 'smooth', block: 'start'}); } else { const qs = [...(b.closest('.msg')?.querySelectorAll('.q') || [])]; sheet(`<h2 class="sh">Evidence</h2>${qs.length ? qs.map(x => x.outerHTML).join('') : '<p class="muted">The evidence is listed above in this answer.</p>'}`); } break; }
      case 'fcompare': { const ids = (d.reports || '').split(',').filter(Boolean); const all = (await api.experiments()).items; const pick = all.filter(e => ids.includes(e.report_id)).map(e => e.id).slice(0, 4);
        S.cmp = pick; saveCmp();
        toast(pick.length >= 2 ? `Comparing ${pick.length} experiments from the cited reports` : pick.length ? 'One experiment comes from the cited reports: pick another to compare' : 'No experiments are linked to the cited reports: pick 2–4'); go(R.compare); break; }
      case 'flimits': { const x = JSON.parse(d.json); sheet(`<h2 class="sh">Limitations</h2>${x.limits ? `<p><span class="evtag gen">AI-stated</span><br>${esc(x.limits)}</p>` : ''}<h3>Evidence coverage notes</h3><ul>${x.notes.map(n => `<li>${esc(n)}</li>`).join('')}</ul>${x.missing.length ? `<p class="small">Variables in your question with no supporting passage: ${esc(x.missing.join(', '))}.</p>` : ''}`); break; }
      case 'fquestions': { const x = JSON.parse(d.json); const g = await api.gaps(); const rel = g.gaps.filter(z => z.supporting_reports.some(r => x.reports.includes(r))).slice(0, 4);
        const tmpl = [...x.missing.map(v => `What did NASA experiments report about ${v}?`), ...x.vars.map(v => `How does ${v} differ between the BASS-II and Saffire experiments?`)].slice(0, 3);
        sheet(`<h2 class="sh">Research questions</h2><p class="small">Template-generated from the evidence and the corpus gaps. These are open questions, not findings.</p>${[...tmpl, ...rel.map(z => z.potential_question)].map(q => `<button class="menuitem" data-act="ask" data-q="${esc(q)}">${ic('chat', 18)}<span>${esc(q)}</span></button>`).join('') || '<p class="muted">No open questions found for these sources.</p>'}`); break; }
      case 'sugg': { S.q.research = d.q; rememberSearch(d.q); go(`/app/search?q=${encodeURIComponent(d.q)}`); break; }
      case 'analyze': S.analysis = {kind: d.kind, id: d.id, title: d.title}; go('/app/analysis'); break;
    }
  } catch (err) { toast(err instanceof ApiError ? err.message : 'That didn’t work.'); }
});
document.addEventListener('change', async e => {
  const t = e.target, a = t.dataset.act;
  try {
    if (a === 'cmp') { S.cmp = t.checked ? [...new Set([...S.cmp, t.dataset.id])].slice(0, 4) : S.cmp.filter(x => x !== t.dataset.id); saveCmp(); render(); }
    if (a === 'history') { await api.updateProfile({prefs: {history: t.checked}}); toast(t.checked ? 'History on' : 'History off and deleted'); }
    if (a?.startsWith('n-')) { const n = {...(S.prefs.notify || {}), [a.slice(2)]: t.checked}; await api.updateProfile({prefs: {notify: n}}); S.prefs.notify = n; toast('Notification preference saved'); }
  } catch (err) { toast(err.message); }
});
const fe = (f, err) => { const x = f.querySelector('.formerr'); if (x) x.textContent = err.message; for (const [k, m] of Object.entries(err.details || {})) { const s = f.querySelector(`[data-for="${k}"]`); if (s) s.textContent = typeof m === 'string' && m.length > 9 ? m : 'Check this field.'; } };
document.addEventListener('submit', async e => {
  const f = e.target.closest('form[data-form]'); if (!f) return; e.preventDefault();
  const v = Object.fromEntries(new FormData(f)); const k = f.dataset.form; const btn = f.querySelector('button:not([type=button])');
  f.querySelectorAll('.ferr').forEach(x => x.textContent = ''); const fx = f.querySelector('.formerr'); if (fx) fx.textContent = '';
  if (k === 'chat') { f.reset(); return ask(v.q); }
  if (k === 'rsearch') { S.q.research = (v.q || '').trim(); rememberSearch(S.q.research); return go(S.q.research ? `/app/search?q=${encodeURIComponent(S.q.research)}` : R.research); }
  if (k === 'rfilters') { Object.assign(S.q, {evidence: v.evidence, material: (v.material || '').trim(), sort: v.sort}); closeSheet(); return render(); }
  if (k === 'media') { S.mediaQ = (v.q || '').trim() || S.mediaQ; return render(); }
  if (k === 'psisearch') { S.psiQ = (v.q || '').trim() || 'combustion'; return render(); }
  if (k === 'register' && v.password !== v.confirm) { const s = f.querySelector('[data-for=confirm]'); if (s) s.textContent = 'Passwords don’t match.'; return; }
  if (k === 'register' && !v.terms) { const s = f.querySelector('[data-for=terms]'); if (s) s.textContent = 'Please accept the terms to continue.'; return; }
  if (btn) btn.disabled = true;
  try {
    if (k === 'login' || k === 'register') {
      const r = k === 'login' ? await api.login(v.email, v.password) : await api.register(v.name, v.email, v.password, v.category, v.institution);
      S.user = r.user; if (k === 'register' && v.interests) await api.updateProfile({interests: v.interests.split(',').map(x => x.trim()).filter(Boolean).slice(0, 8)}).catch(() => {});
      await loadUser(); toast(k === 'login' ? `Welcome back, ${r.user.name.split(' ')[0]}` : 'Account created'); go(R.home, true);
    }
    if (k === 'forgot') { const r = await api.forgot(v.email); $('#forgotout').innerHTML = `<div class="panel good"><p>${esc(r.message)}</p><a class="btn ghost block" href="${R.login}">Back to sign in</a></div>`; f.remove(); }
    if (k === 'reset') { await api.resetPassword(new URLSearchParams(location.search).get('token') || '', v.password); toast('Password changed. Sign in.'); go(R.login, true); }
    if (k === 'note') { await orQueue({type: 'note', id: f.dataset.id, text: v.text || ''}, () => api.saveNote(f.dataset.id, v.text || '')); toast('Note saved'); }
    if (k === 'expnote') { await api.saveExpNote(f.dataset.id, v.text || ''); toast('Note saved'); }
    if (k === 'newcol') { await api.createCollection(v.name, v.description); toast('Created'); render(); }
    if (k === 'quickcol') { const c = await api.createCollection(v.name); await api.addItem(c.id, f.dataset.kind, f.dataset.id); closeSheet(); toast(`Added to “${c.name}”`); }
    if (k === 'editcol') { await api.updateCollection(f.dataset.id, {name: v.name, description: v.description}); toast('Collection updated'); render(); }
    if (k === 'attempt') { const qs = f.querySelectorAll('fieldset'); const ans = {}; qs.forEach(fs => { const c = fs.querySelector('input:checked'); if (c) ans[c.name] = Number(c.value); });
      if (Object.keys(ans).length < qs.length) { toast('Answer every question.'); return; } S.attempt = {id: f.dataset.id, result: await api.attempt(f.dataset.id, ans)}; render(true); }
    if (k === 'newpost') { await api.createPost(f.dataset.room, {title: v.title, body: v.body, ...(S.share ? {ref_kind: S.share.kind, ref_id: S.share.id} : {})}); S.share = null; toast('Posted'); render(); }
    if (k === 'reply') { await api.reply(f.dataset.id, {body: v.body}); toast('Reply posted'); render(); }
    if (k === 'reportpost') { await api.reportPost(f.dataset.id, v.reason); closeSheet(); toast('Sent to moderators'); render(); }
    if (k === 'profile' || k === 'editprofile') { const p = await api.updateProfile({name: v.name, ...(k === 'editprofile' ? {bio: v.bio || '', institution: v.institution || '', category: v.category || '', interests: (v.interests || '').split(',').map(x => x.trim()).filter(Boolean).slice(0, 8)} : {})}); S.user = {...S.user, name: p.user.name}; toast('Profile saved'); if (k === 'editprofile') go(R.profile); }
    if (k === 'password') { await api.changePassword(v.current_password, v.new_password); f.reset(); toast('Password changed'); }
    if (k === 'analysis') { S.analysis = {kind: 'question', id: null, title: v.q}; render(); }
  } catch (err) { if (f.querySelector('.formerr')) fe(f, err); else toast(err instanceof ApiError ? err.message : 'That didn’t work.'); }
  finally { if (btn && document.body.contains(btn)) btn.disabled = false; }
});
$('#sheet').addEventListener('click', e => { if (e.target.id === 'sheet' || e.target.closest('[data-close]')) closeSheet(); });

/* ---------- connectivity + sync ---------- */
function showConn() {
  const b = $('#offbar'); b.hidden = S.conn === 'online'; b.className = 'offbar' + (S.conn === 'server_down' ? ' server_down' : '');
  b.textContent = S.conn === 'server_down' ? 'Research server unreachable · showing saved research' : 'Offline · showing saved research';
}
async function refreshConn(rerender = true) {
  const before = S.conn; await checkServer(); showConn();
  if (S.conn === 'online' && before !== 'online') { const n = await outbox.flush(); if (n) toast(`Back online · synced ${n} change${n === 1 ? '' : 's'}`); }
  if (rerender && before !== S.conn) render();
}
function setOnline(on) { S.conn = on ? 'online' : 'offline'; S.online = on; showConn(); }
addEventListener('online', () => refreshConn());
addEventListener('offline', () => { setOnline(false); render(); });
setInterval(() => { if (document.visibilityState === 'visible') refreshConn(); }, 30000);
addEventListener('error', e => reportError('error', e.message, `${e.filename || ''}:${e.lineno || ''}`));
addEventListener('unhandledrejection', e => { if (!(e.reason instanceof ApiError)) reportError('unhandledrejection', e.reason?.message || String(e.reason)); });
function rememberSearch(q) { if (!q) return; const r = JSON.parse(localStorage.getItem('cs.recentq') || '[]').filter(x => x !== q); r.unshift(q); localStorage.setItem('cs.recentq', JSON.stringify(r.slice(0, 8))); }
let SUG = null;
async function suggestions() {
  if (SUG) return SUG;
  const [s, e] = await Promise.all([api.stats(), api.experiments()]);
  const mats = [...new Set(e.items.flatMap(x => (x.summary.material || '').match(/PMMA|SIBAL|Nomex|cotton|fiberglass/gi) || []))];
  return (SUG = [...s.categories.map(c => [c, 'Topic']), ...s.programs.map(p => [p, 'Program']), ...mats.map(m => [m, 'Material'])]);
}
document.addEventListener('input', async e => {
  const inp = e.target; if (!inp.dataset || !inp.dataset.suggest) return; const box = $('#sugbox'); if (!box) return;
  const q = inp.value.trim().toLowerCase(); const recent = JSON.parse(localStorage.getItem('cs.recentq') || '[]').map(x => [x, 'Recent']);
  let list = []; try { list = [...recent, ...(await suggestions())]; } catch { list = recent; }
  const hits = list.filter(([t]) => !q || t.toLowerCase().includes(q)).slice(0, 6);
  box.hidden = !hits.length || document.activeElement !== inp;
  box.innerHTML = hits.map(([t, k]) => `<button type="button" role="option" data-act="sugg" data-q="${esc(t)}">${ic(k === 'Recent' ? 'clock' : 'search', 16)} ${esc(t)} <small>${k}</small></button>`).join('');
});
document.addEventListener('focusin', e => { if (e.target.dataset?.suggest) e.target.dispatchEvent(new Event('input', {bubbles: true})); });
document.addEventListener('focusout', e => { if (e.target.dataset?.suggest) setTimeout(() => { const b = $('#sugbox'); if (b) b.hidden = true; }, 250); });
let pullY = null;
const pullable = () => /^\/app(\/(research|experiments|workspace|library|community|notifications|learn))?\/?$/.test(location.pathname);
addEventListener('touchstart', e => { pullY = scrollY === 0 && pullable() ? e.touches[0].clientY : null; }, {passive: true});
addEventListener('touchmove', e => { if (pullY !== null) $('#ptr').classList.toggle('on', e.touches[0].clientY - pullY > 70); }, {passive: true});
addEventListener('touchend', async () => { const p = $('#ptr'); if (pullY !== null && p.classList.contains('on')) { p.classList.add('spin'); await refreshConn(false); await render(); p.classList.remove('on', 'spin'); } pullY = null; });
if ('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js').catch(() => {});

/* ---------- 01 Splash: config → session → storage → backend check → onboarding or home (never traps) ---------- */
(async function boot() {
  applyTheme(localStorage.getItem('cs.mtheme') || 'dark'); applyLang();
  const st = $('#splash-status'); const warm = sessionStorage.getItem('cs.booted'); sessionStorage.setItem('cs.booted', '1');
  const minT = new Promise(r => setTimeout(r, warm || matchMedia('(prefers-reduced-motion: reduce)').matches ? 200 : 900));   // full splash only on the first launch of a session
  st.textContent = 'Checking the research service…';
  await dl.init();
  await Promise.race([checkServer(), new Promise(r => setTimeout(() => { S.conn = navigator.onLine ? 'server_down' : 'offline'; r(); }, 6000))]);
  if (S.conn === 'online') { st.textContent = 'Loading your research…'; await loadUser(); } else { st.textContent = S.conn === 'server_down' ? 'Research service unavailable · opening offline mode' : 'Offline · opening saved research'; S.online = false; }
  showConn();
  await minT;
  const first = !localStorage.getItem('cs.onboarded') && !(S.prefs && S.prefs.onboarded);
  if (first && location.pathname.replace(/\/+$/, '') === '/app') history.replaceState({}, '', R.welcome);
  render(true); $('#splash').classList.add('out'); setTimeout(() => $('#splash').remove(), 450);
})();

import {lang} from './i18n.js';
import {CONN} from './core.js';
import {api, S, R, esc, ic, head, backbar, sec, seg, empty, skel, needSignIn, cover, passage, cite, dl, ntrs, date, ago, refHref} from './core.js';

/* ---------- 02 Onboarding ---------- */
const SLIDES = [
  ['Welcome to CTRL+SPACE', 'Explore. Research. Discover. A research companion for fire in space.', 'spark'],
  ['NASA scientific discovery', 'Real NASA Technical Reports Server records on microgravity combustion, with every passage traceable to its source.', 'library'],
  ['AI-powered research', 'Ask questions and get answers built only from verified passages, with citations you can open.', 'chat'],
  ['Explore experiments', 'Compare ISS and spacecraft fire experiments side by side, with honest warnings about what differs.', 'flask'],
];
export function vWelcome() {
  return `<section class="onb"><div class="langsw"><button class="chip ${lang() === 'en' ? 'on' : ''}" data-act="lang" data-l="en" lang="en">English</button><button class="chip ${lang() === 'ar' ? 'on' : ''}" data-act="lang" data-l="ar" lang="ar">العربية</button></div><div class="slides" id="slides">${SLIDES.map(([t, d, i], k) => `<article class="slide" data-i="${k}"><div class="orb">${ic(i, 54)}</div><h1>${t}</h1><p>${d}</p></article>`).join('')}</div>
    <div class="dots">${SLIDES.map((_, k) => `<i class="${k ? '' : 'on'}"></i>`).join('')}</div>
    <div class="onb-actions"><button class="btn ghost" data-act="onbskip">Skip</button><button class="btn primary" data-act="onbnext" id="onbnext">Next</button></div></section>`;
}

/* ---------- 03 Authentication ---------- */
const field = (name, label, type = 'text', extra = '') => `<label class="fld"><span>${label}</span><span class="inwrap"><input name="${name}" type="${type}" ${extra} required>${type === 'password' ? `<button type="button" class="eye" data-act="togglepw" aria-label="Show password" aria-pressed="false">${ic('search', 18)}</button>` : ''}</span><em class="ferr" data-for="${name}"></em></label>`;
const DEMO_EMAIL = 'demo.student@ctrlspace.local', DEMO_PASSWORD = 'Demo@12345';
export function vLogin() {
  return `<section class="auth">${backbar(R.home)}<div class="brandmark">${ic('spark', 30)}</div><h1 class="t">Welcome back</h1><p class="sub">Sign in to sync your research across devices.</p>
    <form data-form="login" novalidate><p class="formerr" role="alert"></p>${field('email', 'Email', 'email', 'autocomplete="email" maxlength="254"')}${field('password', 'Password', 'password', 'autocomplete="current-password" maxlength="200"')}
    <a class="link right" href="${R.forgot}">Forgot password?</a><button class="btn primary block">Sign in</button></form>
    <p class="center sub">New here? <a href="${R.register}">Create an account</a></p>
    <section class="panel demo-cta"><h3>${ic('play', 18)} Try the demo</h3><p class="small">For judges and visitors: explore CTRL+SPACE immediately with a preconfigured student account.</p>
      <div class="demo-creds"><span>${esc(DEMO_EMAIL)}</span><button type="button" class="iconbtn sm" data-act="copydemo" data-v="${esc(DEMO_EMAIL)}" aria-label="Copy demo email">${ic('doc', 16)}</button></div>
      <div class="demo-creds"><span>${esc(DEMO_PASSWORD)}</span><button type="button" class="iconbtn sm" data-act="copydemo" data-v="${esc(DEMO_PASSWORD)}" aria-label="Copy demo password">${ic('doc', 16)}</button></div>
      <button class="btn ghost block" data-act="exploredemo">${ic('play', 16)} Explore demo</button></section></section>`;
}
export const CATEGORIES = [
  ['astronaut', 'rocket', 'Astronaut', 'For flight crew and astronaut candidates researching spacecraft fire safety.'],
  ['student', 'learn', 'Student', 'For university and school students exploring scientific research.'],
  ['researcher', 'flask', 'Researcher', 'For people conducting scientific research and studying experiments.'],
  ['educator', 'users', 'Educator / Teacher', 'For teachers and educators using research materials for learning.'],
  ['other', 'spark', 'Other', 'For visitors and users with different interests.'],
];
export function vRegister() {
  return `<section class="auth">${backbar(R.home)}<h1 class="t">Create account</h1><p class="sub">Save research, keep notes, track learning and join discussions.</p>
    <form data-form="register" novalidate><p class="formerr" role="alert"></p>${field('name', 'Name', 'text', 'autocomplete="name" maxlength="60"')}${field('email', 'Email', 'email', 'autocomplete="email" maxlength="254"')}
    ${field('password', 'Password', 'password', 'autocomplete="new-password" maxlength="200"')}<p class="hint">At least 10 characters, with a capital letter and a number.</p>${field('confirm', 'Confirm password', 'password', 'autocomplete="new-password" maxlength="200"')}
    <label class="fld"><span>I am a…</span></label>
    <div class="picker" role="radiogroup" aria-label="I am a…">${CATEGORIES.map(([v, icon, label, desc], i) => `<label class="pickrow"><input type="radio" name="category" value="${v}" ${i === 0 ? 'required' : ''}>${ic(icon, 20)}<span><b>${label}</b><small>${desc}</small></span></label>`).join('')}</div>
    <em class="ferr" data-for="category"></em>
    <label class="fld"><span>Institution or university (optional)</span><input name="institution" maxlength="120" placeholder="e.g. your school or university"></label>
    <label class="fld"><span>Research interests (optional)</span><input name="interests" maxlength="200" placeholder="e.g. flame spread, PMMA, Saffire"></label>
    <label class="check"><input type="checkbox" name="terms" value="1"> I agree that CTRL+SPACE stores my account data to provide the service, as described in <a href="/app/about">About</a>.</label><em class="ferr" data-for="terms"></em>
    <button class="btn primary block">Create account</button></form>
    <p class="center sub">Already have an account? <a href="${R.login}">Sign in</a></p></section>`;
}
export function vForgot() {
  return `<section class="auth">${backbar(R.login)}<h1 class="t">Forgot password</h1><p class="sub">CTRL+SPACE has no email service. Your request notifies an administrator, who gives you a one-time reset link valid for 1 hour.</p>
    <form data-form="forgot" novalidate><p class="formerr" role="alert"></p>${field('email', 'Email', 'email', 'autocomplete="email" maxlength="254"')}<button class="btn primary block">Request reset</button></form><div id="forgotout"></div></section>`;
}
export function vReset() {
  return `<section class="auth">${backbar(R.login)}<h1 class="t">Set a new password</h1><p class="sub">This link works once and expires after 1 hour.</p>
    <form data-form="reset" novalidate><p class="formerr" role="alert"></p>${field('password', 'New password', 'password', 'autocomplete="new-password" maxlength="200"')}<p class="hint">At least 10 characters, with a capital letter and a number.</p><button class="btn primary block">Change password</button></form></section>`;
}

/* ---------- 04 Home ---------- */
const greet = () => { const h = new Date().getHours(); return h < 5 ? 'Good night' : h < 12 ? 'Good morning' : h < 18 ? 'Good afternoon' : 'Good evening'; };
export const reportCard = (r, wide = false) => `<a class="card ${wide ? 'wide' : ''}" href="${R.report(r.id)}">${cover(r.id, r.program || 'NASA', date(r.published))}<div class="cb"><h3>${esc(r.title)}</h3><p>${r.passage_count ? `${r.passage_count} verified passages` : 'Metadata only'}${dl.has(r.id) ? ' · <b class="cyan">Offline</b>' : ''}</p></div></a>`;
const expCard = e => `<a class="card" href="${R.experiment(e.id)}">${cover(e.id + 'x', e.program, e.platform.split(',')[0])}<div class="cb"><h3>${esc(e.name)}</h3><p>${esc((e.summary.material || 'Material not extracted').slice(0, 60))}</p></div></a>`;
export const mediaTile = m => `<button class="tile" data-act="media" data-json="${esc(JSON.stringify(m))}"><img src="${esc(m.thumb)}" alt="${esc(m.title)}" loading="lazy"><span>${esc(m.title)}</span></button>`;
export async function vHome() {
  const [s, recent, exps, saved, acts] = await Promise.all([api.stats(), api.reports({sort: 'indexed', limit: 6}), api.experiments(),
    S.user ? api.saved().catch(() => ({items: []})) : null, S.user ? api.activity(4).catch(() => ({items: []})) : null]);
  const media = S.online ? api.media(S.mediaQ).catch(e => ({error: e})) : Promise.resolve({error: {code: 'network'}});
  const h = `${head(`${greet()}${S.user ? ',' : ''}`, S.user ? esc(S.user.name.split(' ')[0]) : 'Explore. Research. Discover.',
    `<div class="hacts"><span class="conn ${S.conn === 'online' ? 'on' : S.conn === 'offline' ? 'off' : 'server_down'}" role="status">${ic(S.conn === 'online' ? 'wifi' : 'offline', 16)}${CONN[S.conn]}</span>
     <a class="iconbtn" href="${R.notifications}" aria-label="Notifications">${ic('bell')}${S.unread ? `<b class="badge">${S.unread}</b>` : ''}</a><a class="avatar" href="${S.user ? R.profile : R.login}" aria-label="Profile">${S.user ? esc(S.user.name[0]).toUpperCase() : ic('user', 18)}</a></div>`)}
    <form class="searchbar" data-form="rsearch">${ic('search', 20)}<input name="q" maxlength="200" placeholder="Search NASA research…" aria-label="Search NASA research" autocomplete="off"></form>
    <div class="chips">${[[R.research, 'search', 'Discover'], [R.assistant, 'spark', 'Ask AI'], [R.experiments, 'flask', 'Experiments'], [R.compare, 'compare', 'Compare'], [R.workspace, 'bookmark', 'Saved']].map(([h, i, l]) => `<a class="chip" href="${h}">${ic(i, 16)} ${l}</a>`).join('')}</div>
    <a class="hero" href="${R.assistant}"><div class="hero-bg"></div><div class="hero-t"><span class="kicker">AI research assistant</span><h2>Ask what NASA’s fire experiments found</h2><p>Answers built only from verified passages, with citations.</p><span class="fakeinput">${ic('spark', 18)} Ask a scientific question…</span></div></a>
    <div class="stats"><div><b>${s.reports}</b><span>reports</span></div><div><b>${s.verified_passages}</b><span>passages</span></div><div><b>${s.experiments}</b><span>experiments</span></div><div><b>${s.lessons}</b><span>lessons</span></div></div>
    ${sec('NASA discoveries', [R.research, 'View all'])}<div class="rail">${recent.items.map(r => reportCard(r)).join('')}</div>
    ${sec('Experiments', [R.experiments, 'View all'])}<div class="rail">${exps.items.slice(0, 6).map(expCard).join('')}</div>
    ${sec('From the NASA Image Library', [R.library + '?tab=images', 'Browse'])}<div class="rail" id="homemedia">${skel(2)}</div>
    ${S.user && saved.items.some(i => i.kind === 'experiment') ? `${sec('Saved experiments', [R.workspace, 'My Research'])}<div class="rail">${saved.items.filter(i => i.kind === 'experiment').map(i => `<a class="chipcard" href="${R.experiment(i.id)}">${ic('flask', 16)}<span>${esc(i.title)}</span></a>`).join('')}</div>` : ''}
    ${S.user ? `${sec('Saved reports', [R.workspace, 'My Research'])}${saved.items.length ? `<div class="rail">${saved.items.filter(i => i.kind === 'report').map(i => `<a class="chipcard" href="${R.report(i.id)}">${ic('bookmark', 16)}<span>${esc(i.title)}</span></a>`).join('') || '<p class="muted pad">No saved reports yet.</p>'}</div>` : '<p class="muted pad">Tap the bookmark on any report to save it.</p>'}
      ${sec('Recent activity')}${acts.items.length ? `<ul class="list">${acts.items.map(a => `<li>${ic(a.action === 'asked' ? 'chat' : a.action === 'compared' ? 'compare' : 'doc', 18)}<span>${a.ref_id ? `<a href="${refHref(a.ref_kind, a.ref_id)}">${esc(a.label || a.ref_id)}</a>` : esc(a.label)}</span><small>${ago(a.at)}</small></li>`).join('')}</ul>` : '<p class="muted pad">Your recent research will appear here.</p>'}`
    : `<div class="cta-card"><h3>Make it yours</h3><p>Sign in to save reports, keep notes and sync your AI conversations.</p><div class="row"><a class="btn primary" href="${R.login}">Sign in</a><a class="btn ghost" href="${R.demo}">Demo mode</a></div></div>`}
    <p class="disclaimer">Independent student project. Not affiliated with or endorsed by NASA.</p>`;
  media.then(m => { const el = document.getElementById('homemedia'); if (!el) return;
    el.innerHTML = m.error ? `<div class="note-inline">${ic('offline', 16)} NASA Image Library needs an internet connection.</div>` : m.items.length ? m.items.slice(0, 8).map(mediaTile).join('') : '<p class="muted pad">No images found.</p>'; });
  return h;
}

/* ---------- 05 Research discovery ---------- */
export async function vResearch() {
  const Q = S.q; const [s, res, saved] = await Promise.all([api.stats(), api.reports({q: Q.research, category: Q.cat, evidence: Q.evidence, material: Q.material, sort: Q.sort || (Q.research ? 'relevance' : 'date'), limit: 20}), S.user ? api.saved().catch(() => ({items: []})) : {items: []}]);
  const sv = new Set(saved.items.map(i => i.kind + i.id));
  const nf = [Q.evidence, Q.material, Q.sort].filter(Boolean).length;
  return `${head('RESEARCH', 'NASA technical reports')}
    <div class="suggest"><form class="searchbar" data-form="rsearch">${ic('search', 20)}<input name="q" value="${esc(Q.research)}" placeholder="Search reports, materials, programs…" maxlength="200" aria-label="Search research" autocomplete="off" data-suggest="1" aria-controls="sugbox" aria-autocomplete="list"><button type="button" class="iconbtn sm" data-act="filters" aria-label="Filters">${ic('filter', 18)}${nf ? `<b class="badge">${nf}</b>` : ''}</button></form><div class="sugbox" id="sugbox" role="listbox" hidden></div></div>
    <div class="chips"><button class="chip ${Q.cat ? '' : 'on'}" data-act="cat" data-c="">All</button>${s.categories.map(c => `<button class="chip ${c === Q.cat ? 'on' : ''}" data-act="cat" data-c="${esc(c)}">${esc(c)}</button>`).join('')}</div>
    ${!Q.research && !Q.cat ? `${sec('Latest discoveries')}<div class="rail">${res.items.slice(0, 4).map(r => reportCard(r, true)).join('')}</div>${sec('All reports')}` : `<p class="count">${res.total} result${res.total === 1 ? '' : 's'}${Q.research ? ` for “${esc(Q.research)}”` : ''}</p>`}
    ${res.items.length ? `<div class="stack">${res.items.map(r => `<article class="rrow"><a href="${R.report(r.id)}" class="rthumb">${cover(r.id, r.program || 'NASA')}</a><div class="rbody"><a href="${R.report(r.id)}"><h3>${esc(r.title)}</h3></a>
      <p class="meta">NTRS ${esc(r.id)} · ${date(r.published)} · ${esc(r.doc_type || '')}</p><p class="meta">${r.passage_count ? `<b class="cyan">${r.passage_count} verified passages</b>` : 'Metadata only'}</p></div>
      <button class="iconbtn sm ${sv.has('report' + r.id) ? 'on' : ''}" data-act="${sv.has('report' + r.id) ? 'unsave' : 'save'}" data-kind="report" data-id="${esc(r.id)}" aria-label="Save report">${ic('bookmark', 18)}</button></article>`).join('')}</div>`
      : empty('No reports match. Try another word or clear the filters.', '<button class="btn ghost" data-act="rclear">Clear</button>')}`;
}
export function filtersSheet() {
  const Q = S.q; const o = (v, c, l) => `<option value="${v}" ${v === c ? 'selected' : ''}>${l}</option>`;
  return `<h2 class="sh">Filters</h2><form data-form="rfilters" class="fform"><label class="fld"><span>Evidence</span><select name="evidence">${o('', Q.evidence, 'Any')}${o('verified', Q.evidence, 'Has verified passages')}${o('pages', Q.evidence, 'Has extracted pages')}${o('metadata_only', Q.evidence, 'Metadata only')}</select></label>
    <label class="fld"><span>Material (from experiments)</span><input name="material" value="${esc(Q.material)}" placeholder="e.g. PMMA" maxlength="60"></label>
    <label class="fld"><span>Sort</span><select name="sort">${o('', Q.sort, 'Default')}${o('date', Q.sort, 'Newest')}${o('oldest', Q.sort, 'Oldest')}${o('title', Q.sort, 'A–Z')}</select></label>
    <div class="row"><button type="button" class="btn ghost" data-act="rclear">Reset</button><button class="btn primary">Apply</button></div></form>`;
}

/* ---------- 06 Research details ---------- */
export async function vReport(id) {
  let r, offline = false, pages = null;
  try { r = await api.report(id); } catch (e) { const d = dl.has(id) ? await dl.get(id) : null; if (!d) throw e; r = d.report; pages = d.pages; offline = true; }
  const tab = S.tab.report || 'overview'; const saved = S.user ? new Set((await api.saved().catch(() => ({items: []}))).items.map(i => i.kind + i.id)) : new Set();
  const related = offline ? {items: []} : await api.reports({category: r.categories[0] || '', limit: 6}).catch(() => ({items: []}));
  let body = '';
  if (tab === 'overview') body = `<section class="panel"><h3>Abstract</h3>${r.abstract ? `<p>${esc(r.abstract)}</p>` : '<p class="missing">Not stored in CTRL+SPACE. Read it on the NASA record.</p>'}</section>
    <section class="panel"><h3>Publication</h3><dl class="kv"><dt>Type</dt><dd>${esc(r.doc_type || '—')}</dd><dt>Number</dt><dd>${esc(r.report_number || '—')}</dd><dt>Published</dt><dd>${date(r.published)}</dd><dt>Authors</dt><dd>${esc(r.authors || 'Not captured')}</dd><dt>Center</dt><dd>${esc(r.center || '—')}</dd><dt>Keywords</dt><dd>${esc(r.keywords.join(', ') || 'Not captured')}</dd><dt>Topics</dt><dd>${esc(r.categories.join(', ') || '—')}</dd></dl></section>
    <section class="panel src"><h3>NASA source</h3><p>NASA Technical Reports Server · NTRS ${esc(r.id)}<br><small>Retrieved ${esc(r.retrieved_at)} · ${esc(r.rights || '')}</small></p><a class="btn ghost block" href="${ntrs(r.id)}" target="_blank" rel="noopener">Open on NTRS ↗</a>${r.pdf_url ? `<a class="btn ghost block" href="${esc(r.pdf_url)}" target="_blank" rel="noopener">Original PDF ↗</a>` : ''}</section>
    ${r.experiments.length ? `${sec('Experiments in this report')}<div class="chips">${r.experiments.map(e => `<a class="chip" href="${R.experiment(e.id)}">${esc(e.name)}</a>`).join('')}</div>` : ''}
    ${sec('Figures and related NASA images')}<p class="muted pad">Figures from this report are not digitized. Images below come from a NASA Image Library search for “${esc(r.program || r.keywords[0] || 'microgravity')}” and may not be from this report.</p><div class="rail" id="relmedia" data-q="${esc((r.program || r.keywords[0] || 'microgravity') + ' microgravity')}">${skel(2)}</div>
    ${related.items.filter(x => x.id !== r.id).length ? `${sec('Related research')}<div class="rail">${related.items.filter(x => x.id !== r.id).map(x => reportCard(x)).join('')}</div>` : ''}`;
  if (tab === 'citations') body = r.passages.length ? r.passages.map(p => passage({...p, report_id: r.id})).join('') : empty('No verified passages yet for this report.');
  if (tab === 'pages') { const pg = pages || (offline ? [] : (await api.pages(id, {limit: 50}).catch(() => ({items: []}))).items);
    body = pg.length ? pg.map(p => `<article class="panel"><h3>Page ${p.page_number}</h3><pre>${esc(p.text)}</pre></article>`).join('') : empty('No extracted page text. Pages appear when an administrator imports the original PDF.'); }
  return `<article class="detail">${backbar(R.research, `<button class="iconbtn" data-act="share" data-title="${esc(r.title)}" aria-label="Share">${ic('share')}</button><button class="iconbtn ${saved.has('report' + r.id) ? 'on' : ''}" data-act="${saved.has('report' + r.id) ? 'unsave' : 'save'}" data-kind="report" data-id="${esc(r.id)}" aria-label="Save">${ic('bookmark')}</button>`)}
    ${cover(r.id, r.program || 'NASA report', `${r.doc_type || ''} · ${date(r.published)}`)}
    ${offline ? `<div class="note-inline">${ic('offline', 16)} Offline copy saved ${esc((dl.meta(id)?.saved_at || '').slice(0, 10))}</div>` : ''}
    <h1 class="dt">${esc(r.title)}</h1><p class="meta">NTRS ${esc(r.id)} · ${r.passage_count} verified passages · cites by ${esc({page: 'page', section: 'section', slide: 'slide', abstract: 'abstract'}[r.loc_kind])}</p>
    <div class="row wrap"><a class="btn primary" href="${R.assistant}" data-act="askreport" data-id="${esc(r.id)}" data-title="${esc(r.title)}">${ic('spark', 18)} Ask about this report</a>
      <button class="btn ghost" data-act="${dl.has(r.id) ? 'undl' : 'dl'}" data-id="${esc(r.id)}">${ic('download', 18)} ${dl.has(r.id) ? 'Remove offline copy' : 'Download for offline'}</button>
      <button class="btn ghost" data-act="analyze" data-kind="report" data-id="${esc(r.id)}" data-title="${esc(r.title)}">${ic('spark', 18)} AI analysis</button><button class="btn ghost" data-act="addtocol" data-kind="report" data-id="${esc(r.id)}">${ic('library', 18)} Add to collection</button></div>
    ${seg('report', [['overview', 'Overview'], ['citations', `Citations (${r.passages.length})`], ['pages', 'Pages']], tab)}${body}</article>`;
}

/* ---------- 18 Notifications ---------- */
export async function vNotifications() {
  if (!S.user) return head('ALERTS', 'Notifications') + needSignIn('see notifications');
  const n = await api.notifications();
  return `${backbar(R.home, n.unread ? `<button class="btn ghost sm" data-act="readall">Mark all read</button>` : '')}${head('ALERTS', `${n.unread} unread`)}
    ${n.items.length ? `<ul class="nlist">${n.items.map(x => `<li class="${x.read_at ? '' : 'unread'}"><button data-act="notif" data-id="${x.id}" data-link="${esc(x.link || '')}"><span class="nic k-${esc(x.kind)}">${ic(x.kind === 'replies' ? 'chat' : x.kind === 'moderation' ? 'x' : 'bell', 18)}</span><span><b>${esc(x.title)}</b>${x.body ? `<small>${esc(x.body)}</small>` : ''}<em>${ago(x.created_at)}</em></span></button></li>`).join('')}</ul>` : empty('No notifications yet. You’ll hear about replies to your discussions and moderation decisions.')}
    <p class="muted pad">Notifications are created by real events only. Choose which ones you get in <a href="${R.settings}">Settings</a>.</p>`;
}

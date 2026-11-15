import {lang} from './i18n.js';
import {api, S, R, esc, ic, head, backbar, sec, seg, empty, skel, needSignIn, passage, cite, dl, outbox, date, ago, refHref, CONN} from './core.js';

/* ---------- 11 Research workspace ---------- */
export async function vWorkspace() {
  if (!S.user) return head('MY RESEARCH', 'Saved, collections, notes') + `<a class="menuitem panel" href="${R.library}">${ic('library', 20)}<span>Evidence Library<small>Documents, NASA images, downloads</small></span>${ic('chev', 16)}</a>` + needSignIn('save research, keep notes and questions');
  const t = S.tab.workspace || 'saved'; let body = '';
  const rowLink = (i, icon, title, sub) => `<li><a href="${refHref(i.kind, i.id)}">${ic(icon, 18)}<span><b>${esc(title)}</b><small>${sub}</small></span></a>`;
  if (t === 'saved') { const s = await api.saved(); const rep = s.items.filter(i => i.kind === 'report'), exp = s.items.filter(i => i.kind === 'experiment');
    body = `${sec('Saved reports')}${rep.length ? `<ul class="list big">${rep.map(i => rowLink(i, 'doc', i.title, `saved ${ago(i.saved_at)}${dl.has(i.id) ? ' · offline' : ''}`) + '</li>').join('')}</ul>` : '<p class="muted pad">No saved reports yet.</p>'}
      ${sec('Saved experiments')}${exp.length ? `<ul class="list big">${exp.map(i => rowLink(i, 'flask', i.title, `saved ${ago(i.saved_at)}`) + '</li>').join('')}</ul>` : '<p class="muted pad">No saved experiments yet.</p>'}`; }
  if (t === 'collections') { const c = await api.collections();
    body = `<form class="inline" data-form="newcol"><input name="name" maxlength="80" placeholder="New research project" aria-label="Project name" required><button class="btn primary sm" aria-label="Create">${ic('plus', 16)}</button></form>
    ${c.items.map(x => `<article class="panel"><h3><a href="/app/collection/${x.id}">${ic('library', 18)} ${esc(x.name)}</a></h3><p class="small">${x.items.length} item${x.items.length === 1 ? '' : 's'} · created ${date(x.created_at)}</p>${x.items.map(i => `<a class="chip" href="${refHref(i.kind, i.id)}">${esc(i.title.slice(0, 44))}</a>`).join('')}
      <div class="row"><button class="btn ghost sm" data-act="exportcol" data-id="${x.id}" data-name="${esc(x.name)}">${ic('export', 16)} Export</button><button class="btn ghost sm" data-act="delcol" data-id="${x.id}" data-name="${esc(x.name)}" aria-label="Delete">${ic('trash', 16)}</button></div></article>`).join('') || empty('No projects yet. Create one above.')}`; }
  if (t === 'notes') { const n = await api.researchNotes();
    body = n.items.length ? n.items.map(x => `<article class="panel"><p class="small">${x.kind === 'report' ? 'Report' : 'Experiment'} · ${ago(x.updated_at)} · <a href="/app/note/${x.kind}/${encodeURIComponent(x.id)}">Open editor</a></p><h3><a href="${refHref(x.kind, x.id)}">${esc(x.title)}</a></h3><form data-form="${x.kind === 'report' ? 'note' : 'expnote'}" data-id="${esc(x.id)}"><textarea name="text" rows="3" maxlength="5000" aria-label="Note">${esc(x.text)}</textarea><button class="btn ghost sm">Save</button></form></article>`).join('') : empty('No notes yet. Open a report and use “My notes”.'); }
  if (t === 'questions') { const c = await api.conversations(); body = c.items.length ? `<ul class="list big">${c.items.map(x => `<li><a href="${R.chat(x.id)}">${ic('chat', 18)}<span><b>${esc(x.title)}</b><small>${x.questions} question${x.questions === 1 ? '' : 's'} · ${ago(x.updated_at)}</small></span></a><button class="iconbtn sm" data-act="exportconvid" data-id="${x.id}" aria-label="Export">${ic('export', 16)}</button></li>`).join('')}</ul>` : empty('Your recent questions appear here.'); }
  if (t === 'answers') { const a = await api.savedAnswers(); body = a.items.length ? a.items.map(x => `<article class="panel"><p class="small">${esc(x.coverage || '')} · ${x.mode === 'ai' ? 'AI answer' : 'Retrieval-only (verified evidence)'} · saved ${ago(x.saved_at)}</p><h3><a href="${R.chat(x.conversation_id)}">${esc(x.question || 'Saved answer')}</a></h3>${x.answer ? `<p>${esc(x.answer)}</p>` : ''}<p class="small">Sources: ${x.sources.map(s => `NTRS ${esc(s)}`).join(', ') || '—'}</p><button class="btn ghost sm" data-act="unsaveans" data-mid="${x.message_id}">Remove</button></article>`).join('') : empty('Tap “Save to workspace” under an answer to keep it here.'); }
  if (t === 'history') { const a = await api.activity(50); body = (S.prefs.history === false ? `<p class="note-inline">History is off in Settings.</p>` : '') + (a.items.length ? `<ul class="list">${a.items.map(x => `<li>${ic(x.action === 'asked' ? 'chat' : x.action === 'compared' ? 'compare' : 'doc', 16)}<span>${x.ref_id ? `<a href="${refHref(x.ref_kind, x.ref_id)}">${esc(x.label || x.ref_id)}</a>` : esc(x.label)}</span><small>${ago(x.at)}</small></li>`).join('')}</ul>` : empty('No research history yet.')); }
  if (t === 'export') body = `<div class="stack"><button class="tilebtn" data-act="exportme">${ic('download', 22)}<span><b>All my data</b><small>JSON: projects, notes, saved items, history, progress</small></span></button>
    <button class="tilebtn" data-act="exportcmp" ${S.cmp.length < 2 ? 'disabled' : ''}>${ic('compare', 22)}<span><b>Current comparison</b><small>${S.cmp.length >= 2 ? `${S.cmp.length} experiments, Markdown with sources` : 'Select experiments in Compare first'}</small></span></button>
    <button class="tilebtn" data-act="demobrief">${ic('doc', 22)}<span><b>Research brief</b><small>Question + evidence + comparison, Markdown</small></span></button></div>`;
  return `${head('MY RESEARCH', 'Saved, collections, notes')}<a class="menuitem panel" href="${R.library}">${ic('library', 20)}<span>Evidence Library<small>Documents, NASA images, downloads</small></span>${ic('chev', 16)}</a>
    ${seg('workspace', [['saved', 'Saved'], ['collections', 'Collections'], ['notes', 'Notes'], ['questions', 'Questions'], ['answers', 'Answers'], ['history', 'History'], ['export', 'Export']], t)}${body}`;
}

/* ---------- 12 Learning studio ---------- */
export async function vLearn() {
  const t = S.tab.learn || 'modules';
  if (t === 'challenges') { const c = await api.challenges();
    return `${head('LEARN', 'Studio & challenges')}${seg('learn', [['modules', 'Modules'], ['challenges', 'Challenges']], t)}<div class="stack">${c.items.map(x => `<a class="panel link" href="${R.challenge(x.id)}"><p class="small">${esc(x.difficulty)} · ${x.questions} questions${x.status ? ` · <b>${{passed: 'Passed', attempted: 'Attempted', not_started: 'Not started'}[x.status]}</b>` : ''}</p><h3>${esc(x.title)}</h3><p class="muted">${esc(x.summary)}</p></a>`).join('')}</div>`; }
  const l = await api.lessons(); const done = l.items.filter(x => x.completed).length; const next = l.items.find(x => !x.completed);
  return `${head('LEARN', 'Studio & challenges')}${seg('learn', [['modules', 'Modules'], ['challenges', 'Challenges']], t)}
    <section class="panel prog"><div><b>${done}/${l.items.length}</b><span>modules completed</span></div><div class="meter"><i data-w="${l.items.length ? done / l.items.length * 100 : 0}"></i></div>${next ? `<a class="btn primary block" href="${R.lesson(next.id)}">${ic('play', 16)} ${done ? 'Continue' : 'Start'} guided discovery</a>` : '<p class="cyan">All modules completed.</p>'}</section>
    <div class="stack">${l.items.map((x, i) => `<a class="panel link" href="${R.lesson(x.id)}"><p class="small">Module ${i + 1} · ${esc(x.topic)} · ${x.minutes} min${x.completed ? ' · <b class="cyan">Done</b>' : ''}</p><h3>${esc(x.title)}</h3><p class="muted">${esc(x.summary)}</p></a>`).join('')}</div>`;
}
export async function vLesson(id) {
  const l = await api.lesson(id);
  return `<article class="detail">${backbar(R.learn)}${head(esc(l.topic.toUpperCase()), `${esc(l.level)} · ${l.minutes} min`)}<h1 class="dt">${esc(l.title)}</h1>
    <section class="panel"><h3>Objectives</h3><ul>${l.objectives.map(o => `<li>${esc(o)}</li>`).join('')}</ul></section>
    ${l.sections.map((s, i) => `<section class="panel"><h3>${i + 1}. ${esc(s.heading)}</h3><p><span class="tag">Explanation</span> ${esc(s.explanation)}</p><details class="evd"><summary>${ic('doc', 15)} NASA evidence (${s.evidence.length})</summary>${s.evidence.map(passage).join('')}</details></section>`).join('')}
    <div class="row wrap">${S.user ? (l.completed ? '<span class="tag good">Completed</span>' : `<button class="btn primary" data-act="complete" data-id="${esc(l.id)}">${ic('check', 16)} Mark completed</button>`) : `<a class="btn ghost" href="${R.login}">Sign in to track progress</a>`}${l.challenges.map(c => `<a class="btn ghost" href="${R.challenge(c.id)}">Challenge</a>`).join('')}</div>
    <div class="lnav">${l.prev ? `<a href="${R.lesson(l.prev.id)}">${ic('back', 16)} ${esc(l.prev.title)}</a>` : '<span></span>'}${l.next ? `<a href="${R.lesson(l.next.id)}">${esc(l.next.title)} ${ic('chev', 16)}</a>` : ''}</div></article>`;
}
export async function vChallenge(id) {
  const c = await api.challenge(id); const r = S.attempt?.id === id ? S.attempt.result : null;
  return `<article class="detail">${backbar(R.learn)}${head('CHALLENGE', esc(c.difficulty))}<h1 class="dt">${esc(c.title)}</h1><p class="muted">${esc(c.objective)}</p><p class="small">${esc(c.instructions)}</p>
    ${r ? `<div class="panel ${r.passed ? 'good' : 'bad'}"><h3>${r.passed ? 'Passed' : 'Not yet'}: ${r.score}/${r.total}</h3></div>` : ''}
    <form data-form="attempt" data-id="${esc(c.id)}">${c.questions.map((q, i) => { const res = r?.results.find(x => x.id === q.id);
      return `<fieldset class="panel q ${res ? (res.correct ? 'good' : 'bad') : ''}"><legend>${i + 1}. ${esc(q.prompt)}</legend>${q.options.map((o, j) => `<label class="opt ${res && j === res.correct_answer ? 'right' : ''}"><input type="radio" name="${esc(q.id)}" value="${j}" ${res ? 'disabled' : ''} ${res?.your_answer === j ? 'checked' : ''} required> ${esc(o)}</label>`).join('')}${res?.source ? passage(res.source) : ''}</fieldset>`; }).join('')}
      ${S.user ? (r ? '<button type="button" class="btn ghost block" data-act="retake">Try again</button>' : '<button class="btn primary block">Submit answers</button>') : `<a class="btn primary block" href="${R.login}">Sign in to submit</a>`}</form></article>`;
}

/* ---------- 13 Community ---------- */
export async function vCommunity() {
  const [rooms, recent] = await Promise.all([api.rooms(), api.communityRecent()]);
  return `${head('COMMUNITY', 'Research discussions')}<div class="rail">${rooms.items.map(r => `<a class="roomcard" href="${R.room(r.id)}"><b>${esc(r.name)}</b><small>${r.threads} discussion${r.threads === 1 ? '' : 's'}</small></a>`).join('')}</div>
    ${sec('Recent discussions')}${recent.posts.length ? `<ul class="list big">${recent.posts.map(p => `<li><a href="${R.post(p.id)}">${ic('chat', 18)}<span><b>${esc(p.title)}</b><small>${esc(p.room_name)} · ${esc(p.author)} · ${ago(p.created_at)}</small></span></a></li>`).join('')}</ul>` : empty('No discussions yet. Open a room to start one.')}
    ${sec('Shared discoveries')}${recent.shared.length ? `<div class="stack">${recent.shared.map(s => `<a class="panel link" href="${R.post(s.post_id)}"><p class="small">${esc(s.author)} in ${esc(s.room_name)}</p><h3>${esc(s.ref.title || s.ref.id)}</h3></a>`).join('')}</div>` : '<p class="muted pad">Share a report or experiment from its page.</p>'}
    <p class="muted pad">Posts are written by users: they are not NASA evidence.</p>`;
}
const post = (p, full) => `<article class="panel post ${p.status !== 'visible' ? 'dim' : ''}"><p class="small"><a href="${R.user(p.author_id)}">${esc(p.author)}</a> · ${ago(p.created_at)}${p.edited_at ? ' · edited' : ''}</p>${p.title ? `<h3>${full ? esc(p.title) : `<a href="${R.post(p.id)}">${esc(p.title)}</a>`}</h3>` : ''}<p>${esc(p.body)}</p>
  ${p.ref ? `<a class="chip" href="${refHref(p.ref.kind, p.ref.id)}">${ic(p.ref.kind === 'report' ? 'doc' : 'flask', 14)} ${esc(p.ref.title || p.ref.id)}</a>` : ''}${!full && !p.parent_id ? `<p class="small">${p.replies} repl${p.replies === 1 ? 'y' : 'ies'}</p>` : ''}
  ${S.user && p.status === 'visible' && !p.mine ? (p.reported_by_me ? '<p class="small">You reported this</p>' : `<button class="btn ghost sm" data-act="report" data-id="${p.id}">Report</button>`) : ''}${p.mine && p.status === 'visible' ? `<button class="btn ghost sm" data-act="delpost" data-id="${p.id}">Delete</button>` : ''}</article>`;
export async function vRoom(id) {
  const r = await api.roomPosts(id, {limit: 30});
  return `${backbar(R.community)}${head(esc(r.room.name.toUpperCase()), esc(r.room.description))}
    ${S.user ? `<form class="panel" data-form="newpost" data-room="${esc(id)}"><input name="title" maxlength="140" placeholder="Discussion title" aria-label="Title" required><textarea name="body" rows="3" maxlength="4000" placeholder="Share a question or discovery…" aria-label="Message" required></textarea>${S.share ? `<p class="small">Sharing ${esc(S.share.kind)} ${esc(S.share.id)}</p>` : ''}<button class="btn primary sm">Post</button></form>` : needSignIn('join the discussion')}
    ${r.items.map(p => post(p, false)).join('') || empty('No discussions yet.')}`;
}
export async function vPost(id) {
  const d = await api.post(id);
  return `${backbar(R.room(d.room.id))}${post(d.post, true)}${sec(`Replies (${d.replies.length})`)}${d.replies.map(p => post(p, true)).join('')}
    ${S.user && d.post.status === 'visible' ? `<form class="composer static" data-form="reply" data-id="${d.post.id}"><textarea name="body" rows="1" maxlength="4000" placeholder="Write a reply…" aria-label="Reply" required></textarea><button class="send" aria-label="Send">${ic('send', 20)}</button></form>` : ''}`;
}
export async function vUser(id) {
  const u = await api.userProfile(id);
  return `${backbar(R.community)}<div class="profilehead"><div class="avatar xl">${esc(u.name[0]).toUpperCase()}</div><h1>${esc(u.name)}</h1><p class="muted">${esc(u.role)} · joined ${date(u.joined)}</p></div>
    <div class="stats"><div><b>${u.contributions.discussions}</b><span>discussions</span></div><div><b>${u.contributions.replies}</b><span>replies</span></div><div><b>${u.contributions.shared_research}</b><span>shared</span></div><div><b>${u.contributions.challenges_passed}</b><span>challenges</span></div></div>
    ${sec('Recent discussions')}${u.recent_discussions.length ? `<ul class="list big">${u.recent_discussions.map(p => `<li><a href="${R.post(p.id)}">${ic('chat', 18)}<span><b>${esc(p.title)}</b><small>${ago(p.created_at)}</small></span></a></li>`).join('')}</ul>` : '<p class="muted pad">No discussions yet.</p>'}`;
}

/* ---------- 14 Profile & settings ---------- */
export async function vProfile() {
  if (!S.user) return head('PROFILE', 'Your account') + needSignIn('see your profile');
  const p = await api.myProfile(); const c = p.counts;
  const link = (h, i, t, s = '') => `<a class="menuitem" href="${h}">${ic(i, 20)}<span>${t}${s ? `<small>${s}</small>` : ''}</span>${ic('chev', 16)}</a>`;
  const catLabel = {astronaut: 'Astronaut', student: 'Student', researcher: 'Researcher', educator: 'Educator / Teacher', other: 'Other'}[p.user.category] || 'Researcher';
  return `<div class="profilehead"><div class="avatar xl">${esc(p.user.name[0]).toUpperCase()}</div><h1>${esc(p.user.name)}${p.user.is_demo ? ' <span class="tag good">Demo</span>' : ''}</h1><p class="muted">${esc(p.user.email)} · ${p.user.role === 'admin' ? 'Administrator' : esc(catLabel)}</p>${p.user.institution ? `<p class="small">${esc(p.user.institution)}</p>` : ''}${p.user.bio ? `<p class="small">${esc(p.user.bio)}</p>` : ''}${p.user.interests?.length ? `<div class="chips center">${p.user.interests.map(i => `<span class="chip">${esc(i)}</span>`).join('')}</div>` : ''}</div>
    <div class="stats"><div><b>${c.collections}</b><span>projects</span></div><div><b>${c.notes}</b><span>notes</span></div><div><b>${c.lessons_completed}</b><span>modules</span></div><div><b>${c.challenges_passed}</b><span>challenges</span></div></div>
    <nav class="menu">${link(R.workspace, 'library', 'Research workspace', 'Projects, notes, AI summaries')}${link(R.notifications, 'bell', 'Notifications', S.unread ? `${S.unread} unread` : '')}${link(R.learn, 'learn', 'Learning Studio')}${link('/app/combustion', 'flask', 'Combustion Research Hub', 'PSI data, fire safety case studies, tech transfer')}${link(R.community, 'users', 'Community')}
      ${link(R.offline, 'offline', 'Offline & storage', `${dl.list().length} downloaded`)}${link(R.settings, 'gear', 'Settings')}${link('/app/profile/edit', 'user', 'Edit profile', 'Name, bio, research interests')}${link(R.demo, 'play', 'Demo mode')}${link('/app/judge', 'spark', 'Judge mode', 'Challenge alignment, innovations, impact')}${link('/app/analysis', 'spark', 'AI research analysis')}${link('/app/help', 'learn', 'Help & support')}${link('/app/about', 'doc', 'About CTRL+SPACE')}${p.user.role === 'admin' ? `<a class="menuitem" href="/admin">${ic('user', 20)}<span>Admin dashboard<small>Opens the web console</small></span>${ic('chev', 16)}</a>` : ''}</nav>
    <button class="btn ghost block" data-act="logout">Sign out</button>`;
}
const langPanel = () => `<section class="panel"><h3>Language</h3><div class="chips"><button class="chip ${lang() === 'en' ? 'on' : ''}" data-act="lang" data-l="en" lang="en">English</button><button class="chip ${lang() === 'ar' ? 'on' : ''}" data-act="lang" data-l="ar" lang="ar">العربية</button></div><p class="small" data-i18n-skip>${lang() === 'ar' ? 'تتم ترجمة واجهة التطبيق. تبقى عناوين ناسا والمقتطفات والقيم التجريبية بالإنجليزية لأنها مقتبسة حرفياً من المصادر.' : 'Interface language. NASA titles, passages and experiment values stay in English because they are quoted verbatim from the sources.'}</p></section>`;
export async function vSettings() {
  if (!S.user) return backbar(R.profile) + head('SETTINGS', 'Preferences') + langPanel() + needSignIn('change settings');
  const [p, ss] = await Promise.all([api.myProfile(), api.sessions()]); const n = p.prefs.notify || {};
  const sw = (act, on, label, sub = '') => `<label class="switch"><span>${label}${sub ? `<small>${sub}</small>` : ''}</span><input type="checkbox" data-act="${act}" ${on ? 'checked' : ''}><i></i></label>`;
  return `${backbar(R.profile)}${head('SETTINGS', 'Account & preferences')}
    <section class="panel"><h3>Profile</h3><form data-form="profile" class="inline"><input name="name" value="${esc(p.user.name)}" maxlength="60" aria-label="Name" required><button class="btn primary sm">Save</button></form><p class="small">${esc(p.user.email)}</p></section>
    ${langPanel()}<section class="panel"><h3>Notifications</h3>${sw('n-replies', n.replies !== false, 'Replies to my discussions')}${sw('n-moderation', n.moderation !== false, 'Moderation decisions')}${sw('n-system', n.system !== false, 'System messages')}</section>
    <section class="panel"><h3>Appearance</h3><div class="chips">${[['system', 'System'], ['dark', 'Dark (space)'], ['light', 'Light']].map(([t, l]) => `<button class="chip ${(localStorage.getItem('cs.mtheme') || 'dark') === t ? 'on' : ''}" data-act="theme" data-t="${t}">${l}</button>`).join('')}</div></section>
    <section class="panel"><h3>Privacy</h3>${sw('history', p.prefs.history !== false, 'Keep research history', 'Turning off deletes existing history')}<button class="btn ghost sm" data-act="exportme">${ic('download', 16)} Download my data</button></section>
    <section class="panel"><h3>Storage</h3><a class="menuitem" href="${R.offline}">${ic('offline', 20)}<span>Offline data & downloads</span>${ic('chev', 16)}</a></section>
    <section class="panel"><h3>Sessions</h3>${ss.items.map(s => `<div class="sessrow"><span>${date(s.created_at)}${s.current ? ' · <b class="cyan">this device</b>' : ''}</span>${s.current ? '' : `<button class="btn ghost sm" data-act="revoke" data-id="${s.id}">Sign out</button>`}</div>`).join('')}</section>
    <section class="panel"><h3>Change password</h3><form data-form="password" novalidate><p class="formerr" role="alert"></p><input type="password" name="current_password" placeholder="Current password" autocomplete="current-password" aria-label="Current password" required><input type="password" name="new_password" placeholder="New password" autocomplete="new-password" aria-label="New password" required><button class="btn primary sm">Change</button></form></section>
    <button class="btn ghost block" data-act="logout">Sign out</button>`;
}

/* ---------- 15 Offline mode ---------- */
export async function vOffline() {
  const d = dl.list(), ob = outbox.all(), last = localStorage.getItem('cs.lastsync');
  let est = ''; try { const e = await navigator.storage?.estimate?.(); if (e) est = `${(e.usage / 1048576).toFixed(1)} MB used by the app on this device`; } catch { /* unsupported */ }
  return `${backbar(R.profile)}${head('OFFLINE', CONN[S.conn])}
    <section class="panel status ${S.conn === 'online' ? 'good' : 'bad'}">${ic(S.conn === 'online' ? 'wifi' : 'offline', 26)}<div><b>${CONN[S.conn]}</b><small>${S.conn === 'server_down' ? 'Internet works, but the CTRL+SPACE server does not answer.' : S.conn === 'offline' ? 'No internet connection on this device.' : 'Internet and research server are reachable.'}</small><small>${last ? `Last sync ${ago(last)}` : 'Not synced yet'} · ${ob.length} change${ob.length === 1 ? '' : 's'} waiting</small></div>${ob.length && S.online ? '<button class="btn primary sm" data-act="sync">Sync now</button>' : ''}</section>
    ${sec('Available offline')}${d.length ? `<ul class="list big">${d.map(x => `<li><a href="${'/app/report/' + encodeURIComponent(x.id)}">${ic('download', 18)}<span><b>${esc(x.title)}</b><small>Downloaded ${ago(x.saved_at)}</small></span></a><button class="iconbtn sm" data-act="undl" data-id="${esc(x.id)}" aria-label="Remove">${ic('trash', 16)}</button></li>`).join('')}</ul>` : empty('No downloaded reports. Use “Download for offline” on any report.')}
    <p class="muted pad">Reports and experiments you open are also kept by the app shell for offline reading.</p>
    ${ob.length ? `${sec('Waiting to sync')}<ul class="list">${ob.map(o => `<li>${ic('clock', 16)}<span>${o.type === 'save' ? `Save ${esc(o.kind)} ${esc(o.id)}` : `Note on ${esc(o.id)}`}</span><small>${ago(o.at)}</small></li>`).join('')}</ul>` : ''}
    ${sec('Needs internet')}<ul class="list"><li>${ic('spark', 16)}<span>AI answers (no local AI model is configured)</span></li><li>${ic('image', 16)}<span>New NASA Image Library searches</span></li><li>${ic('user', 16)}<span>Sign in, posting and notifications</span></li></ul>
    ${sec('Storage')}<section class="panel"><p>${dl.list().length} downloaded report${dl.list().length === 1 ? '' : 's'} · ${(dl.bytes() / 1024).toFixed(0)} KB${est ? `<br><small>${esc(est)}</small>` : ''}</p><div class="row"><button class="btn ghost sm" data-act="cleardl">Remove downloads</button><button class="btn ghost sm" data-act="clearcache">Clear cached data</button></div></section>`;
}

/* ---------- 20 Demo mode ---------- */
export async function vDemo() {
  const p = await api.preflight();
  const steps = [['Search BASS-II research', `${R.research}?q=BASS-II`], ['Open a NASA report', `/app/report/${p.reports[0]}`], ['Ask: oxygen margin of safety', 'ask:' + p.questions[2]], ['Compare BASS-II vs Saffire', 'cmp'], ['Generate a research brief', 'brief']];
  return `${backbar(R.profile)}${head('DEMO', 'Competition journey')}
    <section class="panel"><h3>Preflight · <span class="cov ${p.status === 'ok' ? 'good' : p.status === 'warn' ? 'part' : 'none'}">${p.status.toUpperCase()}</span></h3><p class="small">Assistant: ${p.mode === 'ai' ? 'AI answers from cited evidence' : 'retrieval-only (no AI provider configured)'}</p>
      <ul class="checks">${p.checks.map(c => `<li class="${c.status}">${ic(c.status === 'ok' ? 'check' : 'x', 14)} ${esc(c.check)}</li>`).join('')}</ul></section>
    <ol class="steps">${steps.map(([t, a], i) => `<li><span>${i + 1}</span><b>${t}</b>${a.startsWith('/') ? `<a class="btn ghost sm" href="${a}">Go</a>` : `<button class="btn ghost sm" data-act="demo" data-a="${esc(a)}">Go</button>`}</li>`).join('')}</ol>
    <p class="muted pad">Every record is real NTRS data in the local database. No answer is prerecorded.</p>`;
}

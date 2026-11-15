import {api} from './api.js';
import {S, R, esc, ntrs, date, when, KIND, header, passageCard, signInPrompt, refLink, refHref, pager, bar, opt} from './ui.js';

const ACTION = {viewed_report: 'Opened report', viewed_experiment: 'Opened experiment', asked: 'Asked', compared: 'Compared'};
const activityList = items => items.length ? `<ul class="timeline">${items.map(a => `<li><span class="mono">${when(a.at)}</span> ${ACTION[a.action] || esc(a.action)}: ${a.ref_id ? `<a href="${refHref(a.ref_kind, a.ref_id)}">${esc(a.label || a.ref_id)}</a>` : `“${esc(a.label)}”`}</li>`).join('')}</ul>` : '<p class="auth">No activity recorded.</p>';

/* ---------- Screen 09: My Research ---------- */
export async function vWorkspace() {
  if (!S.user) return header('My Research') + signInPrompt('save reports and experiments, organize collections, keep notes and export your research');
  const T = S.wsTab; let body = '';
  if (T === 'saved' || T === 'savedexp') { const kind = T === 'saved' ? 'report' : 'experiment'; const items = (await api.saved()).items.filter(i => i.kind === kind);
    body = items.length ? `<div class="scroll"><table class="dt"><thead><tr><th>${kind === 'report' ? 'Report' : 'Experiment'}</th><th>Saved</th><th>Source</th><th>Actions</th></tr></thead><tbody>${items.map(i => `<tr><td><a href="${refHref(i.kind, i.id)}">${esc(i.title)}</a></td><td>${when(i.saved_at)}</td>
      <td>${i.source_url ? `<a href="${esc(i.source_url)}" target="_blank" rel="noopener">NTRS ${esc(i.id)}</a>` : 'From verified passages'}</td><td><a class="btn ghost sm" href="${refHref(i.kind, i.id)}">Open details</a> <button class="btn ghost sm" data-act="unsave" data-kind="${i.kind}" data-id="${esc(i.id)}">Remove from saved</button></td></tr>`).join('')}</tbody></table></div>`
      : `<p class="empty">No saved ${kind}s yet. Use “Save ${kind}” on any ${kind} page.</p>`; }
  if (T === 'collections') { const res = await api.collections();
    body = `<form class="inline" data-form="newcol"><input name="name" maxlength="80" placeholder="New collection name" aria-label="New collection name" required><button class="btn">Create collection</button></form>
    <div class="colgrid">${res.items.length ? res.items.map(c => `<article class="rcard"><h3>${esc(c.name)}</h3><p class="fine">Created ${when(c.created_at)} · ${c.items.length} item${c.items.length === 1 ? '' : 's'}</p>
      ${c.items.length ? `<ul>${c.items.map(i => `<li><a href="${refHref(i.kind, i.id)}">${esc(i.title)}</a> <small>${i.kind}</small> <button class="btn ghost sm" data-act="rmitem" data-c="${c.id}" data-kind="${i.kind}" data-id="${esc(i.id)}">Remove</button></li>`).join('')}</ul>` : '<p class="auth">Empty. Use “Add to collection” on any report or experiment.</p>'}
      <div class="ractions"><button class="btn ghost sm" data-act="export" data-c="${c.id}" data-name="${esc(c.name)}">Export Markdown</button><button class="btn ghost sm" data-act="delcol" data-c="${c.id}" data-name="${esc(c.name)}">Delete</button></div></article>`).join('') : '<p class="empty">No collections yet. Create one above.</p>'}</div>`; }
  if (T === 'notes') { const n = await api.researchNotes();
    body = n.items.length ? n.items.map(x => `<article class="rcard"><div class="rtop"><span class="prog">${x.kind === 'report' ? 'Report note' : 'Experiment note'}</span><span>Updated ${when(x.updated_at)}</span></div><h3><a href="${refHref(x.kind, x.id)}">${esc(x.title)}</a></h3>
      <form class="notes" data-form="${x.kind === 'report' ? 'note' : 'expnote'}" data-id="${esc(x.id)}"><label class="sr" for="n-${esc(x.id)}">Edit note</label><textarea id="n-${esc(x.id)}" name="text" rows="3" maxlength="5000">${esc(x.text)}</textarea>
      <div class="ractions"><button class="btn ghost sm">Save</button><button type="button" class="btn ghost sm" data-act="delnote" data-kind="${x.kind}" data-id="${esc(x.id)}">Delete</button></div></form></article>`).join('')
      : '<p class="empty">No notes yet. Open any report or experiment and write in “Your research notes”.</p>'; }
  if (T === 'activity') { const a = await api.activity(50); body = (S.prefs.history ? '' : `<p class="note">History is turned off in <a href="${R.settings}">Settings</a>.</p>`) + activityList(a.items) + (a.items.length ? '<button class="btn ghost sm" data-act="clearact">Clear history</button>' : ''); }
  if (T === 'exports') { const cols = (await api.collections()).items;
    body = `<p>Exports are Markdown files that keep units, missing-value states and NTRS source references.</p>
      <div class="egrid"><article class="ecard"><h3>Experiment comparison</h3><p>${S.cmp.length >= 2 ? `${S.cmp.length} experiments selected.` : 'Select 2–4 experiments in Compare first.'}</p><button class="btn sm" data-act="exportcmp" ${S.cmp.length < 2 ? 'disabled' : ''}>Export comparison</button></article>
      <article class="ecard"><h3>Collections</h3><p>Report metadata, experiment values with sources, and your notes.</p>${cols.length ? cols.map(c => `<button class="btn ghost sm" data-act="export" data-c="${c.id}" data-name="${esc(c.name)}">${esc(c.name)}</button>`).join(' ') : '<small>No collections yet.</small>'}</article>
      <article class="ecard"><h3>All my data</h3><p>Everything stored about your account, as JSON.</p><button class="btn ghost sm" data-act="exportme">Download my data</button></article></div>`; }
  const tabs = [['saved', 'Saved reports'], ['savedexp', 'Saved experiments'], ['collections', 'Collections'], ['notes', 'Research notes'], ['activity', 'Recent activity'], ['exports', 'Research exports']];
  return header('My Research', 'Your personal research workspace. Private to your account.') +
    `<div class="tabs" role="tablist">${tabs.map(([k, l]) => `<button role="tab" aria-selected="${k === T}" data-act="wstab" data-tab="${k}">${l}</button>`).join('')}</div>${body}`;
}

/* ---------- Screen 10: Learning Studio ---------- */
export async function vStudio() {
  const res = await api.lessons(); const done = res.items.filter(l => l.completed).length;
  const topics = [...new Set(res.items.map(l => l.topic))]; const T = S.topic || '';
  const list = res.items.filter(l => !T || l.topic === T);
  return header('Learning Studio', 'Educational material on combustion and microgravity. Explanations are written by the CTRL+SPACE team and are not measurements; every NASA result they mention links to the verified passage.') +
    (S.user ? `<div class="progressline">${bar(done / res.items.length, 'meter')}<small>${done} of ${res.items.length} lessons completed</small></div>` : '') +
    `<div class="cats browse"><button class="catchip ${T ? '' : 'on'}" data-act="topic" data-t="">All topics</button>${topics.map(t => `<button class="catchip ${t === T ? 'on' : ''}" data-act="topic" data-t="${esc(t)}">${esc(t)}</button>`).join('')}</div>
    <div class="egrid">${list.map(l => `<article class="ecard"><div class="rtop"><span class="prog">${esc(l.topic)}</span><span>${esc(l.level)}</span><span>${l.minutes} min</span>${l.completed ? '<span class="tag t-finding">Completed</span>' : ''}</div>
      <h3><a class="linkish" href="${R.lesson(l.id)}">${esc(l.title)}</a></h3><p>${esc(l.summary)}</p><ul class="obj">${l.objectives.slice(0, 2).map(o => `<li>${esc(o)}</li>`).join('')}</ul></article>`).join('')}</div>`;
}
export async function vLesson(id) {
  const l = await api.lesson(id);
  return `<a class="back" href="${R.studio}">Back to Learning Studio</a><article class="rdetail lesson"><div class="rtop"><span class="prog">${esc(l.topic)}</span><span>${esc(l.level)}</span><span>${l.minutes} min</span>${l.completed ? '<span class="tag t-finding">Completed</span>' : ''}</div>
    <h2>${esc(l.title)}</h2><p class="lede2">${esc(l.summary)}</p>
    <section class="panel"><h3>Learning objectives</h3><ul>${l.objectives.map(o => `<li>${esc(o)}</li>`).join('')}</ul></section>
    ${l.sections.map((s, i) => `<section class="lsec"><h3>${i + 1}. ${esc(s.heading)}</h3><p class="explain"><span class="who">Explanation</span>${esc(s.explanation)}</p>
      <details ${i === 0 ? 'open' : ''}><summary>NASA evidence for this section (${s.evidence.length})</summary>${s.evidence.map(e => passageCard(e)).join('') || '<p class="missing">Its evidence is currently under review.</p>'}</details></section>`).join('')}
    <section class="panel"><h3>Related reports</h3><ul>${l.related_reports.map(r => `<li><a href="${R.report(r.id)}">${esc(r.title)}</a></li>`).join('')}</ul></section>
    <div class="ractions">${S.user ? (l.completed ? '<span class="tag t-finding">You completed this lesson</span>' : `<button class="btn fire" data-act="complete" data-id="${esc(l.id)}">Mark as completed</button>`) : `<a href="${R.login}">Sign in</a> to track your progress.`}
      ${l.challenges.map(c => `<a class="btn ghost" href="${R.challenge(c.id)}">Try the challenge: ${esc(c.title)}</a>`).join('')}</div>
    <nav class="lnav" aria-label="Lessons">${l.prev ? `<a href="${R.lesson(l.prev.id)}">← ${esc(l.prev.title)}</a>` : '<span></span>'}${l.next ? `<a href="${R.lesson(l.next.id)}">${esc(l.next.title)} →</a>` : ''}</nav></article>`;
}

/* ---------- Screen 11: Challenges ---------- */
const STATUS = {passed: 'Passed', attempted: 'Attempted', not_started: 'Not started'};
export async function vChallenges() {
  const res = await api.challenges();
  return header('Scientific Challenges', 'Fact-recall challenges on NASA combustion research. Each answer is checked against a quoted NASA passage, which you see after submitting. They test reading of the sources, not scientific judgement.') +
    `<div class="egrid">${res.items.map(c => { const p = c.progress;
      return `<article class="ecard"><div class="rtop"><span class="prog">${esc(c.difficulty)}</span><span>${c.questions} questions</span><span>Pass: ${c.pass_score}/${c.questions}</span>${c.status ? `<span class="tag ${c.status === 'passed' ? 't-finding' : ''}">${STATUS[c.status]}</span>` : ''}</div>
      <h3><a class="linkish" href="${R.challenge(c.id)}">${esc(c.title)}</a></h3><p>${esc(c.summary)}</p>
      ${p ? `${bar((p.best_score || 0) / c.questions, 'meter')}<small>${p.attempts ? `Best ${p.best_score}/${c.questions} after ${p.attempts} attempt${p.attempts === 1 ? '' : 's'}` : 'Not attempted yet'}</small>` : `<small><a href="${R.login}">Sign in</a> to submit attempts and track progress.</small>`}</article>`; }).join('')}</div>`;
}
export async function vChallenge(id) {
  const c = await api.challenge(id); const r = S.attempt && S.attempt.id === id ? S.attempt.result : null;
  let draft = {}; try { draft = JSON.parse(localStorage.getItem('cs.draft.' + id) || '{}'); } catch { /* ignore */ }
  const qs = c.questions.map((q, i) => { const res = r?.results.find(x => x.id === q.id);
    return `<fieldset class="q ${res ? (res.correct ? 'right' : 'wrong') : ''}"><legend>${i + 1}. ${esc(q.prompt)}</legend>${q.options.map((o, j) => `<label class="opt ${res && j === res.correct_answer ? 'correct' : ''}"><input type="radio" name="${esc(q.id)}" value="${j}" data-draft="${esc(id)}" ${res ? 'disabled' : ''} ${(res ? res.your_answer === j : draft[q.id] === j) ? 'checked' : ''} required> ${esc(o)}</label>`).join('')}
      ${res ? `<p class="verdict">${res.correct ? 'Correct.' : `Not quite. The source supports “${esc(q.options[res.correct_answer])}”.`}</p>${res.source ? passageCard(res.source) : '<p class="missing">Source passage under review.</p>'}` : ''}</fieldset>`; }).join('');
  return `<a class="back" href="${R.challenges}">Back to challenges</a><article class="rdetail"><div class="rtop"><span class="prog">${esc(c.difficulty)}</span><span>Pass mark ${c.pass_score} of ${c.questions.length}</span>${c.progress ? `<span>${c.progress.attempts} attempt${c.progress.attempts === 1 ? '' : 's'}</span>` : ''}</div><h2>${esc(c.title)}</h2>
    <dl class="meta"><dt>Objective</dt><dd>${esc(c.objective)}</dd><dt>Background</dt><dd>${esc(c.background)}${c.lesson_id ? ` <a href="${R.lesson(c.lesson_id)}">Read the related lesson</a>.` : ''}</dd><dt>Instructions</dt><dd>${esc(c.instructions)}</dd>
      <dt>Scientific sources</dt><dd>${c.related_reports.map(x => `<a href="${R.report(x.id)}">${esc(x.title)}</a>`).join('<br>')}</dd></dl>
    ${r ? `<div class="${r.passed ? 'note' : 'insuff'}"><h3>${r.passed ? 'Passed' : 'Not passed yet'}: ${r.score} / ${r.total}</h3><p>${r.passed ? 'Each answer’s source passage is shown below.' : 'Read the source passages below, then try again.'}</p></div>` : ''}
    ${S.user ? `<form data-form="attempt" data-id="${esc(c.id)}">${qs}<div class="ractions">${r ? '<button type="button" class="btn" data-act="retake">Try again</button>' : '<button class="btn fire">Submit answers</button>'}</div></form>` : `${qs}${signInPrompt('submit answers and track your progress')}`}
    ${c.history?.length ? `<h3 class="sub">Your attempts</h3><ul class="timeline">${c.history.map(h => `<li><span class="mono">${when(h.at)}</span> ${h.score}/${h.total}${h.passed ? ' — passed' : ''}</li>`).join('')}</ul>` : ''}</article>`;
}

/* ---------- Screen 12: Community ---------- */
export async function vCommunity() {
  const [rooms, recent] = await Promise.all([api.rooms(), api.communityRecent()]);
  return header('Research Community', 'Discuss NASA fire research, share reports and experiments, and collaborate. Posts are written by users: they are not NASA evidence, and moderators can hide posts that break the rules.') +
    `<h3 class="sub">Research rooms</h3><div class="egrid">${rooms.items.map(r => `<article class="ecard"><h3><a class="linkish" href="${R.room(r.id)}">${esc(r.name)}</a></h3><p>${esc(r.description)}</p><small>${r.threads} discussion${r.threads === 1 ? '' : 's'}</small></article>`).join('')}</div>
    <div class="dash"><section class="panel"><h3>Recent discussions</h3>${recent.posts.length ? `<ul class="recent">${recent.posts.map(p => `<li><a href="${R.post(p.id)}">${esc(p.title)}</a><small>${esc(p.room_name)} · ${esc(p.author)}</small></li>`).join('')}</ul>` : '<p class="auth">No discussions yet. Open a room to start one.</p>'}</section>
    <section class="panel"><h3>Shared research</h3>${recent.shared.length ? `<ul class="recent">${recent.shared.map(s => `<li>${refLink(s.ref)}<small><a href="${R.post(s.post_id)}">in ${esc(s.room_name)}</a></small></li>`).join('')}</ul>` : '<p class="auth">Nothing shared yet. Use “Share in community” on a report or experiment.</p>'}</section></div>`;
}
const postCard = (p, link = true) => {
  const editing = S.editing === p.id;
  return `<article class="rcard post ${p.status !== 'visible' ? 'muted' : ''}"><div class="rtop"><span class="prog">${esc(p.author)}</span><span>${when(p.created_at)}</span>${p.edited_at ? '<span>edited</span>' : ''}${p.parent_id ? '' : `<span>${p.replies} repl${p.replies === 1 ? 'y' : 'ies'}</span>`}</div>
  ${editing ? `<form class="form wide" data-form="editpost" data-id="${p.id}">${p.parent_id ? '' : `<label>Title<input name="title" maxlength="140" value="${esc(p.title)}" required></label>`}<label>Message<textarea name="body" rows="4" maxlength="4000" required>${esc(p.body)}</textarea></label><div class="ractions"><button class="btn">Save changes</button><button type="button" class="btn ghost" data-act="canceledit">Cancel</button></div></form>`
  : `${p.title ? `<h3>${link ? `<a class="linkish" href="${R.post(p.id)}">${esc(p.title)}</a>` : esc(p.title)}</h3>` : ''}<p class="pbody">${esc(p.body)}</p>${refLink(p.ref)}
  ${S.user && p.status === 'visible' ? `<div class="ractions">${p.mine ? `<button class="btn ghost sm" data-act="editpost" data-id="${p.id}">Edit</button><button class="btn ghost sm" data-act="delpost" data-id="${p.id}">Delete</button>` : (p.reported_by_me ? '<small>You reported this</small>' : `<button class="btn ghost sm" data-act="reportpost" data-id="${p.id}">Report</button>`)}</div>` : ''}`}</article>`;
};
export async function vRoom(id) {
  const res = await api.roomPosts(id, {limit: 20, offset: S.roomOffset || 0});
  return `<a class="back" href="${R.community}">Back to community</a>${header(esc(res.room.name), esc(res.room.description))}
    ${S.user ? `<form class="form wide" data-form="newpost" data-room="${esc(id)}"><label>Title<input name="title" maxlength="140" required></label><label>Message<textarea name="body" rows="4" maxlength="4000" required></textarea></label>${S.share ? `<p class="note">Sharing: ${esc(S.share.kind)} <span class="mono">${esc(S.share.id)}</span> <button type="button" class="btn ghost sm" data-act="unshare">Remove</button></p>` : ''}<button class="btn fire">Post discussion</button></form>` : signInPrompt('start a discussion')}
    <h3 class="sub">Discussions</h3>${res.items.length ? res.items.map(p => postCard(p)).join('') + pager('roompage', res) : '<p class="empty">No discussions yet. Start the first one.</p>'}`;
}
export async function vPost(id) {
  const d = await api.post(id);
  return `<a class="back" href="${R.room(d.room.id)}">Back to ${esc(d.room.name)}</a>${postCard(d.post, false)}
    <h3 class="sub">Replies (${d.replies.length})</h3>${d.replies.map(p => postCard(p, false)).join('') || '<p class="auth">No replies yet.</p>'}
    ${S.user && d.post.status === 'visible' ? `<form class="form wide" data-form="reply" data-id="${d.post.id}"><label>Your reply<textarea name="body" rows="3" maxlength="4000" required></textarea></label><button class="btn">Reply</button></form>` : ''}`;
}

/* ---------- Screen 13: Profile and Settings ---------- */
export async function vProfile() {
  if (!S.user) return header('Profile') + signInPrompt('see your profile');
  const [p, a, cols, saved] = await Promise.all([api.myProfile(), api.activity(10), api.collections(), api.saved()]);
  const c = p.counts;
  return header(esc(p.user.name), `${esc(p.user.email)} · ${p.user.role === 'admin' ? 'Administrator' : 'Researcher'} · joined ${date(p.user.created_at)}`) +
    `<div class="kpis"><div><b>${saved.items.length}</b><span>saved items</span></div><div><b>${c.collections}</b><span>collections</span></div><div><b>${c.notes}</b><span>report notes</span></div><div><b>${c.lessons_completed}</b><span>lessons completed</span></div><div><b>${c.challenges_passed}</b><span>challenges passed</span></div><div><b>${c.posts}</b><span>community posts</span></div></div>
    <div class="dash"><section class="panel"><h3>Saved research and collections</h3>${saved.items.slice(0, 5).map(i => `<p><a href="${refHref(i.kind, i.id)}">${esc(i.title)}</a></p>`).join('') || '<p class="auth">Nothing saved yet.</p>'}
      ${cols.items.length ? `<p class="fine">Collections: ${esc(cols.items.map(x => x.name).join(', '))}</p>` : ''}<a href="${R.workspace}">Open My Research</a></section>
    <section class="panel"><h3>Research activity</h3>${activityList(a.items)}</section></div><a class="btn ghost" href="${R.settings}">Account settings</a>`;
}
const mobilePanel = () => `<section class="panel mobileapp"><h3>Mobile app</h3>${document.body.classList.contains('standalone') ? '<p>You’re using the installed CTRL+SPACE app.</p>' : `<p>Install CTRL+SPACE on your phone’s home screen: it opens full-screen like an app and keeps reports you’ve viewed available offline.</p>
  ${S.installEvt ? '<button class="btn fire" data-act="install">Install app</button>' : '<p class="fine">Android (Chrome): menu ⋮ → <b>Install app</b>. iPhone (Safari): Share → <b>Add to Home Screen</b>.</p>'}`}</section>`;
const themeForm = () => `<div class="tabs" role="radiogroup" aria-label="Theme">${[['system', 'Match my device'], ['light', 'Light'], ['dark', 'Dark']].map(([k, l]) => `<button role="radio" aria-checked="${S.prefs.theme === k}" aria-selected="${S.prefs.theme === k}" data-act="theme" data-t="${k}">${l}</button>`).join('')}</div>`;
export async function vSettings() {
  if (!S.user) return header('Settings') + mobilePanel() + `<section class="panel"><h3>Appearance</h3>${themeForm()}</section>` + signInPrompt('change account settings');
  const [p, ss] = await Promise.all([api.myProfile(), api.sessions()]);
  return header('Settings', 'Personal information, preferences, privacy and account security.') + `
    <section class="panel"><h3>Personal information</h3><form class="form" data-form="profile"><p class="formerr" role="alert"></p><label>Name<input name="name" maxlength="60" value="${esc(p.user.name)}" required><span class="ferr" data-for="name"></span></label><label>Email<input value="${esc(p.user.email)}" disabled></label><button class="btn">Save changes</button></form></section>
    <section class="panel"><h3>Appearance</h3>${themeForm()}<p class="fine">CTRL+SPACE is available in English only. It sends no notifications, so there are no notification settings.</p></section>
    ${mobilePanel()}
    <section class="panel"><h3>Privacy</h3><label class="pick"><input type="checkbox" data-act="history" ${p.prefs.history ? 'checked' : ''}> Keep my research history (used for Recent activity). Turning it off deletes the existing history.</label>
      <div class="ractions"><button class="btn ghost sm" data-act="exportme">Download my data</button><button class="btn ghost sm" data-act="clearact">Clear history now</button></div></section>
    <section class="panel"><h3>Signed-in sessions</h3><div class="scroll"><table class="dt"><thead><tr><th>Signed in</th><th>Expires</th><th></th></tr></thead><tbody>${ss.items.map(s => `<tr><td>${when(s.created_at)}${s.current ? ' <span class="tag t-finding">This device</span>' : ''}</td><td>${when(s.expires_at)}</td><td>${s.current ? '<button class="btn ghost sm" data-act="logout">Sign out</button>' : `<button class="btn ghost sm" data-act="revoke" data-id="${esc(s.id)}">Sign out this session</button>`}</td></tr>`).join('')}</tbody></table></div></section>
    <section class="panel"><h3>Change password</h3><form class="form" data-form="password" novalidate><p class="formerr" role="alert"></p><label>Current password<input type="password" name="current_password" autocomplete="current-password" required><span class="ferr" data-for="current_password"></span></label><label>New password<input type="password" name="new_password" autocomplete="new-password" required><span class="ferr" data-for="new_password"></span><small class="fine">At least 10 characters, with a capital letter and a number. Other sessions will be signed out.</small></label><button class="btn">Change password</button></form></section>
    <section class="panel danger"><h3>Delete account</h3><p>This permanently deletes your account, saved research, collections, notes, history, progress and community posts.</p><form class="form" data-form="delete" novalidate><p class="formerr" role="alert"></p><label>Confirm with your password<input type="password" name="password" autocomplete="current-password" required><span class="ferr" data-for="password"></span></label><button class="btn danger">Delete my account</button></form></section>`;
}
export function vAuth(mode) {
  const reg = mode === 'register';
  return header(reg ? 'Create your account' : 'Sign in', reg ? 'Accounts keep your saved research, notes, progress and community posts.' : 'Welcome back.') + `
    <form class="form" data-form="${mode}" novalidate><p class="formerr" role="alert"></p>
      ${reg ? '<label>Name<input name="name" autocomplete="name" maxlength="60" required><span class="ferr" data-for="name"></span></label>' : ''}
      <label>Email<input name="email" type="email" autocomplete="email" maxlength="254" required><span class="ferr" data-for="email"></span></label>
      <label>Password<input name="password" type="password" autocomplete="${reg ? 'new-password' : 'current-password'}" maxlength="200" required><span class="ferr" data-for="password"></span>${reg ? '<small class="fine">At least 10 characters, with a capital letter and a number.</small>' : ''}</label>
      <button class="btn fire">${reg ? 'Create account' : 'Sign in'}</button>
      <p class="fine">${reg ? `Already have an account? <a href="${R.login}">Sign in</a>` : `New here? <a href="${R.register}">Create an account</a>`}</p></form>`;
}

/* ---------- Screen 14: Admin ---------- */
export async function vAdmin() {
  if (!S.user) return header('Admin Dashboard') + signInPrompt('use the admin dashboard');
  if (S.user.role !== 'admin') return header('Admin Dashboard') + `<div class="err"><h3>Permission denied</h3><p>Your account doesn’t have administrator access.</p></div>`;
  const tabs = [['overview', 'Overview'], ['reports', 'Reports'], ['ingest', 'Import and reprocess'], ['review', 'Evidence review'], ['experiments', 'Experiment review'], ['moderation', 'Moderation'], ['users', 'Users'], ['analytics', 'Analytics'], ['audit', 'Audit log']];
  const T = S.adminTab; let body = '';
  if (T === 'overview') { const [o, h] = await Promise.all([api.admin.overview(), S.health ? Promise.resolve(S.health) : api.admin.health()]);
    body = `<div class="kpis"><div><b>${o.reports.approved}</b><span>indexed reports</span></div><div><b>${o.reports.pending}</b><span>reports awaiting review</span></div><div><b>${o.passages_verified}</b><span>verified evidence passages</span></div><div><b>${o.passages_pending}</b><span>passages awaiting review</span></div><div><b>${o.experiments}</b><span>experiment records</span></div><div><b>${o.users}</b><span>users (${o.admins} admin)</span></div></div>
      <section class="panel"><h3>System health</h3><dl class="meta"><dt>Database</dt><dd>${esc(h.database)} (schema v${h.schema_version})</dd><dt>Search index</dt><dd>${h.search_index_passages} passages</dd><dt>AI provider</dt><dd>${esc(h.ai_provider)}${h.ai_provider === 'none' ? ' — the assistant returns evidence without generated answers' : ''}</dd>
      <dt>File storage</dt><dd>${h.storage_writable ? 'writable' : 'NOT writable'}</dd><dt>Pages needing OCR</dt><dd>${h.pages_needing_ocr}</dd><dt>NASA NTRS</dt><dd>${esc(h.ntrs.replace('_', ' '))}</dd></dl>
      ${S.aiCheck ? `<p class="note"><b>AI provider check:</b> ${esc(S.aiCheck.provider)} — ${esc(S.aiCheck.status)} (${S.aiCheck.latency_ms} ms). ${esc(S.aiCheck.detail)}</p>` : ''}<div class="ractions"><button class="btn ghost sm" data-act="aicheck">Check AI provider</button><button class="btn ghost sm" data-act="checkntrs">Check NTRS connection</button><button class="btn ghost sm" data-act="reindex">Rebuild search index</button></div></section>`; }
  if (T === 'reports') { const r = await api.admin.reports();
    body = `<div class="scroll"><table class="dt"><thead><tr><th>Report</th><th>Status</th><th>Extraction</th><th>Source</th><th>Action</th></tr></thead><tbody>${r.items.map(x => `<tr><td><a href="${R.report(x.id)}">${esc(x.title)}</a><small class="mono">${esc(x.id)} · ${date(x.published)}</small></td><td><span class="status ${esc(x.status)}">${esc(x.status)}</span></td><td>${x.page_count} pages · ${x.passage_count} verified · ${x.unverified_passages} pending</td>
      <td><a href="${esc(x.source_url)}" target="_blank" rel="noopener">NTRS</a>${x.pdf_url ? ` · <a href="${esc(x.pdf_url)}" target="_blank" rel="noopener">PDF</a>` : ''}</td><td><select data-statusfor="${esc(x.id)}" aria-label="Change status">${['approved', 'pending', 'rejected'].map(s => opt(s, x.status)).join('')}</select></td></tr>`).join('')}</tbody></table></div>`; }
  if (T === 'ingest') { const [log, failed] = await Promise.all([api.admin.ingestionLog(), api.admin.failedImports()]);
    body = `<p>Imports metadata and the PDF from NASA NTRS. The report starts as pending, and its extracted passages need review before they can support answers.</p>
      <form class="inline" data-form="ingest"><input name="id" inputmode="numeric" pattern="[0-9]{8,12}" placeholder="NTRS ID, e.g. 20210011385" aria-label="NTRS ID" required><button class="btn fire">Import</button></form><div id="ingestout"></div>
      <h3 class="sub">Failed records</h3>${failed.items.length ? failed.items.map(f => `<div class="review"><b class="mono">${esc(f.report_id)}</b> ${esc(f.step)}: ${esc(f.message)} <small>${when(f.at)}</small> <button class="btn sm" data-act="reprocess" data-id="${esc(f.report_id)}">Reprocess</button></div>`).join('') : '<p class="auth">No failed imports.</p>'}
      <h3 class="sub">Recent ingestion steps</h3>${log.items.map(l => `<p class="fine"><span class="mono">${when(l.at)}</span> ${esc(l.report_id)} ${esc(l.step)}: <b>${esc(l.status)}</b> ${esc(l.message)}</p>`).join('') || '<p class="fine">No imports yet.</p>'}`; }
  if (T === 'review') { const p = await api.admin.passages({limit: 20});
    body = `<p>Verify each passage against the original page. To flag a passage that is already verified, use “Flag extraction” on its report page or in the Evidence Library.</p>` + (p.items.length ? p.items.map(x => `<div class="review"><div class="pmeta"><span class="mono">${esc(x.report_id)}</span><span>Page reference: ${esc(x.locator)}</span><a href="${ntrs(x.report_id)}" target="_blank" rel="noopener">Open source</a></div>${x.flag_reason ? `<p class="warn">Flagged: ${esc(x.flag_reason)}</p>` : ''}<blockquote>${esc(x.text)}</blockquote>
      <div class="ractions"><select data-kindfor="${esc(x.id)}" aria-label="Passage type"><option value="">Passage type…</option>${['finding', 'method', 'condition', 'hypothesis', 'context'].map(k => `<option value="${k}" ${x.kind === k ? 'selected' : ''}>${KIND[k]}</option>`).join('')}</select>
      <button class="btn sm" data-act="verify" data-id="${esc(x.id)}">Approve evidence</button><button class="btn ghost sm" data-act="rejectp" data-id="${esc(x.id)}">Reject</button></div></div>`).join('') : '<p class="empty">No evidence awaiting review.</p>'); }
  if (T === 'experiments') { const e = await api.admin.experiments();
    body = `<p>An experiment can be approved only when every reported value cites a verified passage from an approved report. Check units and missing-value states on the record before approving.</p><div class="scroll"><table class="dt"><thead><tr><th>Experiment</th><th>Status</th><th>Fields</th><th>Evidence check</th><th>Action</th></tr></thead><tbody>${e.items.map(x => `<tr><td><a href="${R.experiment(x.id)}">${esc(x.name)}</a><small>${esc(x.program)}</small></td><td><span class="status ${x.status === 'published' ? 'approved' : 'pending'}">${esc(x.status)}</span></td><td>${x.reported_fields}/${x.total_fields} reported</td>
      <td>${x.blocking_fields.length ? `<span class="warn">Unverified: ${esc(x.blocking_fields.join(', '))}</span>` : 'All reported values verified'}</td>
      <td>${x.status === 'published' ? `<button class="btn ghost sm" data-act="rejectexp" data-id="${esc(x.id)}">Reject</button>` : `<button class="btn sm" data-act="expstatus" data-id="${esc(x.id)}" data-s="published" ${x.blocking_fields.length ? 'disabled' : ''}>Approve and publish</button>`}</td></tr>`).join('')}</tbody></table></div>`; }
  if (T === 'moderation') { const m = await api.admin.moderation();
    body = m.items.length ? m.items.map(p => `<div class="review"><div class="pmeta"><span>${esc(p.author)}</span><span>${p.reports} report${p.reports === 1 ? '' : 's'}: ${esc(p.reasons)}</span><span class="status ${p.status === 'visible' ? 'approved' : 'rejected'}">${esc(p.status)}</span><a href="${R.post(p.parent_id || p.id)}">Open thread</a></div>${p.title ? `<h4>${esc(p.title)}</h4>` : ''}<blockquote>${esc(p.body)}</blockquote>
      <div class="ractions">${p.status === 'visible' ? `<button class="btn sm" data-act="moderate" data-id="${p.id}" data-a="hide">Hide post</button>` : `<button class="btn sm" data-act="moderate" data-id="${p.id}" data-a="restore">Restore</button>`}<button class="btn ghost sm" data-act="moderate" data-id="${p.id}" data-a="dismiss">Dismiss reports</button></div></div>`).join('') : '<p class="empty">No reported posts.</p>'; }
  if (T === 'users') { const u = await api.admin.users();
    body = `<div class="scroll"><table class="dt"><thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Status</th><th>Joined</th><th>Actions</th></tr></thead><tbody>${u.items.map(x => { const me = x.id === S.user.id;
      return `<tr><td>${esc(x.name)}${me ? ' <small>(you)</small>' : ''}</td><td>${esc(x.email)}</td><td>${esc(x.role)}</td><td>${x.disabled ? '<span class="status rejected">disabled</span>' : '<span class="status approved">active</span>'}</td><td class="mono">${date(x.created_at)}</td>
      <td>${me ? '—' : `<button class="btn ghost sm" data-act="setrole" data-id="${x.id}" data-r="${x.role === 'admin' ? 'user' : 'admin'}">${x.role === 'admin' ? 'Make user' : 'Make admin'}</button> <button class="btn ghost sm" data-act="setdisabled" data-id="${x.id}" data-v="${x.disabled ? '0' : '1'}">${x.disabled ? 'Enable' : 'Disable'}</button>`}</td></tr>`; }).join('')}</tbody></table></div>`; }
  if (T === 'analytics') { const a = await api.admin.analytics(30); const names = {ask: 'Questions asked', search: 'Evidence searches', compare: 'Comparisons', signup: 'Sign-ups', post: 'Community posts', challenge_attempt: 'Challenge attempts', lesson_completed: 'Lessons completed'};
    const max = Math.max(1, ...Object.values(a.totals));
    body = `<p class="note">${esc(a.privacy)}</p><figure class="chart"><figcaption>Last ${a.days} days (since ${esc(a.since)})</figcaption>${Object.entries(names).map(([k, l]) => `<div class="bar"><span class="bl">${l}</span><span class="bt">${bar((a.totals[k] || 0) / max, 'bt-in')}</span><b class="mono">${a.totals[k] || 0}</b></div>`).join('')}</figure>`; }
  if (T === 'audit') { const a = await api.admin.audit({limit: 100});
    body = a.items.length ? `<div class="scroll"><table class="dt"><thead><tr><th>Timestamp</th><th>Administrator</th><th>Action</th><th>Affected record</th><th>Detail</th></tr></thead><tbody>${a.items.map(x => `<tr><td class="mono">${when(x.at)}</td><td>${esc(x.actor)}</td><td>${esc(x.action)}</td><td>${esc(x.target || '')}</td><td>${esc(x.detail || '')}</td></tr>`).join('')}</tbody></table></div>` : '<p class="empty">No admin actions recorded yet.</p>'; }
  return header('Admin Dashboard', 'Ingest and review sources, approve evidence and experiments, moderate the community, manage users.') +
    `<div class="tabs" role="tablist">${tabs.map(([k, l]) => `<button role="tab" aria-selected="${k === T}" data-act="tab" data-tab="${k}">${l}</button>`).join('')}</div>${body}`;
}

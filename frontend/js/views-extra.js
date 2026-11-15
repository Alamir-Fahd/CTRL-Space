import {api} from './api.js';
import {S, R, esc, header} from './ui.js';

const CAT_CLASS = {no_data_in_db: 'cov-none', topic_not_found: 'cov-none', data_not_extracted: 'cov-part', data_not_reported: 'cov-part', verified_absence: 'cov-good'};

/* Research gaps (corpus-scoped) */
export async function vGaps() {
  const g = await api.gaps(); const F = S.gapCat || '';
  const list = g.gaps.filter(x => !F || x.category === F);
  const counts = {}; g.gaps.forEach(x => { counts[x.category] = (counts[x.category] || 0) + 1; });
  return header('Research gap analysis', 'What the current CTRL+SPACE corpus does not cover, by type of gap. These are gaps in this collection, not in NASA research.') + `
    <div class="note"><b>Scope.</b> ${esc(g.scope)} Corpus: ${g.corpus.reports_with_text} reports with verified text, ${g.corpus.verified_passages} passages, ${g.corpus.experiments} experiments. <b>Confidence in corpus coverage: ${esc(g.coverage_confidence)}.</b></div>
    <div class="cats browse"><button class="catchip ${F ? '' : 'on'}" data-act="gapcat" data-c="">All (${g.gaps.length})</button>${Object.entries(g.categories).map(([k, l]) => `<button class="catchip ${k === F ? 'on' : ''}" data-act="gapcat" data-c="${k}" ${counts[k] ? '' : 'disabled'}>${esc(l)} (${counts[k] || 0})</button>`).join('')}</div>
    ${list.map(x => `<article class="rcard gap"><div class="rtop"><span class="covbadge ${CAT_CLASS[x.category]}">${esc(g.categories[x.category])}</span><span>Evidence coverage: ${esc(x.evidence_coverage)}</span></div>
      <h3>${esc(x.description)}</h3>
      <dl class="mini"><dt>Missing variables</dt><dd>${esc(x.missing_variables.join(', '))}</dd>
      <dt>Supporting reports</dt><dd>${x.supporting_reports.length ? x.supporting_reports.map(r => `<a href="${R.report(r)}">NTRS ${esc(r)}</a>`).join(', ') : '—'}</dd>
      <dt>Experiments</dt><dd>${esc(x.experiments.join(', ') || '—')}</dd>
      <dt>Possible research question</dt><dd>${esc(x.potential_question)} <small>${esc(x.question_note)}</small></dd></dl></article>`).join('') || '<p class="empty">No gaps of this type.</p>'}`;
}

/* Competition demo mode: preflight + guided journey on real records */
export async function vDemo() {
  const p = await api.preflight();
  const ok = p.status !== 'fail';
  const steps = [
    ['Open CTRL+SPACE', 'The dashboard explains the problem, the solution and how evidence flows.', `<a class="btn ghost sm" href="${R.home}">Open dashboard</a>`],
    ['Search BASS-II research', 'Research Discovery with the query preserved in the URL.', `<a class="btn ghost sm" href="${R.research('BASS-II')}">Search “BASS-II”</a>`],
    ['Open a NASA report', 'Abstract or metadata, verified passages with page or section references, original NTRS link.', `<a class="btn ghost sm" href="${R.report(p.reports[0])}">Open NTRS ${esc(p.reports[0])}</a>`],
    ['Ask a scientific question', 'The question is analyzed, evidence is retrieved and evaluated; coverage is shown.', p.questions.map(q => `<button class="btn ghost sm" data-act="try" data-q="${esc(q)}">${esc(q)}</button>`).join(' ')],
    ['Review evidence, answer and citations', p.mode === 'ai' ? 'The answer is structured into direct answer, explanation, evidence, conditions and limitations; every point cites a passage.' : 'Retrieval-only mode: the verified evidence is organized by type. No answer is generated and the page says so.', ''],
    ['Compare two experiments', 'A BASS-II glovebox test against a Saffire spacecraft-scale test: three comparison levels and honest warnings.', `<button class="btn ghost sm" data-act="democmp">Compare ${esc(p.experiments.join(' vs '))}</button>`],
    ['Generate a research brief', 'A Markdown brief with the question, evidence coverage, verbatim findings, the comparison and sources.', `<button class="btn sm" data-act="demobrief">Download research brief</button>`],
  ];
  return header('Competition demo mode', 'One reliable journey on real records: how combustion behaviour changes under microgravity.') + `
    <section class="panel"><h3>Preflight check <span class="covbadge ${p.status === 'ok' ? 'cov-good' : p.status === 'warn' ? 'cov-part' : 'cov-none'}">${p.status.toUpperCase()}</span></h3>
      <p>Assistant mode: <b>${p.mode === 'ai' ? 'AI answers from cited evidence' : 'Retrieval-only (verified evidence, no generated answers)'}</b>. ${esc(p.note)}</p>
      <ul class="checks">${p.checks.map(c => `<li class="ck-${c.status}"><span>${c.status === 'ok' ? '✓' : c.status === 'warn' ? '!' : '✗'}</span> <b>${esc(c.check)}</b> — ${esc(c.detail)}</li>`).join('')}</ul></section>
    ${ok ? '' : '<div class="err"><h3>Not ready</h3><p>Fix the failed checks before presenting (run python run.py reset-db, then python run.py preflight).</p></div>'}
    <ol class="demosteps">${steps.map(([t, d, a], i) => `<li><div><b>${i + 1}. ${t}</b><p>${d}</p></div><div class="ractions">${a}</div></li>`).join('')}</ol>
    <p class="fine">All records shown are real NTRS data already in the local database. No answer is prerecorded.</p>`;
}

/* Landing explanation for the home page */
export const landing = () => `
  <section class="why"><h2 class="sub big">Why CTRL+SPACE</h2><div class="whygrid">
    <div><h3>The problem</h3><p>Results from NASA’s fire-in-space experiments are spread across long technical reports, posters and presentations that are hard to search and compare.</p></div>
    <div><h3>The solution</h3><p>CTRL+SPACE turns those reports into searchable, comparable, evidence-grounded research: verified passages, structured experiments and cited answers.</p></div>
    <div><h3>The innovation</h3><p>Evidence-first AI: the model only sees verified passages, every claim must cite one, numbers are checked against their sources, and missing data stays missing.</p></div>
    <div><h3>The impact</h3><p>Students and researchers can explore microgravity combustion faster, and every statement can be traced back to the NASA source.</p></div></div></section>
  <section class="how"><h2 class="sub big">How it works</h2><ol class="pipeline">
    <li><b>1 · Data in</b><span>NTRS records and PDFs are imported. Passages are verified by a person before use.</span></li>
    <li><b>2 · Retrieval</b><span>Your question is analyzed and ranked against verified passages only (BM25). Weak matches stop here.</span></li>
    <li><b>3 · Evidence → LLM</b><span>Only the retrieved passages are sent to the AI, with rules: cite, keep conditions, no causal claims.</span></li>
    <li><b>4 · Validation</b><span>Citations must match retrieved passages; numbers must appear in them. Without an AI provider, you get the organized evidence.</span></li></ol></section>`;

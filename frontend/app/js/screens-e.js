/* ---------- Combustion Research Hub: PSI Data Repository, fire safety case studies, tech transfer ---------- */
/* ---------- Impact Dashboard + Judge Mode (NASA Space Apps judging criteria) ---------- */
import {api, R, S, esc, ic, head, backbar, sec, empty} from './core.js';

const CASES = {
  apollo1: {title: 'Apollo 1', date: 'January 27, 1967', source: 'https://sma.nasa.gov/sma-disciplines/accllp/apollo-1',
    summary: 'A fire swept through the Command Module during a pre-launch test, killing astronauts Virgil "Gus" Grissom, Edward White and Roger Chaffee.',
    sections: [
      ['What happened', 'During a preflight test at Launch Pad 34, with the cabin pressurized with pure oxygen and the hatch sealed, a flash fire swept through the Command Module so quickly the crew had no time to open the hatch.'],
      ['Cause', 'Investigators found evidence of arcing in wiring near the environment control system but could not pinpoint a single ignition source. The pure-oxygen atmosphere let the fire spread far faster than it would have in ordinary air.'],
      ['Investigation', 'NASA’s Apollo 204 Review Board published a roughly 3,000-page report on April 9, 1967. It found the three-piece hatch took about 90 seconds to open and could not be opened at all once cabin pressure rose, that the test had been classified “non-hazardous” (the rocket was unfueled) so no formal safety review occurred, and that no emergency rescue procedure existed.'],
      ['Safety lessons', 'NASA replaced the hatch with a single-piece design that opens in about three seconds from inside or outside, moved later crews to the redesigned Block II spacecraft, sharply restricted combustible materials in the cabin, and developed fire-resistant spacesuits.'],
    ]},
  apollo13: {title: 'Apollo 13', date: 'April 11–17, 1970', source: 'https://sma.nasa.gov/sma-disciplines/accllp/apollo-13',
    summary: 'An oxygen tank explosion on the third day of the mission forced the crew into the Lunar Module as a “lifeboat” and turned a Moon landing into a six-day survival flight home.',
    sections: [
      ['What happened', 'On April 13, 1970, during a routine tank-stir procedure, the crew heard a loud bang and saw warning lights for fuel cell failures. Oxygen vented into space, ruling out a lunar landing. Jack Swigert radioed Mission Control: “Houston, we’ve had a problem.”'],
      ['Cause', 'In 1965 the oxygen tank heaters’ voltage was raised from 28 to 65 volts, but the thermostatic switches were never updated to match. During pre-launch testing the heaters ran for extended periods, reaching roughly 1,000°F and degrading the Teflon wire insulation inside the tank — damage that went undetected until the tank was filled with oxygen in flight.'],
      ['Mission consequences', 'The crew moved into the Lunar Module, rationing water to six ounces per person per day as cabin temperature fell to about 38°F and carbon-dioxide removal became a struggle. Lovell, Haise and Swigert returned safely after six days.'],
      ['Safety lessons', 'Later missions added a third oxygen tank in a separate bay, upgraded thermostats to match the higher voltage, removed the tank-stirring fans implicated in the accident, sheathed wiring in stainless steel, and strengthened NASA’s engineering oversight of subsystem design.'],
    ]},
  mir: {title: 'Fire aboard Mir', date: 'February 24, 1997', source: 'https://www.nasa.gov/history/25-years-ago-fire-aboard-space-station-mir/',
    summary: 'A solid-fuel oxygen generator ignited aboard the Russian space station Mir, producing a three-foot flame during a six-person crew handover.',
    sections: [
      ['What happened', 'Shortly after dinner, a canister in a solid-fuel oxygen generator ignited, producing “a three-foot flame with sparks and bits of molten metal” and filling station modules with smoke. Six crew members were aboard: cosmonauts Valeri Korzun and Aleksandr Kaleri, NASA astronaut Jerry Linenger, newly arrived cosmonauts Vasili Tsibliyev and Aleksandr Lazutkin, and German astronaut Reinhold Ewald.'],
      ['Cause', 'A two-year investigation concluded that hydrocarbons — likely latex from work gloves — had contaminated the generator canister, increasing its fire risk.'],
      ['Crew response', 'The crew donned oxygen masks; Korzun used fire extinguishers to suppress the flames while Linenger steadied him and others supplied more extinguishers. The fire self-extinguished; some Kvant-1 module panels were charred but the station suffered no structural damage, and the life-support system cleared the toxic smoke within hours.'],
      ['Safety lessons', 'The incident shaped emergency training protocols and informed the redundant, dissimilar backup oxygen-generation systems built into the International Space Station.'],
    ]},
};
const TECH = [
  {title: 'Firefighter air tanks', source: 'https://spinoff.nasa.gov/node/9582',
    body: 'NASA’s Johnson Space Center worked with Scott Aviation (A-T-O Inc.) to adapt spacesuit life-support principles into a lighter self-contained breathing apparatus for firefighters: about 20 lb — 13 lb lighter than conventional tanks — with roughly 30 minutes of air at double the pressure of standard tanks, using an aluminum liner wrapped in resin-impregnated glass fibers that eliminates corrosion, plus an improved face mask and a clearer low-air warning. Structural Composites, Boeing and Martin-Marietta later built on the same approach.'},
  {title: 'Smoke and fire detector', source: 'https://spinoff.nasa.gov/node/9407',
    body: 'Technology from the Space Shuttle Orbiter program led to the Brunswick Incipient Fire Detector, which samples air to identify actual combustion particles rather than relying on visible smoke — so it tells real fires apart from dust and is less prone to false alarms. Multiple sensors can feed one central processor, making it well suited to large spaces such as mines, where it can flag a fire’s location before flames or smoke are visible.'},
  {title: 'Firefighter protective clothing', source: 'https://spinoff.nasa.gov/node/9918',
    body: 'Lightweight, heat-resistant materials originally developed for Apollo-era spacesuits and spacecraft thermal protection were adapted under Project FIRES (Firefighter’s Integrated Response Equipment System) to improve the protective gear firefighters wear, aiming to reduce injuries and fatalities during fire suppression.'},
];
const DISCLAIMER = 'NASA does not endorse any non-U.S. Government entity and is not responsible for information contained on non-U.S. Government websites. For non-U.S. Government websites, participants must comply with any data use parameters of that specific website.';

export function vCombustionHub() {
  return `${head('COMBUSTION RESEARCH', 'NASA fire & combustion science resources')}
    <section class="panel"><h3>${ic('flask', 18)} PSI Data Repository</h3><p>NASA’s Physical Sciences Informatics (PSI) repository holds the investigations behind microgravity combustion research — objectives, methods and findings, each citable by its own PSI accession ID.</p><a class="btn primary" href="/app/combustion/psi">Browse combustion investigations</a></section>
    <section class="panel"><h3>Background</h3><p>NASA Glenn’s Combustion Science program studies how flames behave without gravity’s buoyant flow, which on Earth dominates and obscures the chemistry and physics of burning. The results improve predictions of material flammability for crewed missions and inform fire safety on Earth. <a href="https://www.nasa.gov/glenn/glenn-expertise-space-exploration/physical-sciences-program/combustion-science/" target="_blank" rel="noopener">NASA Glenn: Combustion Science ↗</a></p>
      <p>A Researcher’s Guide to ISS Combustion Science explains why reduced gravity lets researchers isolate the chemistry of burning from the buoyancy effects that dominate flames on Earth. <a href="https://www.nasa.gov/missions/station/a-researchers-guide-to-combustion-science/" target="_blank" rel="noopener">Read the guide ↗</a></p></section>
    <section class="panel"><h3>Why it matters</h3><div class="ytwrap"><iframe class="yt" src="https://www.youtube.com/embed/W1oXykoz9zg" title="NASA ScienceCasts: The Power of Studying Combustion on the ISS" loading="lazy" allowfullscreen></iframe></div><p class="small">NASA ScienceCasts — The Power of Studying Combustion on the ISS. <a href="https://www.youtube.com/watch?v=W1oXykoz9zg" target="_blank" rel="noopener">Watch on YouTube ↗</a></p></section>
    ${sec('Spacecraft fire safety case studies')}<div class="stack">${Object.entries(CASES).map(([id, c]) => `<a class="panel res" href="/app/combustion/case/${id}"><h3>${esc(c.title)}</h3><p class="meta">${esc(c.date)}</p><p class="muted">${esc(c.summary)}</p></a>`).join('')}</div>
    ${sec('NASA technology transfer')}${TECH.map(t => `<details class="panel faq"><summary>${esc(t.title)}</summary><p>${esc(t.body)}</p><a class="small" href="${t.source}" target="_blank" rel="noopener">NASA Spinoff ↗</a></details>`).join('')}
    <p class="muted pad">${esc(DISCLAIMER)} Historical case studies and technology-transfer summaries on this page are written from the official NASA pages linked above; the PSI investigation records are NASA’s own metadata, fetched live and cached here for offline use.</p>`;
}
export function vCase(id) {
  const c = CASES[id];
  if (!c) return backbar('/app/combustion') + empty('Case study not found.');
  return `${backbar('/app/combustion')}${head(esc(c.title.toUpperCase()), esc(c.date))}
    ${c.sections.map(([h, t]) => `<section class="panel"><h3>${esc(h)}</h3><p>${esc(t)}</p></section>`).join('')}
    <p class="small pad">Source: <a href="${c.source}" target="_blank" rel="noopener">${esc(c.source)} ↗</a></p>
    <p class="muted pad">${esc(DISCLAIMER)}</p>`;
}
export async function vPsi() {
  const q = S.psiQ; let data; try { data = await api.psi(q); } catch (e) { return backbar('/app/combustion') + head('PSI COMBUSTION', 'NASA Physical Sciences Informatics') + empty(e.message); }
  return `${backbar('/app/combustion')}${head('PSI COMBUSTION', `${data.total ?? data.items.length} investigation${data.total === 1 ? '' : 's'}${data.stale ? ' · offline copy' : ''}`)}
    <form class="searchbar" data-form="psisearch">${ic('search', 20)}<input name="q" value="${esc(q)}" maxlength="80" aria-label="Search PSI investigations"><button class="btn sm primary">Search</button></form>
    ${data.items.length ? `<div class="stack">${data.items.map(it => `<a class="panel res" href="/app/combustion/psi/${esc(it.accession)}"><h3>${esc(it.title)}</h3><p class="meta">${esc(it.accession)} · ${esc(it.research_area || '')}${it.sub_research_area ? ' · ' + esc(it.sub_research_area) : ''}</p><p class="muted">${esc((it.objectives || '').slice(0, 160))}…</p></a>`).join('')}</div>`
      : empty('No PSI investigations matched that search.')}
    <p class="muted pad">Source: ${esc(data.source)} · retrieved ${esc((data.retrieved_at || '').slice(0, 10))}${data.cached ? ' (cached)' : ''}. ${esc(data.usage || '')}</p>`;
}
export async function vPsiDetail(accession) {
  let it; try { it = await api.psiInvestigation(accession); } catch (e) { return backbar('/app/combustion/psi') + empty(e.message); }
  const kv = (k, v) => v ? `<dt>${esc(k)}</dt><dd>${esc(v)}</dd>` : '';
  const bytes = n => n == null ? null : n > 1e6 ? `${(n / 1e6).toFixed(1)} MB` : n > 1e3 ? `${(n / 1e3).toFixed(0)} KB` : `${n} B`;
  return `${backbar('/app/combustion/psi')}${head(esc(it.accession), esc(it.research_area || ''))}${it.stale ? `<p class="note-inline">${ic('offline', 16)} Offline copy, last retrieved ${esc((it.retrieved_at || '').slice(0, 10))}.</p>` : ''}
    <h1 class="dt">${esc(it.title || it.accession)}</h1>
    <section class="panel"><dl class="kv">${kv('Project type', it.project_type)}${kv('Sub-research area', it.sub_research_area)}${kv('Flight platform', it.flight_platform)}${kv('Managing center', it.managing_center)}${kv('Start date', it.start_date)}${kv('End date', it.end_date)}${kv('DOI', it.doi)}${kv('License', it.license_name)}${kv('Version', it.version ? `v${it.version}` : null)}</dl></section>
    ${it.objective ? `<section class="panel"><h3>Objective</h3><p>${esc(it.objective)}</p></section>` : ''}
    ${it.approach ? `<section class="panel"><h3>Approach</h3><p>${esc(it.approach)}</p></section>` : ''}
    ${it.publications?.length ? `${sec(`Publications (${it.publications.length})`)}<ul class="list">${it.publications.map(p => `<li><span><b>${esc(p.title)}</b>${p.authors ? `<small>${esc(p.authors)}</small>` : ''}${p.doi ? `<small>DOI: ${esc(p.doi)}</small>` : ''}</span></li>`).join('')}</ul>` : ''}
    ${it.files?.length ? `${sec(`Data files and documents (${it.file_count})`)}<ul class="list">${it.files.slice(0, 20).map(f => `<li><a href="${esc(f.url?.startsWith('http') ? f.url : 'https://psi.nasa.gov' + (f.url || ''))}" target="_blank" rel="noopener">${ic('doc', 18)}<span><b>${esc(f.name)}</b>${f.size ? `<small>${esc(bytes(f.size))}</small>` : ''}</span></a></li>`).join('')}</ul>${it.file_count > 20 ? `<p class="muted pad">+ ${it.file_count - 20} more files on the full investigation page.</p>` : ''}` : ''}
    <a class="btn primary block" href="${it.landing_url}" target="_blank" rel="noopener">Cite this investigation on psi.nasa.gov ↗</a>
    <p class="muted pad">Source: ${esc(it.source || 'NASA Physical Sciences Informatics (PSI) Data Repository')} · retrieved ${esc((it.retrieved_at || '').slice(0, 10))}${it.cached ? ' (cached)' : ''}. ${esc(it.usage || '')}</p>
    <p class="muted pad">${esc(DISCLAIMER)}</p>`;
}

export async function vImpact() {
  const im = await api.impact(); const r = im.research, v = im.validation;
  const stat = (n, l) => `<div><b>${esc(String(n))}</b><span>${esc(l)}</span></div>`;
  return `${backbar(R.profile)}${head('RESEARCH IMPACT', 'Measured from this running instance, not a user study')}
    <div class="stats">${stat(r.reports_indexed, 'reports indexed')}${stat(r.verified_passages, 'verified passages')}${stat(r.experiments, 'experiments')}${stat(r.questions_processed, 'questions processed')}${stat(r.evidence_grounded_answers, 'evidence-grounded answers')}${stat(r.active_sessions, 'active sessions')}</div>
    ${v ? `<section class="panel"><h3>Scientific validation</h3><p>Retrieval recall@6: <b>${esc(String(v.recall_at_6))}</b> · MRR: <b>${esc(String(v.mrr))}</b> · evidence-gate pass rate: <b>${esc(String(v.gate_pass_rate))}</b> on ${esc(String(v.answerable_questions))} answerable benchmark questions.</p><p>Correctly refused <b>${esc(String(v.correctly_refused))}/${esc(String(v.unsupported_questions))}</b> deliberately unsupported questions (never guessed).</p><p class="small">Benchmark run: ${esc((v.run_at || '').slice(0, 10))} · ${esc(v.source)}</p></section>` : '<p class="muted pad">No benchmark run found.</p>'}
    <p class="muted pad">${esc(im.disclaimer)}</p>`;
}
export async function vJudge() {
  const s = await api.stats();
  return `${backbar(R.profile)}${head('JUDGE MODE', 'NASA Space Apps 2026 — Flame in Freefall')}
    <section class="panel"><h3>Challenge alignment</h3><p>CTRL+SPACE is built for “Flame in Freefall”: it searches NASA’s own combustion-science records (NTRS reports and PSI investigations), lets an AI assistant answer only from verified passages, and lets researchers compare real microgravity combustion experiments side by side.</p></section>
    <section class="panel"><h3>Main innovations</h3><ul><li>Evidence gate: checks retrieval quality before any AI call, and refuses rather than guesses.</li><li>Numeric grounding: every number in a generated answer is checked against its cited passage.</li><li>Comparison levels 1–3 distinguish shared conditions, confounding differences and raw findings — never causal claims.</li><li>Live NASA PSI integration for combustion investigations, not a static copy.</li><li>One Arabic-RTL mobile client sharing the same backend and evidence rules as English.</li></ul></section>
    <section class="panel"><h3>NASA data sources</h3><ul><li>NASA Technical Reports Server (NTRS) — ${s.reports} reports, ${s.verified_passages} human-verified passages</li><li>NASA Physical Sciences Informatics (PSI) — live combustion investigations, <a href="/app/combustion/psi">browse</a></li><li>NASA Image and Video Library</li><li>NASA Spinoff &amp; SMA history pages — fire-safety case studies and technology transfer</li></ul></section>
    <section class="panel"><h3>AI architecture</h3><p>Question → BM25 retrieval → evidence-sufficiency gate → (if passed) generation from an optional provider (Anthropic / OpenAI / Ollama) → citation validation → numeric grounding check → structured answer. Without a configured provider the same evidence is shown as a retrieval-only brief — never silently upgraded into a generated answer.</p></section>
    <div class="row wrap"><a class="btn primary" href="/app/impact">${ic('spark', 18)} Impact dashboard</a><a class="btn ghost" href="${R.demo}">${ic('play', 18)} Live demo script</a><a class="btn ghost" href="/app/combustion">${ic('flask', 18)} Combustion hub</a></div>
    <p class="muted pad">CTRL+SPACE is an independent student project exploring NASA open data. It is not affiliated with or endorsed by NASA, and it is not a validated spacecraft fire-prediction or safety-certification tool.</p>`;
}

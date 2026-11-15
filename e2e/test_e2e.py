"""Browser tests for the CTRL+SPACE spec: launch, the six mandatory journeys (A-F) and every screen.
Run: bash scripts/run_e2e.sh  (throwaway server + admin from env). Screenshots -> e2e/screenshots/."""
import os, re, sys, time
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import expect, sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8000'
OUT = os.path.join(os.path.dirname(__file__), 'screenshots')
ADMIN = (os.environ.get('CTRLSPACE_E2E_ADMIN_EMAIL'), os.environ.get('CTRLSPACE_E2E_ADMIN_PASSWORD'))
PW, STAMP = 'FlameSpread2026', str(int(time.time()))
results, console_errors = [], []
EXPECTED_4XX = re.compile(r'status of (401|403|404|409|422)')


def step(name):
    def deco(fn):
        def run(page):
            t = time.time()
            try:
                fn(page); results.append((name, 'PASS', f'{time.time() - t:.1f}s'))
            except Exception as e:
                results.append((name, 'FAIL', str(e).splitlines()[0][:170])); page.screenshot(path=os.path.join(OUT, f'FAIL-{name[:30]}.png'))
        return run
    return deco


def shot(page, name):
    page.wait_for_timeout(300); page.screenshot(path=os.path.join(OUT, f'{name}.png'), full_page=True)


def open_(page, path):
    page.goto(BASE + path); page.wait_for_selector('#splash', state='detached', timeout=10000)


def login(page, email, pw):
    open_(page, '/login'); page.fill('input[name=email]', email); page.fill('input[name=password]', pw)
    page.click('form[data-form=login] button'); expect(page.locator('#acct .who')).to_be_visible()


def logout(page):
    page.click('#acct button:has-text("Sign out")'); expect(page.locator('#acct a:has-text("Sign in")')).to_be_visible()


@step('Launch: logo, backend check, then dashboard')
def launch(page):
    page.goto(BASE + '/')
    expect(page.locator('#splash .splash-mark')).to_contain_text('space')
    shot(page, '00-launch')
    page.wait_for_selector('#splash', state='detached', timeout=10000)
    expect(page.locator('main h1')).to_have_text('Explore the Science of Fire in Space')
    expect(page).to_have_title('Dashboard · CTRL+SPACE')


@step('01 Home: hero actions, 6 quick cards, real overview, recent research')
def home(page):
    expect(page.locator('.hero-cta a')).to_have_count(2)
    expect(page.locator('.quickgrid .path')).to_have_count(6)
    expect(page.locator('.band .stat').first).to_contain_text('research reports available')
    expect(page.locator('.rgrid .rcard')).to_have_count(4)
    page.click('form[data-form=homesearch] button')
    expect(page.locator('#hserr')).to_contain_text('at least 2')
    shot(page, '01-home')


@step('Journey A: search → filters → results → report → evidence → NASA source')
def journey_a(page):
    page.fill('#hs', 'flame spread'); page.click('form[data-form=homesearch] button')
    expect(page).to_have_url(BASE + '/research?q=flame%20spread')
    expect(page.locator('main h2')).to_have_text('Research Discovery')
    page.select_option('form[data-form=disc] select[name=evidence]', 'verified'); page.fill('form[data-form=disc] input[name=year_from]', '2014')
    page.click('form[data-form=disc] button.fire')
    expect(page.locator('.count')).to_contain_text('with filters applied')
    card = page.locator('.rcard', has_text='Combustion of Solids in Microgravity')
    expect(card.locator('.status-line')).to_contain_text('verified passage')
    shot(page, '02-research-discovery')
    card.locator('a:has-text("Open report")').click()
    expect(page).to_have_url(BASE + '/library/20160000593')
    expect(page.locator('.passage').first).to_contain_text('Objectives')
    expect(page.locator('a:has-text("Open original NASA source")')).to_have_attribute('href', 'https://ntrs.nasa.gov/citations/20160000593')
    expect(page.locator('dl.meta')).to_contain_text('Combustion, Fire Safety, Microgravity')
    shot(page, '04-report-details')
    page.go_back(); expect(page).to_have_url(re.compile(r'/research'))


@step('Journey B: assistant validation, evidence answer, insufficient evidence')
def journey_b(page):
    open_(page, '/assistant')
    page.fill('#aq', 'hi'); page.click('form[data-form=ask] button')
    expect(page.locator('#askerr')).to_have_text('Enter at least 3 characters.')
    page.click('button.chip:has-text("What factors influence flame extinction?")')
    expect(page.locator('#askout .passage').first).to_be_visible(timeout=15000)
    expect(page.locator('#askout .passage a:has-text("Open NASA source")').first).to_have_attribute('href', re.compile(r'^https://ntrs\.nasa\.gov/citations/'))
    shot(page, '05-assistant')
    page.fill('#aq', 'What is the best pizza topping in Cairo?'); page.click('form[data-form=ask] button')
    expect(page.locator('.insuff')).to_contain_text('Insufficient scientific evidence was found in the available research collection to provide a reliable answer.')
    expect(page.locator('#aq')).to_have_value('What is the best pizza topping in Cairo?')


@step('Journey C: explorer → details → add → select another → compare → export')
def journey_c(page):
    open_(page, '/experiments')
    page.select_option('form[data-form=expf] select[name=material]', 'PMMA'); page.click('form[data-form=expf] button')
    expect(page.locator('.count')).to_contain_text('of 8 experiments')
    shot(page, '06-experiment-explorer')
    page.locator('.ecard', has_text='Saffire VI-3').locator('a:has-text("Details")').click()
    for f in ('Oxygen basis', 'Temperature', 'Experimental apparatus'):
        expect(page.locator(f'table.dt th:has-text("{f}")').first).to_be_visible()
    expect(page.locator('table.dt thead')).to_contain_text('Verification')
    shot(page, '07-experiment-details')
    page.click('button:has-text("Add to comparison")'); page.click('.side a:has-text("Compare")')
    expect(page.locator('.note')).to_contain_text('at least one more')
    page.fill('[data-input=cmpfilter]', 'VI-4'); page.wait_for_timeout(600)
    page.check('input[data-id="saffire6-4"]')
    expect(page.locator('.selhead b')).to_have_text('2 of 4 selected')
    expect(page.locator('h3.sub:has-text("Conditions")')).to_be_visible(); expect(page.locator('h3.sub:has-text("Measurements and results")')).to_be_visible()
    expect(page.locator('.chart figcaption')).to_be_visible()
    expect(page.locator('.warnbox')).to_contain_text('Similarities')
    shot(page, '08-compare')
    with page.expect_download() as dl:
        page.click('button:has-text("Export comparison")')
    md = open(dl.value.path(), encoding='utf-8').read()
    assert '## Conditions' in md and 'NTRS 20240007488' in md, 'comparison export'


@step('Journey D: save report → My Research → collection → reopen')
def journey_d(page):
    open_(page, '/register')
    page.fill('input[name=name]', 'Test Researcher'); page.fill('input[name=email]', f'r{STAMP}@example.com'); page.fill('input[name=password]', 'short')
    page.click('form[data-form=register] button'); expect(page.locator('[data-for=password]')).not_to_be_empty()
    page.fill('input[name=password]', PW); page.click('form[data-form=register] button'); expect(page.locator('#acct .who')).to_have_text('Test Researcher')
    page.click('.side a:has-text("Research Discovery")')
    page.click('button[data-act=discclear]')
    page.locator('.rcard', has_text='Results from On-Board CSA-CP').locator('a:has-text("Open report")').click()
    page.click('button:has-text("Save report")'); expect(page.locator('button:has-text("Saved ✓")')).to_be_visible()
    page.click('button:has-text("Add to collection")')
    page.fill('#dlg form[data-form=quickcol] input', 'CO measurements'); page.click('#dlg form[data-form=quickcol] button'); expect(page.locator('#dlg')).not_to_be_visible()
    page.fill('#note', 'Concurrent rods: 550 ppm CO per 1% CO2.'); page.click('form[data-form=note] button'); expect(page.locator('#toast')).to_contain_text('Note saved')
    page.click('.side a:has-text("My Research")')
    expect(page.locator('table.dt')).to_contain_text('Results from On-Board CSA-CP')
    shot(page, '09-my-research')
    page.click('button[data-tab=collections]'); expect(page.locator('.rcard', has_text='CO measurements')).to_contain_text('Results from On-Board')
    page.click('button[data-tab=notes]'); expect(page.locator('.rcard textarea')).to_have_value('Concurrent rods: 550 ppm CO per 1% CO2.')
    page.click('button[data-tab=activity]'); expect(page.locator('.timeline')).to_contain_text('Opened report')


@step('Journey E: library → filter → report → extracted pages → source → back')
def journey_e(page):
    page.click('.side a:has-text("Evidence Library")')
    expect(page.locator('main h2')).to_have_text('Scientific Evidence Library')
    page.select_option('form[data-form=lib] select[name=evidence]', 'verified'); page.click('form[data-form=lib] button.btn:not(.ghost)')
    expect(page.locator('.count')).to_have_text('4 reports')
    shot(page, '03-evidence-library')
    page.locator('.rcard').first.locator('a:has-text("Open details")').click()
    page.click('button[data-tab=pages]'); expect(page.locator('.empty')).to_contain_text('No extracted page text')
    expect(page.locator('a:has-text("Open original NASA source")')).to_have_attribute('href', re.compile(r'^https://ntrs\.nasa\.gov/citations/'))
    page.click('a:has-text("Back to Evidence Library")'); expect(page).to_have_url(BASE + '/library')
    page.click('button[data-tab=passages]'); page.fill('form[data-form=libp] input', 'radiative quenching'); page.click('form[data-form=libp] button')
    expect(page.locator('.passage').first).to_contain_text('radiative quenching')


@step('10 Studio: topics, objectives, evidence, prev/next, completion')
def studio(page):
    page.click('.side a:has-text("Learning Studio")')
    page.click('.catchip:has-text("Flame extinction")'); expect(page.locator('.ecard')).to_have_count(1)
    page.click('a:has-text("Airflow, quenching and blow-off")')
    expect(page.locator('.panel', has_text='Learning objectives').locator('li')).to_have_count(3)
    expect(page.locator('.panel', has_text='Related reports')).to_contain_text('Combustion of Solids')
    page.click('button:has-text("Mark as completed")'); expect(page.locator('.ractions')).to_contain_text('You completed this lesson')
    shot(page, '10-studio')
    page.click('.lnav a:has-text("Oxygen concentration")'); expect(page.locator('main h2')).to_have_text('Oxygen concentration and flame spread')


@step('11 Challenges: details, saved draft, grading with sources, status')
def challenges(page):
    open_(page, '/challenges/flow-limits')
    expect(page.locator('dl.meta')).to_contain_text('Objective'); expect(page.locator('dl.meta')).to_contain_text('Instructions')
    page.check('input[name=q1][value="0"]'); page.reload(); page.wait_for_selector('#splash', state='detached')
    expect(page.locator('input[name=q1][value="0"]')).to_be_checked()                       # draft kept
    page.check('input[name=q2][value="2"]'); page.check('input[name=q3][value="0"]')         # q3 wrong on purpose
    page.click('form[data-form=attempt] button.fire')
    expect(page.locator('.rdetail h3').first).to_contain_text('Passed: 2 / 3')
    expect(page.locator('fieldset.q.wrong .verdict')).to_contain_text('20 cm/s')
    shot(page, '11-challenge')
    page.click('a:has-text("Back to challenges")'); expect(page.locator('.ecard', has_text='Flow and extinction limits')).to_contain_text('Passed')


@step('12 Community: share, post, edit, reply; second user reports')
def community(page):
    open_(page, '/library/20160000593')
    page.click('button:has-text("Share in community")'); page.click('#dlg button:has-text("BASS-II")')
    expect(page.locator('form[data-form=newpost] .note')).to_contain_text('Sharing: report')
    page.fill('form[data-form=newpost] input[name=title]', f'Margin of safety {STAMP}'); page.fill('form[data-form=newpost] textarea', 'First version')
    page.click('form[data-form=newpost] button.fire')
    post = page.locator('.post', has_text=STAMP).first
    post.locator('button:has-text("Edit")').click(); page.fill('form[data-form=editpost] textarea', 'Has anyone compared this with Saffire?'); page.click('form[data-form=editpost] button.btn:not(.ghost)')
    expect(page.locator('.post', has_text=STAMP).first).to_contain_text('edited')
    page.locator('.post', has_text=STAMP).first.locator('a.linkish').click()
    page.fill('form[data-form=reply] textarea', 'Saffire used concurrent flow at 20 cm/s.'); page.click('form[data-form=reply] button')
    expect(page.locator('.post')).to_have_count(2)
    url = page.url
    page.click('.side a:has-text("Community")'); expect(page.locator('.panel', has_text='Recent discussions')).to_contain_text(STAMP)
    shot(page, '12-community')
    logout(page)
    open_(page, '/register')
    page.fill('input[name=name]', 'Second User'); page.fill('input[name=email]', f's{STAMP}@example.com'); page.fill('input[name=password]', PW); page.click('form[data-form=register] button')
    expect(page.locator('#acct .who')).to_have_text('Second User')
    page.goto(url); page.wait_for_selector('#splash', state='detached')
    page.locator('.post').first.locator('button:has-text("Report")').click(); page.select_option('#dlg select[name=reason]', 'off_topic'); page.click('#dlg form button')
    expect(page.locator('.post').first).to_contain_text('You reported this')
    logout(page)


@step('13 Profile & settings: privacy, sessions, theme, password')
def settings(page):
    login(page, f'r{STAMP}@example.com', PW)
    page.click('.side a:has-text("Profile")'); expect(page.locator('.kpis')).to_contain_text('saved items'); shot(page, '13-profile')
    page.click('.side a:has-text("Settings")')
    expect(page.locator('.panel', has_text='Signed-in sessions')).to_contain_text('This device')
    page.uncheck('input[data-act=history]'); expect(page.locator('#toast')).to_contain_text('History turned off')
    page.click('button[data-t=dark]'); expect(page.locator('html')).to_have_attribute('data-theme', 'dark')
    page.fill('input[name=current_password]', 'Wrong12345X'); page.fill('input[name=new_password]', 'NewFlame2027x'); page.click('form[data-form=password] button')
    expect(page.locator('form[data-form=password] .formerr')).to_contain_text('incorrect')
    page.fill('input[name=current_password]', PW); page.click('form[data-form=password] button'); expect(page.locator('#toast')).to_contain_text('Password changed')
    shot(page, '13-settings')
    page.click('button[data-t=system]'); logout(page)


@step('Journey F: admin health → report → flag evidence → review → reject/approve experiment → audit')
def journey_f(page):
    open_(page, '/admin'); expect(page.locator('main')).to_contain_text('Sign in to use the admin dashboard')
    login(page, *ADMIN)
    expect(page).to_have_url(BASE + '/admin')
    expect(page.locator('.panel', has_text='System health')).to_contain_text(re.compile(r'schema v\d'))
    shot(page, '14-admin-overview')
    page.click('button[data-tab=reports]'); expect(page.locator('table.dt tbody tr')).to_have_count(6)
    open_(page, '/library/20160000593')
    page.locator('.passage', has_text='13.6% oxygen').locator('button:has-text("Flag extraction")').click()
    page.fill('#dlg textarea', 'Check the value against the original poster'); page.click('#dlg form button')
    expect(page.locator('#toast')).to_contain_text('flagged')
    open_(page, '/admin'); page.click('button[data-tab=experiments]')
    expect(page.locator('tr', has_text='Spacecraft Materials Microgravity')).to_contain_text('Unverified')
    page.click('button[data-tab=review]')
    item = page.locator('.review', has_text='13.6% oxygen'); expect(item).to_contain_text('Flagged: Check the value')
    item.locator('select').select_option('finding'); item.locator('button:has-text("Approve evidence")').click(); expect(page.locator('#toast')).to_contain_text('Evidence approved')
    page.click('button[data-tab=experiments]')
    page.locator('tr', has_text='Growth and Extinction Limit').locator('button:has-text("Reject")').click()
    page.fill('#dlg textarea', 'Units to recheck'); page.click('#dlg form button'); expect(page.locator('#toast')).to_contain_text('rejected')
    page.locator('tr', has_text='Growth and Extinction Limit').locator('button:has-text("Approve and publish")').click(); expect(page.locator('#toast')).to_contain_text('approved')
    page.click('button[data-tab=moderation]'); page.locator('.review', has_text=STAMP).locator('button:has-text("Hide post")').click()
    page.click('button[data-tab=users]'); urow = page.locator('tr', has_text=f's{STAMP}@example.com')
    urow.locator('button:has-text("Disable")').click(); expect(urow).to_contain_text('disabled'); urow.locator('button:has-text("Enable")').click()
    page.click('button[data-tab=audit]')
    for a in ('passage.flagged', 'passage.verify', 'experiment.rejected', 'experiment.published', 'post.hide', 'user.disabled'):
        expect(page.locator('table.dt')).to_contain_text(a)
    shot(page, '14-admin-audit'); logout(page)


@step('Honest states: 404 route, missing report, hidden post')
def states(page):
    open_(page, '/no/such/page'); expect(page.locator('h2')).to_have_text('Page not found')
    open_(page, '/library/99999999'); expect(page.locator('.err h3')).to_have_text('Not found')
    open_(page, '/community/bass-ii'); expect(page.locator('.post', has_text='hidden by a moderator').first).to_be_visible()


@step('Landing: problem, solution, innovation, impact + how it works')
def landing(page):
    open_(page, '/')
    expect(page.locator('.whygrid > div')).to_have_count(4); expect(page.locator('.pipeline li')).to_have_count(4)
    expect(page.locator('.whygrid')).to_contain_text('Evidence-first AI')


@step('Assistant: question analysis, coverage, retrieval-only structured evidence, brief')
def structured(page):
    open_(page, '/assistant')
    page.fill('#aq', 'How does oxygen concentration affect flame spread in microgravity?'); page.click('form[data-form=ask] button')
    expect(page.locator('.note.mode')).to_contain_text('Retrieval-only mode', timeout=15000)
    expect(page.locator('.coverage')).to_contain_text('interpretation question')
    expect(page.locator('.covbadge').first).to_have_text('Well supported')
    expect(page.locator('h3.sub:has-text("Experimental evidence (reported findings)")')).to_be_visible()
    expect(page.locator('ul.srcs li').first).to_contain_text('NTRS')
    shot(page, '05b-assistant-structured')
    with page.expect_download() as dl:
        page.click('button:has-text("Download research brief")')
    md = open(dl.value.path(), encoding='utf-8').read()
    assert 'Evidence coverage' in md and 'Reported findings (verbatim)' in md, 'brief content'


@step('Compare: three levels, statement types, normalized units')
def levels(page):
    open_(page, '/experiments/saffire6-3')
    expect(page.locator('tr:has(th:has-text("Flow velocity")) .norm')).to_contain_text('0.2 m/s (divide by 100 (from cm/s); original kept)')
    page.evaluate("sessionStorage.setItem('cs.cmp', JSON.stringify(['bass2-smmrf','saffire6-3']))"); open_(page, '/compare')
    expect(page.locator('h3:has-text("Level 2")')).to_be_visible()
    expect(page.locator('.ctxlist')).to_contain_text('Different materials')
    expect(page.locator('.finding .tag').first).to_contain_text('Reported')
    expect(page.locator('.rule')).to_contain_text('does not infer')
    shot(page, '08b-compare-levels')


@step('Research gaps: corpus-scoped and typed')
def gaps(page):
    page.click('.side a:has-text("Research Gaps")')
    expect(page.locator('.note').first).to_contain_text('Confidence in corpus coverage: Low')
    page.click('.catchip:has-text("Research topic not found")')
    expect(page.locator('.gap').first).to_contain_text('no verified passage')
    expect(page.locator('.gap').first).to_contain_text('NOT evidence that NASA never studied it')
    shot(page, '16-research-gaps')


@step('Demo mode: preflight, guided journey, live brief')
def demo(page):
    page.click('.side a:has-text("Demo mode")')
    expect(page.locator('.checks')).to_contain_text('Database'); expect(page.locator('.checks')).to_contain_text('retrieval-only mode')
    expect(page.locator('.demosteps li')).to_have_count(7)
    shot(page, '17-demo-mode')
    with page.expect_download() as dl:
        page.click('button:has-text("Download research brief")')
    md = open(dl.value.path(), encoding='utf-8').read()
    assert 'Mode: retrieval-only' in md and 'Why these results are hard to compare' in md, 'demo brief'
    page.click('button[data-act=democmp]'); expect(page.locator('.selhead b')).to_have_text('2 of 4 selected')


def mobile(browser):
    ctx = browser.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2, is_mobile=True, has_touch=True)
    ctx.route('**/fonts.g*/**', lambda r: r.abort()); p = ctx.new_page()
    open_(p, '/'); shot(p, '15-mobile-home')
    p.click('.top .menu'); expect(p.locator('.side')).to_be_in_viewport(); shot(p, '15-mobile-menu')
    p.click('.side nav a:has-text("Compare")'); expect(p.locator('h2')).to_have_text('Compare Scientific Experiments')
    bad = [r for r in ('/', '/research', '/experiments/bass2-gel', '/studio', '/community') if (open_(p, r) or p.evaluate('document.documentElement.scrollWidth > window.innerWidth'))]
    results.append(('Mobile: menu drawer, no horizontal scroll', 'FAIL' if bad else 'PASS', ', '.join(bad))); ctx.close()


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        ctx = b.new_context(viewport={'width': 1366, 'height': 900}, accept_downloads=True)
        ctx.route('**/fonts.g*/**', lambda r: r.abort()); page = ctx.new_page()
        page.on('console', lambda m: m.type == 'error' and 'fonts.g' not in m.text and 'ERR_FAILED' not in m.text and not EXPECTED_4XX.search(m.text) and console_errors.append(m.text))
        page.on('pageerror', lambda e: console_errors.append(str(e)))
        for fn in (launch, home, landing, journey_a, journey_b, structured, journey_c, levels, journey_d, journey_e, studio, challenges, community, settings, journey_f, gaps, demo, states):
            fn(page)
        mobile(b); b.close()
    w = max(len(n) for n, _, _ in results)
    for n, s, d in results:
        print(f'{s:4}  {n.ljust(w)}  {d}')
    print(f'\n{sum(s == "PASS" for _, s, _ in results)}/{len(results)} passed; console errors: {len(console_errors)}')
    for e in console_errors:
        print('  console:', e[:200])
    sys.exit(0 if all(s == 'PASS' for _, s, _ in results) and not console_errors else 1)

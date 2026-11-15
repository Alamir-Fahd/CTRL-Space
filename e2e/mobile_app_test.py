"""Mobile app (/app) journeys on a phone profile. Usage: python e2e/mobile_app_test.py BASE_URL "iPhone 14"
Screenshots -> e2e/screenshots/app/ (used for the UI gallery)."""
import os, sys, time
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import expect, sync_playwright
B, DEV = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else 'iPhone 14')
OUT = os.path.join(os.path.dirname(__file__), 'screenshots', 'app', DEV.replace(' ', '-')); os.makedirs(OUT, exist_ok=True)
res, errs = [], []; ST = str(int(time.time())); PW = 'FlameSpread2026'


def ok(name, fn, pg):
    try: fn(); res.append(('PASS', name)); print('PASS', name, flush=True)
    except Exception as e: res.append(('FAIL', name)); print('FAIL', name, str(e).splitlines()[0][:160], flush=True); pg.screenshot(path=f'{OUT}/FAIL-{name[:30]}.png')


def ready(pg): pg.wait_for_selector('#splash', state='detached', timeout=10000); pg.wait_for_selector('#view > :not(.pad)', timeout=10000); pg.wait_for_timeout(450)
def shot(pg, n): pg.screenshot(path=f'{OUT}/{n}.png')
def open_(pg, path): pg.goto(B + path); ready(pg)


with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(**p.devices[DEV], accept_downloads=True); ctx.route('**/fonts.g*/**', lambda r: r.abort()); pg = ctx.new_page()
    pg.on('pageerror', lambda e: errs.append(str(e)))

    def splash():
        pg.goto(B + '/app', wait_until='commit'); expect(pg.locator('#splash .tagline')).to_have_text('Explore. Research. Discover.'); pg.wait_for_timeout(250); shot(pg, '01-splash'); ready(pg)
    ok('01 Splash: logo, tagline, backend check, then onboarding', splash, pg)

    def onboarding():
        expect(pg).to_have_url(B + '/app/welcome'); shot(pg, '02-onboarding')
        for _ in range(3): pg.click('#onbnext'); pg.wait_for_timeout(450)
        expect(pg.locator('#onbnext')).to_have_text('Get started'); pg.click('#onbnext'); pg.wait_for_url(B + '/app'); ready(pg)
        open_(pg, '/app'); expect(pg).to_have_url(B + '/app')                                   # completion persisted
    ok('02 Onboarding: 4 slides, next, get started, persisted', onboarding, pg)

    def register():
        open_(pg, '/app/register'); pg.fill('input[name=name]', 'Kenzy Test'); pg.fill('input[name=email]', f'k{ST}@example.com')
        pg.fill('input[name=password]', PW); pg.fill('input[name=confirm]', PW + 'x'); pg.click('form[data-form=register] button.primary')
        expect(pg.locator('[data-for=confirm]')).to_have_text('Passwords don’t match.')
        pg.fill('input[name=confirm]', PW); pg.click('form[data-form=register] button.primary'); expect(pg.locator('[data-for=terms]')).to_contain_text('accept')
        pg.click('button[data-act=togglepw] >> nth=0'); expect(pg.locator('input[name=password]')).to_have_attribute('type', 'text')
        pg.fill('input[name=interests]', 'flame spread, PMMA'); pg.check('input[name=category][value=researcher]'); pg.fill('input[name=institution]', 'Test University'); pg.check('input[name=terms]'); shot(pg, '04-register')
        pg.click('form[data-form=register] button.primary'); pg.wait_for_url(B + '/app'); ready(pg)
        expect(pg.locator('#view .ah p')).to_have_text('Kenzy'); expect(pg.locator('.iconbtn .badge')).to_have_text('1'); shot(pg, '05-home')
        open_(pg, '/app/profile'); expect(pg.locator('.profilehead')).to_contain_text('Researcher'); expect(pg.locator('.profilehead')).to_contain_text('Test University')
    ok('03-04 Registration: confirm, terms, show password, category, institution, interests → home', register, pg)

    def login_screens():
        ctx2 = b.new_context(**p.devices[DEV]); ctx2.route('**/fonts.g*/**', lambda r: r.abort()); q = ctx2.new_page()
        q.add_init_script("localStorage.setItem('cs.onboarded','1')"); open_(q, '/app/login'); q.fill('input[name=email]', 'nobody@example.com'); q.fill('input[name=password]', 'Wrong12345X')
        q.click('form[data-form=login] button.primary'); expect(q.locator('.formerr')).to_contain_text('incorrect'); q.screenshot(path=f'{OUT}/03-login.png')
        open_(q, '/app/forgot'); q.fill('input[name=email]', 'nobody@example.com'); q.click('form[data-form=forgot] button'); expect(q.locator('#forgotout')).to_contain_text('administrator'); q.screenshot(path=f'{OUT}/06-forgot.png'); ctx2.close()
    ok('03/05 Login errors and password recovery (no enumeration)', login_screens, pg)

    def discover():
        pg.click('.tabbar a[data-tab=research]'); ready(pg); expect(pg.locator('.chips .chip').first).to_have_text('All'); shot(pg, '07-discover')
        pg.fill('form[data-form=rsearch] input', 'carbon monoxide'); pg.press('form[data-form=rsearch] input', 'Enter'); ready(pg)
        expect(pg).to_have_url(B + '/app/search?q=carbon%20monoxide'); expect(pg.locator('.res')).to_have_count(4); shot(pg, '08-search-results')
        pg.click('button[data-act=filters]'); pg.select_option('#sheet select[name=evidence]', 'verified'); pg.click('#sheet button.primary'); ready(pg)
        expect(pg.locator('.chips .chip.on').first).to_contain_text('verified')
    ok('07-08 Discover, search results, filter sheet, active chips', discover, pg)

    def details():
        open_(pg, '/app/report/20160000593'); expect(pg.locator('h1.dt')).to_contain_text('BASS-II'); shot(pg, '09-report-details')
        pg.click('.detail .topbar button[data-act=save]'); expect(pg.locator('#toast')).to_contain_text('Saved')
        pg.click('button[data-act=dl]'); expect(pg.locator('#toast')).to_contain_text('offline')
        pg.click('button[data-act=seg][data-v=citations]'); expect(pg.locator('.psg').first).to_be_visible()
        pg.click('button[data-act=seg][data-v=overview]')
    ok('09 Research details: save, download for offline, citations', details, pg)

    def assistant():
        pg.click('a[data-act=askreport]'); ready(pg); expect(pg.locator('.scope')).to_contain_text('Combustion of Solids')
        pg.fill('.composer textarea', 'What extinction limits were reported?'); pg.click('.composer .send')
        expect(pg.locator('.msg.ai').first).to_contain_text('Retrieval-only', timeout=15000); expect(pg.locator('.msg.ai .ctx')).to_contain_text('Scoped to report')
        pg.click('button[data-act=unscope]'); pg.locator('.fu .chip').first.click(); expect(pg.locator('.msg.ai')).to_have_count(2, timeout=15000)
        expect(pg).to_have_url(__import__('re').compile(r'/app/assistant/\d+')); shot(pg, '10-ai-assistant')
        pg.click('a[aria-label="Conversation history"]'); ready(pg); expect(pg.locator('.list li')).to_have_count(1)
        with pg.expect_download() as d: pg.click('button[data-act=exportconvid]')
        assert 'What extinction limits were reported?' in open(d.value.path(), encoding='utf-8').read()
    ok('10 AI assistant: report scope, follow-up, history, export', assistant, pg)

    def analysis():
        open_(pg, '/app/report/20150019858'); pg.click('button[data-act=analyze]'); ready(pg)
        for h in ('Research overview', 'Key findings', 'Important variables', 'Scientific implications', 'Evidence quality', 'Limitations', 'Related sources'):
            expect(pg.locator(f'.panel h3:has-text("{h}")')).to_be_visible()
        shot(pg, '11-ai-analysis')
    ok('11 AI research analysis: 7 sections', analysis, pg)

    def library():
        pg.click('.tabbar a[data-tab=workspace]'); ready(pg); expect(pg.locator('#view .ah h1')).to_have_text('MY RESEARCH'); pg.click('a.menuitem:has-text("Evidence Library")'); ready(pg)
        expect(pg.locator('.list li')).to_contain_text('Combustion of Solids'); shot(pg, '12-library')
        pg.click('button[data-act=seg][data-v=images]'); expect(pg.locator('#medgrid .note-inline, #medgrid .tile').first).to_be_visible(timeout=15000)
        pg.click('button[data-act=seg][data-v=downloads]'); expect(pg.locator('.list li')).to_contain_text('Combustion of Solids')
    ok('12 Evidence library: saved, NASA images (honest offline), downloads', library, pg)

    def collections():
        open_(pg, '/app/report/20150019858'); pg.click('button[data-act=addtocol]'); pg.fill('#sheet input[name=name]', 'CO research'); pg.click('#sheet button.primary')
        expect(pg.locator('#toast')).to_contain_text('Added'); open_(pg, '/app/library'); pg.click('button[data-act=seg][data-v=collections]'); pg.click('a:has-text("CO research")'); ready(pg)
        pg.fill('form[data-form=editcol] textarea', 'Carbon monoxide evidence'); pg.fill('form[data-form=editcol] input', 'CO evidence'); pg.click('form[data-form=editcol] button'); ready(pg)
        expect(pg.locator('#view .ah h1')).to_have_text('CO EVIDENCE'); shot(pg, '13-collection')
    ok('13 Collections: create, add, rename, describe', collections, pg)

    def experiments():
        pg.click('.tabbar a[data-tab=experiments]'); ready(pg); shot(pg, '14-experiments')
        open_(pg, '/app/experiments/bass2-smmrf'); expect(pg.locator('.panel h3:has-text("Objective")')).to_be_visible(); expect(pg.locator('.panel:has(h3:text-is("Results"))')).to_contain_text('−2.4% O2')
        pg.click('button[data-act=addcmp]'); shot(pg, '15-experiment-details'); pg.evaluate("window.scrollTo(0, document.body.scrollHeight)"); shot(pg, '17-experiment-results')
    ok('14-15/17 Experiment explorer, details, results', experiments, pg)

    def compare():
        open_(pg, '/app/compare'); pg.check('input[data-id="saffire6-3"]'); ready(pg); expect(pg.locator('#view .ah p')).to_have_text('2 of 4 selected'); shot(pg, '16-compare')
        pg.click('button[data-act=seg][data-v=notes]'); expect(pg.locator('.panel h3:has-text("Why these are hard to compare")')).to_be_visible()
        pg.click('button[data-act=seg][data-v=ai]'); expect(pg.locator('#cmpai .msg')).to_contain_text('Retrieval-only', timeout=15000)
        pg.click('button[data-act=seg][data-v=outcomes]'); expect(pg.locator('.xcard')).to_have_count(2)
        pg.click('button[data-act=seg][data-v=parameters]'); expect(pg.locator('.xcard').first.locator('.var.diff').first).to_be_visible()
    ok('16 Compare: select, parameters, outcomes, notes, AI summary', compare, pg)

    def workspace_notes():
        open_(pg, '/app/workspace'); pg.click('button[data-act=seg][data-v=notes]'); shot(pg, '18-workspace')
        open_(pg, '/app/note/report/20160000593'); pg.fill('#noteed', 'Negative oxygen margin: de-rate 1g limits.'); expect(pg.locator('#notest')).to_contain_text('Saved', timeout=6000); shot(pg, '19-notes-editor')
        open_(pg, '/app/workspace'); pg.click('button[data-act=seg][data-v=notes]'); expect(pg.locator('.panel textarea').first).to_have_value('Negative oxygen margin: de-rate 1g limits.')
    ok('18-19 Workspace and notes editor (autosave persisted)', workspace_notes, pg)

    def learn():
        open_(pg, '/app/learn'); shot(pg, '20-learning'); pg.click('a.btn.primary'); ready(pg); pg.click('button[data-act=complete]'); expect(pg.locator('.tag.good')).to_be_visible()
    ok('20 Learning Studio: guided discovery, completion', learn, pg)

    def notifs_profile():
        open_(pg, '/app/notifications'); expect(pg.locator('.nlist li.unread')).to_have_count(1); shot(pg, '21-notifications')
        pg.click('button[data-act=readall]'); ready(pg); expect(pg.locator('.nlist li.unread')).to_have_count(0)
        open_(pg, '/app/profile'); expect(pg.locator('.profilehead')).to_contain_text('PMMA'); shot(pg, '22-profile')
        open_(pg, '/app/profile/edit'); pg.fill('textarea[name=bio]', 'Computer science student, CTRL+SPACE team.'); pg.click('form[data-form=editprofile] button.primary'); ready(pg)
        expect(pg.locator('.profilehead')).to_contain_text('CTRL+SPACE team'); open_(pg, '/app/profile/edit'); shot(pg, '23-edit-profile')
        open_(pg, '/app/settings'); pg.locator('label.switch:has-text("Replies") input').uncheck(); expect(pg.locator('#toast')).to_contain_text('saved'); shot(pg, '24-settings')
    ok('21-24 Notifications, profile, edit profile, settings', notifs_profile, pg)

    def offline():
        open_(pg, '/app/demo'); expect(pg.locator('.checks')).to_contain_text('Database'); shot(pg, '26-demo')
        open_(pg, '/app/about'); shot(pg, '27-about'); open_(pg, '/app/help'); shot(pg, '28-help')
        open_(pg, '/app/offline'); expect(pg.locator('.list li').first).to_contain_text('Combustion of Solids')
        ctx.set_offline(True); pg.goto(B + '/app/report/20160000593'); ready(pg)
        expect(pg.locator('#offbar')).to_be_visible(); expect(pg.locator('h1.dt')).to_contain_text('BASS-II')
        pg.goto(B + '/app/offline'); ready(pg); expect(pg.locator('.status')).to_contain_text('Offline'); shot(pg, '25-offline')
        ctx.set_offline(False); pg.goto(B + '/app'); ready(pg); expect(pg.locator('#offbar')).to_be_hidden()
    ok('25-28 Offline (downloaded report, banner, reconnect), demo, about, help', offline, pg)

    def nav():
        for t in ('home', 'research', 'assistant', 'experiments', 'workspace'):
            pg.click(f'.tabbar a[data-tab={t}]'); ready(pg); expect(pg.locator(f'.tabbar a[data-tab={t}]')).to_have_attribute('aria-current', 'page')
        pg.go_back(); ready(pg); expect(pg.locator('.tabbar a[data-tab=experiments]')).to_have_attribute('aria-current', 'page')
        small = pg.evaluate("[...document.querySelectorAll('.tabbar a, #view button:not(.cite), #view a.btn, #view a.chip')].filter(e=>{const r=e.getBoundingClientRect();return r.width&&r.height<44}).map(e=>e.className+':'+Math.round(e.getBoundingClientRect().height))")
        assert not small, f'targets under 44px: {small[:5]}'
        cites = pg.evaluate("[...document.querySelectorAll('.cite')].filter(e=>{const r=e.getBoundingClientRect();return r.width&&r.height<24}).length"); assert cites == 0
        assert not pg.evaluate('document.documentElement.scrollWidth > innerWidth')
    ok('Navigation: 5 tabs, active state, back, touch targets, no overflow', nav, pg)

    def upgrade_ai():
        open_(pg, '/app/assistant'); expect(pg.locator('.aistatus')).to_contain_text('Retrieval-only')
        held = []
        pg.route('**/api/assistant/ask', lambda r: held.append(r))                      # hold the request: generation in progress
        pg.fill('.composer textarea', 'What happens to flames at very low airflow?'); pg.click('.composer .send')
        expect(pg.locator('.stopbtn')).to_be_visible(); pg.click('.stopbtn'); expect(pg.locator('.msg.stopped')).to_contain_text('Stopped', timeout=8000)
        expect(pg.locator('.composer .send')).to_be_visible()
        for r in held:
            try: r.abort()
            except Exception: pass
        pg.unroute('**/api/assistant/ask')
        pg.fill('.composer textarea', 'What is the oxygen margin of safety for PMMA rods?'); pg.click('.composer .send')
        card = pg.locator('.msg.ai').last; expect(card.locator('.evtag.src')).to_have_text('Original NASA evidence', timeout=15000)
        card.locator('button[data-act=flimits]').click(); expect(pg.locator('#sheet')).to_contain_text('Evidence coverage notes'); pg.keyboard.press('Escape')
        card.locator('button[data-act=fquestions]').click(); expect(pg.locator('#sheet')).to_contain_text('not findings'); pg.keyboard.press('Escape')
        card.locator('button[data-act=saveans]').click(); expect(pg.locator('#toast')).to_contain_text('Saved to My Research')
        open_(pg, '/app/workspace'); pg.click('button[data-act=seg][data-v=answers]'); expect(pg.locator('.panel h3').first).to_contain_text('oxygen margin of safety')
        open_(pg, '/app/assistant'); pg.fill('.composer textarea', 'What is the oxygen margin of safety for PMMA rods?'); pg.click('.composer .send')
        pg.locator('.msg.ai').last.locator('button[data-act=fcompare]').click(); pg.wait_for_url(B + '/app/compare'); ready(pg)
        expect(pg.locator('#view .ah p')).to_contain_text('of 4 selected')
    ok('AI centerpiece: status, stop generation, evidence labels, limitations, research questions, save, compare from citations', upgrade_ai, pg)

    def upgrade_misc():
        open_(pg, '/app/research'); pg.click('input[data-suggest]'); pg.fill('input[data-suggest]', 'comb'); expect(pg.locator('#sugbox button').first).to_contain_text('Combustion products')
        pg.locator('#sugbox button').first.click(); pg.wait_for_url(__import__('re').compile(r'/app/search\?q=')); ready(pg)
        open_(pg, '/app/settings'); pg.click('button[data-act=theme][data-t=system]'); expect(pg.locator('button[data-act=theme][data-t=system]')).to_have_class(__import__('re').compile('on'))
        ctx2 = b.new_context(**p.devices[DEV]); ctx2.route('**/fonts.g*/**', lambda r: r.abort()); ctx2.route('**/api/**', lambda r: r.fulfill(status=503, body='{}', content_type='application/json')); q = ctx2.new_page()
        q.add_init_script("localStorage.setItem('cs.onboarded','1')"); q.goto(B + '/app'); q.wait_for_selector('#splash', state='detached', timeout=12000)
        expect(q.locator('#offbar')).to_contain_text('Research server unreachable'); ctx2.close()
    ok('Search suggestions, System theme, server-down vs offline state', upgrade_misc, pg)

    def demo_login():
        open_(pg, '/app/profile'); pg.click('button[data-act=logout]'); ready(pg)
        open_(pg, '/app/login')
        expect(pg.locator('.demo-creds')).to_have_count(2)
        pg.click('[data-act=exploredemo]'); pg.wait_for_url(B + '/app'); ready(pg)
        open_(pg, '/app/profile')
        expect(pg.locator('.profilehead')).to_contain_text('Demo'); expect(pg.locator('.profilehead')).to_contain_text('Student')
    ok('Demo access: visible credentials, Explore Demo signs in for real, profile shows Student + Demo badge', demo_login, pg)

    def logout():
        open_(pg, '/app/profile'); pg.click('button[data-act=logout]'); ready(pg); expect(pg.locator('.cta-card')).to_be_visible()
    ok('Sign out', logout, pg)
    b.close()
print(f"\n{sum(r[0] == 'PASS' for r in res)}/{len(res)} passed; page errors: {errs}")
sys.exit(0 if all(r[0] == 'PASS' for r in res) and not errs else 1)

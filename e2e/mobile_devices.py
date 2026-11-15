"""Runs CTRL+SPACE under Chromium MOBILE DEVICE EMULATION (Pixel 7, Galaxy S9+): real viewport, pixel density,
touch input and Android Chrome user agent. This is browser emulation, NOT an Android emulator.
Usage: python e2e/mobile_devices.py BASE_URL ADMIN_EMAIL ADMIN_PASSWORD   -> screenshots in e2e/screenshots/mobile/"""
import os, sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright

B, AE, AP = sys.argv[1], sys.argv[2], sys.argv[3]
OUT = os.path.join(os.path.dirname(__file__), 'screenshots', 'mobile'); os.makedirs(OUT, exist_ok=True)
log, errs = [], []
def ok(name, cond=True):
    log.append(('PASS' if cond else 'FAIL', name)); print(log[-1][0], name, flush=True)


def ready(pg, path):
    pg.goto(B + path); pg.wait_for_selector('#splash', state='detached', timeout=10000)


with sync_playwright() as p:
    b = p.chromium.launch()
    for dev in ('Pixel 7', 'Galaxy S9+'):
        ctx = b.new_context(**p.devices[dev]); ctx.route('**/fonts.g*/**', lambda r: r.abort()); pg = ctx.new_page()
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('console', lambda m: m.type == 'error' and 'fonts.g' not in m.text and 'ERR_FAILED' not in m.text and errs.append(m.text))
        tag = dev.replace(' ', '').replace('+', 'plus')
        pg.goto(B + '/'); pg.wait_for_timeout(250); pg.screenshot(path=f'{OUT}/{tag}-1-launch.png')
        pg.wait_for_selector('#splash', state='detached', timeout=10000); pg.screenshot(path=f'{OUT}/{tag}-2-home.png')
        touch = pg.evaluate("navigator.maxTouchPoints > 0"); ua = pg.evaluate('navigator.userAgent')[:58]
        log.append(('INFO', f"{dev}: viewport {pg.evaluate('innerWidth')}x{pg.evaluate('innerHeight')} CSS px, DPR {pg.evaluate('devicePixelRatio')}, touch={touch}, UA: {ua}..."))
        ok(f'{dev}: launch screen → dashboard', pg.inner_text('main h1') == 'Explore the Science of Fire in Space')
        pg.tap('.top .menu'); pg.wait_for_timeout(350); pg.screenshot(path=f'{OUT}/{tag}-3-menu.png')
        ok(f'{dev}: menu drawer opens on tap', pg.evaluate("document.body.classList.contains('nav-open')"))
        pg.tap('.side nav a:has-text("Research Discovery")'); pg.wait_for_selector('.rcard')
        pg.fill('form[data-form=disc] input[name=q]', 'oxygen'); pg.tap('form[data-form=disc] button.fire'); pg.wait_for_timeout(500)
        pg.screenshot(path=f'{OUT}/{tag}-4-discovery.png'); ok(f'{dev}: search by tap', 'for “oxygen”' in pg.inner_text('.count'))
        pg.locator('.rcard a:has-text("Open report")').first.tap(); pg.wait_for_selector('.passage'); pg.screenshot(path=f'{OUT}/{tag}-5-report.png')
        ok(f'{dev}: report details with evidence', pg.url.startswith(B + '/library/'))
        ready(pg, '/experiments')
        centre = lambda sel: pg.eval_on_selector(sel, "e => e.scrollIntoView({block: 'center'})")   # where a thumb would tap
        centre('input[data-id="saffire6-3"]'); pg.locator('input[data-id="saffire6-3"]').tap(); pg.wait_for_timeout(400)
        centre('input[data-id="saffire6-4"]'); y = pg.evaluate('scrollY'); pg.locator('input[data-id="saffire6-4"]').tap(); pg.wait_for_timeout(400)
        ok(f'{dev}: ticking Compare keeps scroll position', abs(pg.evaluate('scrollY') - y) < 400)
        pg.tap('.tray a'); pg.wait_for_selector('table.cmp'); pg.screenshot(path=f'{OUT}/{tag}-6-compare.png')
        ok(f'{dev}: compare two experiments by tap', pg.locator('table.cmp').count() == 2)
        ready(pg, '/assistant')
        pg.fill('#aq', 'What factors influence flame extinction?'); pg.tap('form[data-form=ask] button'); pg.wait_for_selector('#askout .passage', timeout=15000)
        pg.screenshot(path=f'{OUT}/{tag}-7-assistant.png'); ok(f'{dev}: assistant returns cited evidence')
        ready(pg, '/login'); pg.fill('input[name=email]', AE); pg.fill('input[name=password]', AP); pg.tap('form[data-form=login] button')
        pg.wait_for_selector('.kpis'); pg.screenshot(path=f'{OUT}/{tag}-8-admin.png'); ok(f'{dev}: sign in → admin dashboard')
        wide = []
        for r in ('/', '/research', '/library/20150019858', '/experiments/bass2-gel', '/compare', '/my-research', '/studio/flow-and-extinction', '/challenges/products', '/community', '/settings', '/admin', '/gaps', '/demo'):
            ready(pg, r); pg.wait_for_timeout(250)
            if pg.evaluate('document.documentElement.scrollWidth > innerWidth || innerWidth > screen.width'):
                wide.append(r)
        ok(f'{dev}: no sideways scrolling or zoom-out on 13 screens', not wide); wide and log.append(('INFO', f'overflowing: {wide}'))
        small = pg.evaluate("[...document.querySelectorAll('main button, main a.btn, main select, .top .btn')].filter(e => { const r = e.getBoundingClientRect(); return r.width && r.height < 32; }).map(e => e.textContent.trim().slice(0, 20))")
        log.append(('INFO', f'{dev}: controls under 32px tall on Admin: {len(small)} {small[:6]}'))
        pg.tap('#acct button:has-text("Sign out")'); ctx.close()
    ctx = b.new_context(); m = ctx.new_page().request.get(B + '/manifest.webmanifest').json()
    sizes = {i['sizes'] for i in m['icons']}; ok('installable-app manifest (standalone, 192 + 512 icons, maskable icon)', m['display'] == 'standalone' and {'192x192', '512x512'} <= sizes and any(i.get('purpose') == 'maskable' for i in m['icons'])); ctx.close(); b.close()
for s, n in log:
    print(f'{s:4}  {n}')
print('console/page errors:', errs)
sys.exit(0 if all(s != 'FAIL' for s, _ in log) and not errs else 1)

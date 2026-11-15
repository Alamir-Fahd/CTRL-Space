"""Installable-app (PWA) checks on a Pixel 7 profile. Usage: python e2e/pwa_test.py BASE_URL"""
import sys
from playwright.sync_api import sync_playwright
B = sys.argv[1]; res, errs = [], []
ok = lambda n, c, d='': (res.append(('PASS' if c else 'FAIL', n, d)), print(res[-1][0], n, d, flush=True))
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(**p.devices['Pixel 7']); ctx.route('**/fonts.g*/**', lambda r: r.abort()); pg = ctx.new_page()
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(B + '/'); pg.wait_for_selector('#splash', state='detached'); pg.wait_for_timeout(1500); pg.reload(); pg.wait_for_selector('#splash', state='detached'); pg.wait_for_timeout(500)
    ok('Service worker controls the app', pg.evaluate('!!navigator.serviceWorker.controller'))
    cdp = ctx.new_cdp_session(pg); inst = cdp.send('Page.getInstallabilityErrors')['installabilityErrors']
    ok('Chromium installability check: no errors', inst == [], str(inst))
    ok('Manifest parses cleanly', not cdp.send('Page.getAppManifest').get('errors'))
    ok('Bottom tab bar (5 tabs)', pg.locator('.tabbar a').count() == 5 and pg.locator('.tabbar').is_visible())
    pg.locator('.tabbar a:has-text("Research")').tap(); pg.wait_for_selector('.rcard')
    pg.locator('.rcard', has_text='Results from On-Board').locator('a:has-text("Open report")').tap(); pg.wait_for_selector('.passage'); pg.wait_for_timeout(500)
    ctx.set_offline(True)
    pg.goto(B + '/library/20150019858'); pg.wait_for_selector('#splash', state='detached', timeout=10000); pg.wait_for_selector('.passage', timeout=5000)
    ok('Offline: opens straight to a saved report', pg.locator('.passage').count() == 11)
    ok('Offline: banner shown', pg.locator('#offline').is_visible())
    pg.goto(B + '/library/20160000593'); pg.wait_for_selector('#splash', state='detached', timeout=10000); pg.wait_for_timeout(600)
    ok('Offline: unvisited report gives an honest error', pg.locator('main .err').count() == 1)
    ctx.set_offline(False); pg.reload(); pg.wait_for_selector('#splash', state='detached'); pg.wait_for_selector('.passage')
    ok('Back online: banner hidden', pg.locator('#offline').is_hidden())
    pg.goto(B + '/settings'); pg.wait_for_selector('#splash', state='detached'); pg.wait_for_timeout(300)
    ok('Settings shows install instructions when signed out', pg.locator('.panel.mobileapp').is_visible())
    b.close()
print('page errors:', errs); sys.exit(0 if all(r[0] == 'PASS' for r in res) and not errs else 1)

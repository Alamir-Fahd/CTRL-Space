"""Arabic (RTL) journeys for the mobile app. Usage: python e2e/mobile_ar_test.py BASE_URL"""
import os, sys, time
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import expect, sync_playwright
B = sys.argv[1]; OUT = os.path.join(os.path.dirname(__file__), 'screenshots', 'app', 'arabic'); os.makedirs(OUT, exist_ok=True)
res, errs = [], []; ST = str(int(time.time())); PW = 'FlameSpread2026'
def ok(n, f):
    try: f(); res.append(('PASS', n)); print('PASS', n, flush=True)
    except Exception as e: res.append(('FAIL', n)); print('FAIL', n, str(e).splitlines()[0][:160], flush=True)
def ready(pg): pg.wait_for_selector('#splash', state='detached', timeout=10000); pg.wait_for_selector('#view > :not(.pad)', timeout=10000); pg.wait_for_timeout(500)
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(**p.devices['iPhone 14']); ctx.route('**/fonts.g*/**', lambda r: r.abort()); pg = ctx.new_page()
    pg.on('pageerror', lambda e: errs.append(str(e)))
    def switch():
        pg.goto(B + '/app'); ready(pg); expect(pg).to_have_url(B + '/app/welcome')
        pg.click('.langsw button[data-l=ar]'); ready(pg)
        expect(pg.locator('html')).to_have_attribute('dir', 'rtl'); expect(pg.locator('.slide h1').first).to_have_text('مرحباً بك في CTRL+SPACE')
        expect(pg.locator('#onbnext')).to_have_text('التالي'); pg.screenshot(path=f'{OUT}/ar-02-onboarding.png'); pg.click('button[data-act=onbskip]'); ready(pg)
    ok('Switch to Arabic from onboarding: RTL + translated slides', switch)
    def register():
        pg.goto(B + '/app/register'); ready(pg); expect(pg.locator('h1.t')).to_have_text('إنشاء حساب')
        pg.fill('input[name=name]', 'كنزي'); pg.fill('input[name=email]', f'ar{ST}@example.com'); pg.fill('input[name=password]', PW); pg.fill('input[name=confirm]', PW + 'x')
        pg.click('form[data-form=register] button.primary'); expect(pg.locator('[data-for=confirm]')).to_have_text('كلمتا المرور غير متطابقتين.')
        pg.fill('input[name=confirm]', PW); pg.check('input[name=terms]'); pg.click('form[data-form=register] button.primary'); pg.wait_for_url(B + '/app'); ready(pg)
        expect(pg.locator('.tabbar a[data-tab=research] span')).to_have_text('استكشف'); pg.screenshot(path=f'{OUT}/ar-05-home.png')
    ok('Arabic registration: validation message, account created, Arabic tab bar', register)
    def assistant():
        pg.click('.tabbar a[data-tab=assistant]'); ready(pg); expect(pg.locator('.chatempty .note-inline')).to_contain_text('بالإنجليزية')
        pg.fill('.composer textarea', 'What happens to flames at very low airflow?'); pg.click('.composer .send')
        expect(pg.locator('.msg.ai .mode')).to_contain_text('استرجاع فقط', timeout=15000); expect(pg.locator('.msg.ai h4').first).to_have_text('النتائج المُبلّغ عنها')
        expect(pg.locator('.msg.ai blockquote, .msg.ai .q').first).to_contain_text('flow')       # NASA evidence stays verbatim English
        pg.screenshot(path=f'{OUT}/ar-10-assistant.png')
    ok('Assistant in Arabic: labels translated, NASA evidence verbatim', assistant)
    def compare():
        pg.evaluate("sessionStorage.setItem('cs.cmp', JSON.stringify(['bass2-smmrf','saffire6-3']))"); pg.goto(B + '/app/compare'); ready(pg)
        expect(pg.locator('#view .ah p')).to_have_text('تم اختيار 2 من 4'); pg.click('button[data-act=seg][data-v=notes]'); pg.wait_for_timeout(400)
        expect(pg.locator('.panel h3').first).to_have_text('لماذا تصعب مقارنتها'); expect(pg.locator('.panel li').first).to_contain_text('مواد مختلفة')
        assert not pg.evaluate('document.documentElement.scrollWidth > innerWidth'); pg.screenshot(path=f'{OUT}/ar-16-compare.png')
    ok('Compare in Arabic: count, notes, no overflow in RTL', compare)
    def back():
        pg.goto(B + '/app/settings'); ready(pg); pg.screenshot(path=f'{OUT}/ar-24-settings.png'); pg.click('button[data-act=lang][data-l=en]'); ready(pg)
        expect(pg.locator('html')).to_have_attribute('dir', 'ltr'); expect(pg.locator('#view .ah h1')).to_have_text('SETTINGS')
    ok('Switch back to English from Settings', back)
    b.close()
print(f"\n{sum(r[0] == 'PASS' for r in res)}/{len(res)} passed; page errors: {errs}")
sys.exit(0 if all(r[0] == 'PASS' for r in res) and not errs else 1)

"""Viewport, accessibility (WCAG 2.2 AA heuristics) and performance audit of the mobile app.
Usage: python e2e/mobile_audit.py BASE_URL  -> reports/mobile_audit.json"""
import json, os, sys, time
from playwright.sync_api import sync_playwright
B = sys.argv[1]; PART = sys.argv[2] if len(sys.argv) > 2 else 'all'
ROUTES = ['/app', '/app/research', '/app/search?q=PMMA', '/app/report/20150019858', '/app/assistant', '/app/experiments', '/app/experiments/bass2-gel', '/app/compare',
          '/app/workspace', '/app/library', '/app/learn', '/app/community', '/app/settings', '/app/offline', '/app/login', '/app/about']
VIEWS = [('320', 320, 640), ('360', 360, 740), ('375', 375, 667), ('390', 390, 844), ('412', 412, 915), ('430', 430, 932), ('tablet', 820, 1180), ('desktop', 1280, 800), ('landscape', 844, 390)]
A11Y = r"""(() => {
  const lum = c => { const m = c.match(/[\d.]+/g); if (!m) return null; const [r, g, b] = m.slice(0, 3).map(v => { v /= 255; return v <= .03928 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4; }); return .2126 * r + .7152 * g + .0722 * b; };
  const bgOf = el => { for (let e = el; e; e = e.parentElement) { const s = getComputedStyle(e); if (s.backgroundImage !== 'none') return null; const m = s.backgroundColor.match(/[\d.]+/g); if (m && (m.length < 4 || +m[3] > .9)) return s.backgroundColor; } return getComputedStyle(document.body).backgroundColor; };
  const vis = e => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.opacity !== '0'; };
  const name = e => (e.getAttribute('aria-label') || e.textContent || e.getAttribute('title') || '').trim();
  const out = {unnamed: [], unlabeled: [], noalt: [], contrast: [], h1: !!document.querySelector('#view h1, #view h2')};
  document.querySelectorAll('#view button, #view a, .tabbar a').forEach(e => { if (vis(e) && !name(e)) out.unnamed.push(e.outerHTML.slice(0, 80)); });
  document.querySelectorAll('#view input, #view textarea, #view select').forEach(e => { if (!vis(e) || e.type === 'hidden') return; const l = e.closest('label') || (e.id && document.querySelector(`label[for="${e.id}"]`)) || e.getAttribute('aria-label'); if (!l) out.unlabeled.push(e.outerHTML.slice(0, 80)); });
  document.querySelectorAll('#view img').forEach(e => { if (!e.hasAttribute('alt')) out.noalt.push(e.src.slice(-40)); });
  const seen = new Set();
  document.querySelectorAll('#view *, .tabbar *').forEach(e => {
    if (!vis(e) || ![...e.childNodes].some(n => n.nodeType === 3 && n.nodeValue.trim())) return;
    const s = getComputedStyle(e), bg = bgOf(e); if (!bg) return;
    const f = lum(s.color), b = lum(bg); if (f === null || b === null) return;
    const ratio = (Math.max(f, b) + .05) / (Math.min(f, b) + .05), size = parseFloat(s.fontSize), large = size >= 24 || (size >= 18.66 && +s.fontWeight >= 700);
    if (ratio < (large ? 3 : 4.5)) { const k = e.className + '|' + s.color; if (!seen.has(k)) { seen.add(k); out.contrast.push({el: (e.tagName + '.' + e.className).slice(0, 50), text: e.textContent.trim().slice(0, 30), ratio: +ratio.toFixed(2)}); } }
  });
  return out;
})()"""
OUTF = f'reports/mobile_audit_{PART}.json'
res = {'run_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'viewports': {}, 'a11y': {}, 'perf': {}}
def ready(pg): pg.wait_for_selector('#splash', state='detached', timeout=12000); pg.wait_for_selector('#view > :not(.pad)', timeout=12000); pg.wait_for_timeout(350)
with sync_playwright() as p:
    b = p.chromium.launch()
    # ---- performance: cold and warm start on a phone profile
    if PART in ('all', 'perf'):
        ctx = b.new_context(**p.devices['Pixel 7']); ctx.route('**/fonts.g*/**', lambda r: r.abort()); pg = ctx.new_page()
        pg.add_init_script("localStorage.setItem('cs.onboarded','1')")
        for label in ('cold', 'warm'):
            t0 = time.time(); pg.goto(B + '/app'); ready(pg); usable = round((time.time() - t0) * 1000)
            nav = pg.evaluate("(() => { const n = performance.getEntriesByType('navigation')[0]; const r = performance.getEntriesByType('resource'); return {ttfb: Math.round(n.responseStart), dcl: Math.round(n.domContentLoadedEventEnd), load: Math.round(n.loadEventEnd), js_kb: Math.round(r.filter(x => x.name.endsWith('.js')).reduce((a, x) => a + (x.decodedBodySize || 0), 0) / 1024), css_kb: Math.round(r.filter(x => x.name.endsWith('.css')).reduce((a, x) => a + (x.decodedBodySize || 0), 0) / 1024), img_kb: Math.round(r.filter(x => /\\.(jpg|png)$/.test(x.name)).reduce((a, x) => a + (x.decodedBodySize || 0), 0) / 1024)}; })()")
            res['perf'][label] = {**nav, 'first_screen_usable_ms_incl_splash': usable}
            pg.wait_for_timeout(1500)
        t0 = time.time(); pg.click('.tabbar a[data-tab=research]'); pg.wait_for_selector('.rrow'); res['perf']['tab_switch_research_ms'] = round((time.time() - t0) * 1000)
        t0 = time.time(); pg.goto(B + '/app/assistant'); ready(pg); pg.fill('.composer textarea', 'What happens to flames at very low airflow?'); pg.click('.composer .send'); pg.wait_for_selector('.msg.ai')
        res['perf']['assistant_answer_ms_retrieval_only'] = round((time.time() - t0) * 1000)
        ctx.close()
    if PART in ('all', 'viewports'):
        for name, w, h in VIEWS:
            c = b.new_context(viewport={'width': w, 'height': h}, is_mobile=w < 700, has_touch=w < 900, device_scale_factor=2); c.route('**/fonts.g*/**', lambda r: r.abort()); q = c.new_page()
            q.add_init_script("localStorage.setItem('cs.onboarded','1')"); bad = []
            for r in ROUTES:
                q.goto(B + r); ready(q)
                if q.evaluate('document.documentElement.scrollWidth > innerWidth + 1'): bad.append(r)
            res['viewports'][name] = {'size': f'{w}x{h}', 'routes': len(ROUTES), 'horizontal_overflow': bad}; c.close()
    if PART in ('all', 'a11y'):
        for theme in ('dark', 'light'):
            c = b.new_context(**p.devices['iPhone 14']); c.route('**/fonts.g*/**', lambda r: r.abort()); q = c.new_page()
            q.add_init_script(f"localStorage.setItem('cs.onboarded','1'); localStorage.setItem('cs.mtheme','{theme}')")
            agg = {'unnamed': [], 'unlabeled': [], 'noalt': [], 'contrast': [], 'missing_heading': []}
            for r in ROUTES:
                q.goto(B + r); ready(q); x = q.evaluate(A11Y)
                for k in ('unnamed', 'unlabeled', 'noalt'): agg[k] += [f'{r}: {v}' for v in x[k]]
                agg['contrast'] += [{**v, 'route': r} for v in x['contrast']]
                if not x['h1']: agg['missing_heading'].append(r)
            rm = q.evaluate("matchMedia('(prefers-reduced-motion: reduce)').matches")
            res['a11y'][theme] = {k: (v if k != 'contrast' else v[:40]) for k, v in agg.items()} | {'contrast_failures': len(agg['contrast'])}
            c.close()
    b.close()
os.makedirs('reports', exist_ok=True); json.dump(res, open(OUTF, 'w'), indent=1)
print(json.dumps({'perf': res['perf'], 'viewports': {k: v['horizontal_overflow'] for k, v in res['viewports'].items()},
                  'a11y': {t: {k: (len(v) if isinstance(v, list) else v) for k, v in a.items()} for t, a in res['a11y'].items()}}, indent=1))

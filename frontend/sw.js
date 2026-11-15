/* CTRL+SPACE service worker: installable app shell + offline reading of public research data.
   Never caches personal or admin data, never caches POST requests. */
const VERSION = 'ctrlspace-v5.10.0';
const SHELL = ['/', '/index.html', '/css/app.css', '/js/app.js', '/js/api.js', '/js/ui.js', '/js/views-research.js', '/js/views-platform.js',
  '/js/views-extra.js', '/app', '/app/index.html', '/app/app.css', '/app/js/main.js', '/app/js/core.js', '/app/js/screens-a.js', '/app/js/screens-b.js', '/app/js/screens-c.js', '/app/js/screens-d.js', '/app/js/screens-e.js', '/app/js/i18n.js', '/assets/hero.jpg', '/assets/icon-192.png', '/assets/icon-512.png', '/assets/icon-maskable-512.png', '/manifest.webmanifest'];
const PUBLIC_API = /^\/api\/(stats|reports|experiments|lessons|search|gaps|rooms|media|psi|impact|challenges|community)(\/|\?|$)/;

self.addEventListener('install', e => e.waitUntil(caches.open(VERSION + '-shell').then(c => c.addAll(SHELL)).then(() => self.skipWaiting())));
self.addEventListener('activate', e => e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => !k.startsWith(VERSION)).map(k => caches.delete(k)))).then(() => self.clients.claim())));
self.addEventListener('message', e => { if (e.data === 'clear-data') caches.delete(VERSION + '-data'); });

self.addEventListener('fetch', e => {
  const req = e.request, url = new URL(req.url);
  if (req.method !== 'GET' || url.origin !== location.origin) return;
  if (req.mode === 'navigate') {                                   // any app route -> app shell (network first)
    e.respondWith(fetch(req).catch(() => caches.match(url.pathname.startsWith('/app') ? '/app/index.html' : '/index.html')));
    return;
  }
  if (url.pathname.startsWith('/api/')) {
    if (!PUBLIC_API.test(url.pathname + url.search)) return;      // personal/admin/auth: network only
    e.respondWith(fetch(req).then(res => {
      if (res.ok) { const copy = res.clone(); caches.open(VERSION + '-data').then(c => c.put(req, copy)); }
      return res;
    }).catch(async () => {
      const hit = await caches.match(req);
      if (!hit) throw new Error('offline');
      const h = new Headers(hit.headers); h.set('X-CTRLSPACE-Offline', '1');
      return new Response(await hit.blob(), {status: hit.status, headers: h});
    }));
    return;
  }
  e.respondWith(caches.match(req).then(hit => hit || fetch(req).then(res => {          // static: cache first
    if (res.ok) { const copy = res.clone(); caches.open(VERSION + '-shell').then(c => c.put(req, copy)); }
    return res;
  })));
});

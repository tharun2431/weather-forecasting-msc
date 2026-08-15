const CACHE = 'deepweather-v9';
const ASSETS = ['./','./index.html','./styles.css','./app.js','./ui.js','./wx-visuals.js','./manifest.json',
                './scaler.json','./lstm_model.onnx','./icon-192.png','./icon-512.png'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks =>
    Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))
  ).then(() => self.clients.claim()));
});

self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  // live weather is always fetched fresh, never served stale from cache
  if (url.hostname.endsWith('open-meteo.com')) return;

  // The ONNX runtime is loaded from a CDN and was never in the precache list, so
  // inference - the one thing this app claims to do offline - could not run
  // without a network. Cache it on first fetch, serve from cache thereafter.
  if (url.hostname.endsWith('jsdelivr.net')) {
    e.respondWith(
      caches.match(e.request).then(hit => hit || fetch(e.request).then(res => {
        if (res && (res.ok || res.type === 'opaque')) {
          const copy = res.clone();
          caches.open(CACHE).then(c => c.put(e.request, copy));
        }
        return res;
      }))
    );
    return;
  }
  // ignoreSearch so cache-busting query strings (app.js?v=12) still match offline
  e.respondWith(
    caches.match(e.request, { ignoreSearch: true }).then(hit => hit || fetch(e.request))
  );
});

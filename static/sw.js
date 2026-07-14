const CACHE_NAME = 'laplacian-v11';
const STATIC_ASSETS = [
  '/static/style.css',
  '/static/enhancements.css',
  '/static/script.js',
  '/static/ui-enhancements.js',
  '/static/lap favivon.png',
  '/static/New lap logo.png'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(STATIC_ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', event => {
  // Network-first for HTML navigation and API calls so auth redirects always work
  if (event.request.mode === 'navigate' || event.request.url.includes('/api/')) {
    event.respondWith(
      fetch(event.request).catch(() => caches.match(event.request))
    );
  } else {
    // Cache-first for static assets only
    event.respondWith(
      caches.match(event.request).then(cached => cached || fetch(event.request))
    );
  }
});

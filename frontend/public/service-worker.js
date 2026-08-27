const CACHE_NAME = 'docofhome-shell-1.7.13.1'
self.addEventListener('install', () => self.skipWaiting())
self.addEventListener('activate', (event) => event.waitUntil(
  caches.keys().then((keys) => Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))))
    .then(() => self.clients.claim())
))
// Network-first and no runtime response cache: updates remain immediately visible.
self.addEventListener('fetch', (event) => {
  if (event.request.method === 'GET' && event.request.mode === 'navigate') event.respondWith(fetch(event.request))
})

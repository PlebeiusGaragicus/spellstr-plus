/* Spellstr Service Worker - manifest-driven offline cache */
// Build stamp; updated by gen_assets_manifest.sh during deploy
const SW_BUILD = "20250901T001857Z";
const MANIFEST_URL = '/assets-manifest.json';
const RUNTIME_CACHE = 'spellstr-runtime-v1';
const APP_CACHE_PREFIX = 'spellstr-';

// Utility: fetch manifest bypassing HTTP cache
async function loadManifest() {
  const res = await fetch(MANIFEST_URL, { cache: 'no-store' });
  if (!res.ok) throw new Error('manifest fetch failed');
  return res.json();
}

function cacheNameFrom(manifest) {
  const v = (manifest && manifest.version) ? String(manifest.version) : 'v0';
  return `${APP_CACHE_PREFIX}${v}`;
}

async function preCacheAll(cacheName, files) {
  const cache = await caches.open(cacheName);
  const urls = Array.from(new Set(files.map(f => f.url)))
    .filter(u => u !== '/service-worker.js'); // never precache the SW script itself
  await Promise.all(urls.map(async (u) => {
    try {
      const res = await fetch(u, { cache: 'no-store' });
      if (res && (res.ok || res.type === 'opaque')) {
        await cache.put(u, res.clone());
      }
    } catch (_) { /* ignore single fetch failures */ }
  }));
}

self.addEventListener('install', (event) => {
  event.waitUntil((async () => {
    try {
      const manifest = await loadManifest();
      const cacheName = cacheNameFrom(manifest);
      await preCacheAll(cacheName, manifest.files || []);
    } catch (_) { /* install continues even if manifest not available */ }
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    try {
      // Get current cache name from manifest and delete old app caches
      const manifest = await loadManifest();
      const keep = cacheNameFrom(manifest);
      const keys = await caches.keys();
      await Promise.all(keys.map((k) => {
        if (k.startsWith(APP_CACHE_PREFIX) && k !== keep) {
          return caches.delete(k);
        }
      }));
    } catch (_) { /* continue activation */ }
    await self.clients.claim();
  })());
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);
  const sameOrigin = url.origin === self.location.origin;

  // Always bypass SW for the SW script and the assets manifest
  if (sameOrigin && (url.pathname === '/service-worker.js' || url.pathname === '/assets-manifest.json')) {
    event.respondWith(fetch(req, { cache: 'no-store' }));
    return;
  }

  // Navigations: network-first, fallback to cached index.html
  if (req.mode === 'navigate') {
    event.respondWith((async () => {
      try {
        return await fetch(req, { cache: 'no-store' });
      } catch (_) {
        // Fallback to cached /index.html from any app cache
        const keys = await caches.keys();
        for (const k of keys) {
          if (k.startsWith(APP_CACHE_PREFIX)) {
            const cache = await caches.open(k);
            const cached = await cache.match('/index.html');
            if (cached) return cached;
          }
        }
        return Response.error();
      }
    })());
    return;
  }

  // Same-origin assets/data: cache-first with network fallback
  if (sameOrigin) {
    event.respondWith((async () => {
      const cached = await caches.match(req);
      if (cached) return cached;
      try {
        const res = await fetch(req);
        if (res && res.ok) {
          try {
            const runtime = await caches.open(RUNTIME_CACHE);
            await runtime.put(req, res.clone());
          } catch (_) {}
        }
        return res;
      } catch (_) {
        // Do not return HTML for asset requests; return a plain-text offline response
        return new Response('Offline', { status: 503, statusText: 'Offline', headers: { 'Content-Type': 'text/plain' } });
      }
    })());
  }
});

// Optional message to allow future manual update flows
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

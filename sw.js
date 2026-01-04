// sw.js - Advanced offline support for Bimalism coaching site (2026 style)
// Current cache version - change this number when you update content!

const CACHE_VERSION = 'bimalism-v2026-1-2';
const CACHE_SHELL     = `shell-${CACHE_VERSION}`;
const CACHE_PAGES     = `pages-${CACHE_VERSION}`;
const CACHE_ASSETS    = `assets-${CACHE_VERSION}`;

const OFFLINE_PAGE = '/offline.html';

// Files to precache (critical app shell)
const PRECACHE_FILES = [
  '/',
  '/index.html',
  '/Bimalismlogo.png',
  '/logo1.png',
  '/manifest.json',           // if you added it
  // Add other important pages here when they exist:
  // '/neet.html',
  // '/jee.html',
  // '/tips.html',
  // '/settings.html',
  // etc.
];

// Install event → precache critical files
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_SHELL)
      .then((cache) => cache.addAll(PRECACHE_FILES))
      .then(() => self.skipWaiting())   // Activate new SW immediately
  );
});

// Activate → clean old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.filter((name) => {
          return name !== CACHE_SHELL &&
                 name !== CACHE_PAGES &&
                 name !== CACHE_ASSETS;
        }).map((name) => caches.delete(name))
      );
    }).then(() => self.clients.claim())
  );
});

// Main fetch handler
self.addEventListener('fetch', (event) => {
  // Skip non-GET requests and dev tools
  if (event.request.method !== 'GET' || 
      event.request.url.includes('chrome-extension') ||
      event.request.url.includes('devtools')) {
    return;
  }

  const url = new URL(event.request.url);

  // A) Navigation requests → Stale While Revalidate (great UX)
  if (event.request.mode === 'navigate') {
    event.respondWith(
      caches.open(CACHE_PAGES).then((cache) => {
        return cache.match(event.request).then((cachedResponse) => {
          const fetchPromise = fetch(event.request).then((networkResponse) => {
            // Update cache for next time (don't cache error responses)
            if (networkResponse.ok) {
              cache.put(event.request, networkResponse.clone());
            }
            return networkResponse;
          }).catch(() => {
            // Network failed → use cache or fallback
            return cachedResponse || caches.match(OFFLINE_PAGE);
          });

          // Return from cache immediately if available, otherwise wait for network
          return cachedResponse || fetchPromise;
        });
      })
    );
    return;
  }

  // B) Static assets (images, styles, fonts) → Cache First
  if (event.request.destination === 'image' ||
      event.request.destination === 'style' ||
      event.request.destination === 'font' ||
      event.request.destination === 'script') {
    event.respondWith(
      caches.match(event.request).then((cachedResponse) => {
        return cachedResponse || fetch(event.request).then((networkResponse) => {
          // Cache successful responses
          if (networkResponse && networkResponse.status === 200) {
            caches.open(CACHE_ASSETS).then((cache) => {
              cache.put(event.request, networkResponse.clone());
            });
          }
          return networkResponse;
        }).catch(() => cachedResponse); // offline → cached version
      })
    );
    return;
  }

  // C) Everything else → Network first with cache fallback
  event.respondWith(
    fetch(event.request)
      .catch(() => caches.match(event.request) || caches.match(OFFLINE_PAGE))
  );
});
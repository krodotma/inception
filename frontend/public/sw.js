/* Service Worker for Inception PWA - Stage 3.5 Steps 431-440 */

const CACHE_NAME = 'inception-v1';
const OFFLINE_URL = '/offline.html';

const PRECACHE_ASSETS = [
    '/',
    '/index.html',
    '/app/graph.js',
    '/app/terminal.js',
    '/app/state.js',
    '/styles/main.css',
    '/offline.html',
];

// Install - cache assets
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(PRECACHE_ASSETS);
        })
    );
    self.skipWaiting();
});

// Activate - clean old caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) => {
            return Promise.all(
                keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key))
            );
        })
    );
    self.clients.claim();
});

// Fetch - network first, fallback to cache
self.addEventListener('fetch', (event) => {
    // Skip API requests
    if (event.request.url.includes('/api/') || event.request.url.includes('/ws/')) {
        return;
    }

    event.respondWith(
        fetch(event.request)
            .then((response) => {
                // Clone and cache successful responses
                if (response.ok) {
                    const clone = response.clone();
                    caches.open(CACHE_NAME).then((cache) => {
                        cache.put(event.request, clone);
                    });
                }
                return response;
            })
            .catch(() => {
                // Fallback to cache
                return caches.match(event.request).then((cached) => {
                    if (cached) return cached;
                    // Return offline page for navigation
                    if (event.request.mode === 'navigate') {
                        return caches.match(OFFLINE_URL);
                    }
                    return new Response('Offline', { status: 503 });
                });
            })
    );
});

// Background sync for offline ingestion
self.addEventListener('sync', (event) => {
    if (event.tag === 'sync-ingestion') {
        event.waitUntil(syncPendingIngestion());
    }
});

async function syncPendingIngestion() {
    const pending = await getPendingIngestion();
    for (const item of pending) {
        try {
            await fetch('/api/ingest', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(item),
            });
            await removePendingIngestion(item.id);
        } catch (e) {
            console.warn('Sync failed, will retry:', e);
        }
    }
}

// IndexedDB helpers for offline queue
async function getPendingIngestion() {
    // Stub - would use IndexedDB
    return [];
}

async function removePendingIngestion(id) {
    // Stub - would use IndexedDB
}

/**
 * DARKSULFOCUS - Service Worker for Offline Functionality
 * Caches pages, assets, and enables offline access
 */

const CACHE_NAME = 'darksulfocus-v2';
const STATIC_CACHE = 'darksulfocus-static-v2';
const DYNAMIC_CACHE = 'darksulfocus-dynamic-v2';

// Files to cache immediately
const CORE_CACHE_FILES = [
    '/',
    '/home',
    '/profile',
    '/progress', 
    '/help',
    '/login',
    '/register',
    '/static/css/style.css',
    '/static/js/app.js',
    '/static/js/timer.js',
    '/static/js/offline.js',
    '/static/img/favicon.png',
    '/offline.html'
];

// External resources to cache
const EXTERNAL_CACHE_FILES = [
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
    'https://cdn.jsdelivr.net/npm/chart.js'
];

// Install event - cache core files
self.addEventListener('install', event => {
    console.log('Service Worker installing...');
    event.waitUntil(
        Promise.all([
            // Cache core files
            caches.open(STATIC_CACHE).then(cache => {
                console.log('Caching core files...');
                return cache.addAll(CORE_CACHE_FILES.concat(EXTERNAL_CACHE_FILES));
            })
        ])
    );
    self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
    console.log('Service Worker activating...');
    event.waitUntil(
        caches.keys().then(keys => {
            return Promise.all(
                keys.filter(key => 
                    key !== STATIC_CACHE && 
                    key !== DYNAMIC_CACHE
                ).map(key => caches.delete(key))
            );
        })
    );
    self.clients.claim();
});

// Fetch event - serve from cache when offline
self.addEventListener('fetch', event => {
    const { request } = event;
    const url = new URL(request.url);

    // Handle navigation requests (HTML pages)
    if (request.mode === 'navigate') {
        event.respondWith(
            fetch(request)
                .then(response => {
                    // If online, cache the page and return it
                    if (response.ok) {
                        const responseClone = response.clone();
                        caches.open(DYNAMIC_CACHE).then(cache => {
                            cache.put(request, responseClone);
                        });
                        return response;
                    }
                    throw new Error('Network response was not ok');
                })
                .catch(() => {
                    // If offline, try to serve from cache
                    return caches.match(request)
                        .then(cachedResponse => {
                            if (cachedResponse) {
                                return cachedResponse;
                            }
                            
                            // Try to match the route path from cached files
                            const url = new URL(request.url);
                            const pathname = url.pathname;
                            
                            // Check static cache first
                            return caches.match(pathname, { cacheName: STATIC_CACHE })
                                .then(staticResponse => {
                                    if (staticResponse) {
                                        return staticResponse;
                                    }
                                    
                                    // Check dynamic cache
                                    return caches.match(pathname, { cacheName: DYNAMIC_CACHE })
                                        .then(dynamicResponse => {
                                            if (dynamicResponse) {
                                                return dynamicResponse;
                                            }
                                            
                                            // Return offline page for uncached routes
                                            return caches.match('/offline.html');
                                        });
                                });
                        });
                })
        );
        return;
    }

    // Handle API requests
    if (url.pathname.startsWith('/api/') || request.method === 'POST') {
        event.respondWith(
            fetch(request)
                .then(response => response)
                .catch(() => {
                    // Store failed requests for later sync
                    if (request.method === 'POST') {
                        storeFailedRequest(request);
                    }
                    return new Response(
                        JSON.stringify({ 
                            offline: true, 
                            message: 'Request stored for later sync' 
                        }),
                        { 
                            status: 200,
                            headers: { 'Content-Type': 'application/json' }
                        }
                    );
                })
        );
        return;
    }

    // Handle other requests (CSS, JS, images)
    event.respondWith(
        caches.match(request)
            .then(cachedResponse => {
                if (cachedResponse) {
                    return cachedResponse;
                }
                return fetch(request)
                    .then(response => {
                        // Cache successful responses
                        if (response.ok) {
                            const responseClone = response.clone();
                            caches.open(DYNAMIC_CACHE).then(cache => {
                                cache.put(request, responseClone);
                            });
                        }
                        return response;
                    })
                    .catch(() => {
                        // Return fallback for failed requests
                        if (request.destination === 'image') {
                            return caches.match('/static/img/favicon.png');
                        }
                        return new Response('Offline', { status: 503 });
                    });
            })
    );
});

// Store failed requests for background sync
function storeFailedRequest(request) {
    request.clone().text().then(body => {
        const requestData = {
            url: request.url,
            method: request.method,
            headers: [...request.headers.entries()],
            body: body,
            timestamp: Date.now()
        };
        
        // Store in IndexedDB for later sync
        if ('indexedDB' in self) {
            const dbRequest = indexedDB.open('darksulfocus-offline', 1);
            dbRequest.onsuccess = event => {
                const db = event.target.result;
                const transaction = db.transaction(['requests'], 'readwrite');
                const store = transaction.objectStore('requests');
                store.add(requestData);
            };
            dbRequest.onupgradeneeded = event => {
                const db = event.target.result;
                if (!db.objectStoreNames.contains('requests')) {
                    db.createObjectStore('requests', { keyPath: 'timestamp' });
                }
            };
        }
    });
}

// Background sync for failed requests
self.addEventListener('sync', event => {
    if (event.tag === 'background-sync') {
        event.waitUntil(syncFailedRequests());
    }
});

function syncFailedRequests() {
    return new Promise((resolve, reject) => {
        const dbRequest = indexedDB.open('darksulfocus-offline', 1);
        dbRequest.onsuccess = event => {
            const db = event.target.result;
            const transaction = db.transaction(['requests'], 'readwrite');
            const store = transaction.objectStore('requests');
            const getAllRequest = store.getAll();
            
            getAllRequest.onsuccess = () => {
                const requests = getAllRequest.result;
                const syncPromises = requests.map(requestData => {
                    return fetch(requestData.url, {
                        method: requestData.method,
                        headers: new Headers(requestData.headers),
                        body: requestData.body
                    }).then(() => {
                        // Remove successful request from storage
                        store.delete(requestData.timestamp);
                    }).catch(err => {
                        console.error('Failed to sync request:', err);
                    });
                });
                
                Promise.all(syncPromises).then(() => resolve()).catch(() => reject());
            };
        };
    });
}
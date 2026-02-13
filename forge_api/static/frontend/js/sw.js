/**
 * Service Worker for ForgeDB Frontend
 * Provides offline caching and performance optimizations
 */

const CACHE_NAME = 'forgedb-v2';
const STATIC_CACHE = 'forgedb-static-v2';
const DYNAMIC_CACHE = 'forgedb-dynamic-v2';
const API_CACHE = 'forgedb-api-v2';

// Resources to cache immediately
const STATIC_ASSETS = [
    '/',
    '/static/frontend/css/main.css',
    '/static/frontend/css/responsive.css',
    '/static/frontend/css/performance-optimizations.css',
    '/static/frontend/js/performance.js',
    '/static/frontend/js/main.js',
    '/static/frontend/js/api-integration.js',
    '/static/frontend/js/notification-system.js',
    '/static/frontend/vendor/chart.min.js',
    '/static/frontend/img/favicon.ico',
    '/static/frontend/img/icon-192x192.png',
    '/static/frontend/manifest.json'
];

// API endpoints to cache with different strategies
const API_CACHE_PATTERNS = [
    { pattern: /\/api\/v1\/dashboard\//, strategy: 'networkFirst', maxAge: 5 * 60 * 1000 }, // 5 minutes
    { pattern: /\/api\/v1\/clients\//, strategy: 'staleWhileRevalidate', maxAge: 10 * 60 * 1000 }, // 10 minutes
    { pattern: /\/api\/v1\/products\//, strategy: 'staleWhileRevalidate', maxAge: 15 * 60 * 1000 }, // 15 minutes
    { pattern: /\/api\/v1\/equipment\//, strategy: 'staleWhileRevalidate', maxAge: 15 * 60 * 1000 }, // 15 minutes
    { pattern: /\/api\/v1\/auth\//, strategy: 'networkOnly' } // Never cache auth requests
];

// Cache size limits
const CACHE_LIMITS = {
    [STATIC_CACHE]: 50,
    [DYNAMIC_CACHE]: 100,
    [API_CACHE]: 200
};

// Install event - cache static assets
self.addEventListener('install', event => {
    console.log('Service Worker installing...');
    
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then(cache => {
                console.log('Caching static assets...');
                return cache.addAll(STATIC_ASSETS);
            })
            .then(() => {
                console.log('Static assets cached successfully');
                return self.skipWaiting();
            })
            .catch(error => {
                console.error('Error caching static assets:', error);
            })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
    console.log('Service Worker activating...');
    
    event.waitUntil(
        caches.keys()
            .then(cacheNames => {
                return Promise.all(
                    cacheNames.map(cacheName => {
                        if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE) {
                            console.log('Deleting old cache:', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => {
                console.log('Service Worker activated');
                return self.clients.claim();
            })
    );
});

// Fetch event - serve cached content when possible
self.addEventListener('fetch', event => {
    const { request } = event;
    const url = new URL(request.url);
    
    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }
    
    // Handle different types of requests
    if (isStaticAsset(request)) {
        event.respondWith(handleStaticAsset(request));
    } else if (isAPIRequest(request)) {
        event.respondWith(handleAPIRequest(request));
    } else if (isPageRequest(request)) {
        event.respondWith(handlePageRequest(request));
    }
});

// Check if request is for a static asset
function isStaticAsset(request) {
    const url = new URL(request.url);
    return url.pathname.startsWith('/static/') || 
           url.pathname.match(/\.(css|js|png|jpg|jpeg|gif|svg|ico|woff|woff2)$/);
}

// Check if request is for an API endpoint
function isAPIRequest(request) {
    const url = new URL(request.url);
    return url.pathname.startsWith('/api/');
}

// Check if request is for a page
function isPageRequest(request) {
    const url = new URL(request.url);
    return request.headers.get('accept')?.includes('text/html');
}

// Handle static asset requests - cache first strategy
async function handleStaticAsset(request) {
    try {
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        const networkResponse = await fetch(request);
        
        // Cache successful responses
        if (networkResponse.ok) {
            const cache = await caches.open(STATIC_CACHE);
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        console.error('Error handling static asset:', error);
        
        // Return cached version if available
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        // Return offline fallback
        return new Response('Asset not available offline', { status: 503 });
    }
}

// Handle API requests with different caching strategies
async function handleAPIRequest(request) {
    const url = new URL(request.url);
    const cacheConfig = API_CACHE_PATTERNS.find(config => config.pattern.test(url.pathname));
    
    if (!cacheConfig) {
        // Default to network-only for unknown API endpoints
        return fetch(request);
    }
    
    switch (cacheConfig.strategy) {
        case 'networkFirst':
            return networkFirst(request, API_CACHE, cacheConfig.maxAge);
        case 'staleWhileRevalidate':
            return staleWhileRevalidate(request, API_CACHE, cacheConfig.maxAge);
        case 'networkOnly':
            return fetch(request);
        default:
            return networkFirst(request, API_CACHE, cacheConfig.maxAge);
    }
}

// Network first strategy - try network, fallback to cache
async function networkFirst(request, cacheName, maxAge) {
    try {
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            const cache = await caches.open(cacheName);
            const responseClone = networkResponse.clone();
            
            // Add timestamp for cache expiration
            const responseWithTimestamp = new Response(responseClone.body, {
                status: responseClone.status,
                statusText: responseClone.statusText,
                headers: {
                    ...Object.fromEntries(responseClone.headers.entries()),
                    'sw-cache-timestamp': Date.now().toString(),
                    'sw-cache-max-age': maxAge.toString()
                }
            });
            
            await cache.put(request, responseWithTimestamp);
            await limitCacheSize(cacheName, CACHE_LIMITS[cacheName]);
        }
        
        return networkResponse;
    } catch (error) {
        console.error('Network request failed, trying cache:', error);
        
        const cachedResponse = await getCachedResponse(request, cacheName, maxAge);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        // Return offline response
        return new Response(
            JSON.stringify({ 
                error: 'Data not available offline',
                cached: false,
                timestamp: Date.now()
            }), 
            { 
                status: 503,
                headers: { 'Content-Type': 'application/json' }
            }
        );
    }
}

// Stale while revalidate strategy - return cache immediately, update in background
async function staleWhileRevalidate(request, cacheName, maxAge) {
    const cachedResponse = await getCachedResponse(request, cacheName, maxAge);
    
    // Start network request in background
    const networkResponsePromise = fetch(request).then(async networkResponse => {
        if (networkResponse.ok) {
            const cache = await caches.open(cacheName);
            const responseClone = networkResponse.clone();
            
            const responseWithTimestamp = new Response(responseClone.body, {
                status: responseClone.status,
                statusText: responseClone.statusText,
                headers: {
                    ...Object.fromEntries(responseClone.headers.entries()),
                    'sw-cache-timestamp': Date.now().toString(),
                    'sw-cache-max-age': maxAge.toString()
                }
            });
            
            await cache.put(request, responseWithTimestamp);
            await limitCacheSize(cacheName, CACHE_LIMITS[cacheName]);
        }
        return networkResponse;
    }).catch(error => {
        console.error('Background network request failed:', error);
        return null;
    });
    
    // Return cached response immediately if available
    if (cachedResponse) {
        // Don't await the network request, let it complete in background
        networkResponsePromise;
        return cachedResponse;
    }
    
    // If no cache, wait for network
    try {
        return await networkResponsePromise;
    } catch (error) {
        return new Response(
            JSON.stringify({ 
                error: 'Data not available',
                cached: false,
                timestamp: Date.now()
            }), 
            { 
                status: 503,
                headers: { 'Content-Type': 'application/json' }
            }
        );
    }
}

// Get cached response with expiration check
async function getCachedResponse(request, cacheName, maxAge) {
    const cache = await caches.open(cacheName);
    const cachedResponse = await cache.match(request);
    
    if (!cachedResponse) {
        return null;
    }
    
    // Check if cache has expired
    const cacheTimestamp = cachedResponse.headers.get('sw-cache-timestamp');
    const cacheMaxAge = cachedResponse.headers.get('sw-cache-max-age');
    
    if (cacheTimestamp && cacheMaxAge) {
        const age = Date.now() - parseInt(cacheTimestamp);
        if (age > parseInt(cacheMaxAge)) {
            // Cache expired, remove it
            await cache.delete(request);
            return null;
        }
    }
    
    // Add header to indicate cached response
    const response = cachedResponse.clone();
    response.headers.set('X-Served-From', 'sw-cache');
    return response;
}

// Limit cache size to prevent storage overflow
async function limitCacheSize(cacheName, maxEntries) {
    const cache = await caches.open(cacheName);
    const keys = await cache.keys();
    
    if (keys.length > maxEntries) {
        // Remove oldest entries (FIFO)
        const entriesToDelete = keys.slice(0, keys.length - maxEntries);
        await Promise.all(entriesToDelete.map(key => cache.delete(key)));
    }
}

// Handle page requests - network first with offline fallback
async function handlePageRequest(request) {
    try {
        const networkResponse = await fetch(request);
        
        // Cache successful page responses
        if (networkResponse.ok) {
            const cache = await caches.open(DYNAMIC_CACHE);
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        console.error('Page request failed, trying cache:', error);
        
        // Try to serve cached page
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        // Serve offline fallback page
        return caches.match('/offline.html') || 
               new Response('Page not available offline', { 
                   status: 503,
                   headers: { 'Content-Type': 'text/html' }
               });
    }
}

// Determine if API response should be cached
function shouldCacheAPIResponse(request) {
    const url = new URL(request.url);
    
    // Only cache GET requests
    if (request.method !== 'GET') {
        return false;
    }
    
    // Check against cacheable patterns
    return API_CACHE_PATTERNS.some(pattern => pattern.test(url.pathname));
}

// Background sync for offline actions
self.addEventListener('sync', event => {
    console.log('Background sync triggered:', event.tag);
    
    if (event.tag === 'background-sync') {
        event.waitUntil(doBackgroundSync());
    }
});

// Handle background sync
async function doBackgroundSync() {
    try {
        // Process any queued offline actions
        const offlineActions = await getOfflineActions();
        
        for (const action of offlineActions) {
            try {
                await processOfflineAction(action);
                await removeOfflineAction(action.id);
            } catch (error) {
                console.error('Failed to process offline action:', error);
            }
        }
    } catch (error) {
        console.error('Background sync failed:', error);
    }
}

// Get offline actions from IndexedDB (simplified)
async function getOfflineActions() {
    // This would typically use IndexedDB to store offline actions
    // For now, return empty array
    return [];
}

// Process an offline action
async function processOfflineAction(action) {
    const response = await fetch(action.url, {
        method: action.method,
        headers: action.headers,
        body: action.body
    });
    
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    return response;
}

// Remove processed offline action
async function removeOfflineAction(actionId) {
    // This would remove the action from IndexedDB
    console.log('Removing offline action:', actionId);
}

// Push notification handling
self.addEventListener('push', event => {
    console.log('Push notification received:', event);
    
    const options = {
        body: event.data ? event.data.text() : 'New notification from ForgeDB',
        icon: '/static/frontend/images/icon-192x192.png',
        badge: '/static/frontend/images/badge-72x72.png',
        vibrate: [100, 50, 100],
        data: {
            dateOfArrival: Date.now(),
            primaryKey: 1
        },
        actions: [
            {
                action: 'explore',
                title: 'View Details',
                icon: '/static/frontend/images/checkmark.png'
            },
            {
                action: 'close',
                title: 'Close',
                icon: '/static/frontend/images/xmark.png'
            }
        ]
    };
    
    event.waitUntil(
        self.registration.showNotification('ForgeDB', options)
    );
});

// Notification click handling
self.addEventListener('notificationclick', event => {
    console.log('Notification clicked:', event);
    
    event.notification.close();
    
    if (event.action === 'explore') {
        event.waitUntil(
            clients.openWindow('/dashboard/')
        );
    }
});

// Message handling from main thread
self.addEventListener('message', event => {
    console.log('Service Worker received message:', event.data);
    
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
    
    if (event.data && event.data.type === 'CACHE_URLS') {
        event.waitUntil(
            cacheUrls(event.data.urls)
        );
    }
});

// Cache specific URLs
async function cacheUrls(urls) {
    const cache = await caches.open(DYNAMIC_CACHE);
    
    for (const url of urls) {
        try {
            await cache.add(url);
            console.log('Cached URL:', url);
        } catch (error) {
            console.error('Failed to cache URL:', url, error);
        }
    }
}

// Periodic background sync (if supported)
if ('periodicSync' in self.registration) {
    self.addEventListener('periodicsync', event => {
        if (event.tag === 'content-sync') {
            event.waitUntil(syncContent());
        }
    });
}

// Sync content in background
async function syncContent() {
    try {
        // Sync critical data in background
        const criticalEndpoints = [
            '/api/dashboard/summary/',
            '/api/notifications/unread/'
        ];
        
        const cache = await caches.open(DYNAMIC_CACHE);
        
        for (const endpoint of criticalEndpoints) {
            try {
                const response = await fetch(endpoint);
                if (response.ok) {
                    await cache.put(endpoint, response);
                }
            } catch (error) {
                console.error('Failed to sync endpoint:', endpoint, error);
            }
        }
    } catch (error) {
        console.error('Content sync failed:', error);
    }
}
/**
 * Performance Optimization and Loading Enhancements
 * ForgeDB Frontend Application
 */

// ===== LAZY LOADING IMPLEMENTATION =====

class LazyLoader {
    constructor() {
        this.imageObserver = null;
        this.contentObserver = null;
        this.init();
    }

    init() {
        // Initialize Intersection Observer for images
        if ('IntersectionObserver' in window) {
            this.imageObserver = new IntersectionObserver(
                this.handleImageIntersection.bind(this),
                {
                    rootMargin: '50px 0px',
                    threshold: 0.01
                }
            );

            this.contentObserver = new IntersectionObserver(
                this.handleContentIntersection.bind(this),
                {
                    rootMargin: '100px 0px',
                    threshold: 0.01
                }
            );

            this.observeElements();
        } else {
            // Fallback for older browsers
            this.loadAllImages();
        }
    }

    observeElements() {
        // Observe lazy images
        document.querySelectorAll('img[data-src]').forEach(img => {
            this.imageObserver.observe(img);
        });

        // Observe lazy content sections
        document.querySelectorAll('[data-lazy-content]').forEach(element => {
            this.contentObserver.observe(element);
        });
    }

    handleImageIntersection(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                this.loadImage(img);
                this.imageObserver.unobserve(img);
            }
        });
    }

    handleContentIntersection(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const element = entry.target;
                this.loadContent(element);
                this.contentObserver.unobserve(element);
            }
        });
    }

    loadImage(img) {
        const src = img.getAttribute('data-src');
        if (src) {
            img.src = src;
            img.removeAttribute('data-src');
            img.classList.add('loaded');
        }
    }

    loadContent(element) {
        const url = element.getAttribute('data-lazy-content');
        if (url) {
            this.fetchContent(url, element);
        }
    }

    async fetchContent(url, element) {
        try {
            element.innerHTML = '<div class="text-center p-4"><div class="spinner-border" role="status"></div></div>';
            
            const response = await fetch(url);
            const content = await response.text();
            
            element.innerHTML = content;
            element.removeAttribute('data-lazy-content');
            
            // Re-observe any new lazy elements in the loaded content
            this.observeElements();
        } catch (error) {
            console.error('Error loading lazy content:', error);
            element.innerHTML = '<div class="alert alert-warning">Error loading content</div>';
        }
    }

    loadAllImages() {
        // Fallback: load all images immediately
        document.querySelectorAll('img[data-src]').forEach(img => {
            this.loadImage(img);
        });
    }
}

// ===== CLIENT-SIDE CACHING =====

class CacheManager {
    constructor() {
        this.cache = new Map();
        this.maxAge = 5 * 60 * 1000; // 5 minutes
        this.maxSize = 50; // Maximum number of cached items
    }

    set(key, data) {
        // Remove oldest items if cache is full
        if (this.cache.size >= this.maxSize) {
            const firstKey = this.cache.keys().next().value;
            this.cache.delete(firstKey);
        }

        this.cache.set(key, {
            data: data,
            timestamp: Date.now()
        });
    }

    get(key) {
        const item = this.cache.get(key);
        
        if (!item) {
            return null;
        }

        // Check if item has expired
        if (Date.now() - item.timestamp > this.maxAge) {
            this.cache.delete(key);
            return null;
        }

        return item.data;
    }

    clear() {
        this.cache.clear();
    }

    has(key) {
        const item = this.cache.get(key);
        if (!item) return false;
        
        if (Date.now() - item.timestamp > this.maxAge) {
            this.cache.delete(key);
            return false;
        }
        
        return true;
    }
}

// ===== API RESPONSE CACHING =====

class APICache {
    constructor() {
        this.cache = new CacheManager();
    }

    async fetchWithCache(url, options = {}) {
        const cacheKey = this.generateCacheKey(url, options);
        
        // Return cached response if available
        const cachedResponse = this.cache.get(cacheKey);
        if (cachedResponse && !options.bypassCache) {
            return cachedResponse;
        }

        try {
            const response = await fetch(url, options);
            const data = await response.json();
            
            // Cache successful responses
            if (response.ok) {
                this.cache.set(cacheKey, data);
            }
            
            return data;
        } catch (error) {
            // Return cached data if available during error
            if (cachedResponse) {
                console.warn('Using cached data due to fetch error:', error);
                return cachedResponse;
            }
            throw error;
        }
    }

    generateCacheKey(url, options) {
        const method = options.method || 'GET';
        const body = options.body || '';
        return `${method}:${url}:${body}`;
    }

    clearCache() {
        this.cache.clear();
    }
}

// ===== IMAGE OPTIMIZATION =====

class ImageOptimizer {
    constructor() {
        this.webpSupported = this.checkWebPSupport();
        this.init();
    }

    checkWebPSupport() {
        const canvas = document.createElement('canvas');
        canvas.width = 1;
        canvas.height = 1;
        return canvas.toDataURL('image/webp').indexOf('data:image/webp') === 0;
    }

    init() {
        // Replace image sources with optimized versions
        document.querySelectorAll('img[data-optimize]').forEach(img => {
            this.optimizeImage(img);
        });
    }

    optimizeImage(img) {
        const originalSrc = img.src || img.getAttribute('data-src');
        if (!originalSrc) return;

        // Add WebP support if available
        if (this.webpSupported) {
            const webpSrc = originalSrc.replace(/\.(jpg|jpeg|png)$/i, '.webp');
            img.src = webpSrc;
            
            // Fallback to original if WebP fails
            img.onerror = () => {
                img.src = originalSrc;
                img.onerror = null;
            };
        }

        // Add responsive image attributes
        this.addResponsiveAttributes(img);
    }

    addResponsiveAttributes(img) {
        if (!img.hasAttribute('loading')) {
            img.setAttribute('loading', 'lazy');
        }
        
        if (!img.hasAttribute('decoding')) {
            img.setAttribute('decoding', 'async');
        }
    }
}

// ===== PERFORMANCE MONITORING =====

class PerformanceMonitor {
    constructor() {
        this.metrics = {};
        this.init();
    }

    init() {
        // Monitor page load performance
        if ('performance' in window) {
            window.addEventListener('load', () => {
                setTimeout(() => this.collectMetrics(), 0);
            });
        }

        // Monitor long tasks
        if ('PerformanceObserver' in window) {
            this.observeLongTasks();
            this.observeLayoutShifts();
        }
    }

    collectMetrics() {
        const navigation = performance.getEntriesByType('navigation')[0];
        if (navigation) {
            this.metrics = {
                domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
                loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
                firstPaint: this.getFirstPaint(),
                firstContentfulPaint: this.getFirstContentfulPaint(),
                largestContentfulPaint: this.getLargestContentfulPaint()
            };

            this.reportMetrics();
        }
    }

    getFirstPaint() {
        const paintEntries = performance.getEntriesByType('paint');
        const firstPaint = paintEntries.find(entry => entry.name === 'first-paint');
        return firstPaint ? firstPaint.startTime : null;
    }

    getFirstContentfulPaint() {
        const paintEntries = performance.getEntriesByType('paint');
        const fcp = paintEntries.find(entry => entry.name === 'first-contentful-paint');
        return fcp ? fcp.startTime : null;
    }

    getLargestContentfulPaint() {
        return new Promise(resolve => {
            const observer = new PerformanceObserver(list => {
                const entries = list.getEntries();
                const lastEntry = entries[entries.length - 1];
                resolve(lastEntry.startTime);
                observer.disconnect();
            });
            observer.observe({ entryTypes: ['largest-contentful-paint'] });
        });
    }

    observeLongTasks() {
        const observer = new PerformanceObserver(list => {
            list.getEntries().forEach(entry => {
                if (entry.duration > 50) {
                    console.warn('Long task detected:', entry.duration + 'ms');
                }
            });
        });
        observer.observe({ entryTypes: ['longtask'] });
    }

    observeLayoutShifts() {
        const observer = new PerformanceObserver(list => {
            let cumulativeScore = 0;
            list.getEntries().forEach(entry => {
                if (!entry.hadRecentInput) {
                    cumulativeScore += entry.value;
                }
            });
            
            if (cumulativeScore > 0.1) {
                console.warn('High cumulative layout shift:', cumulativeScore);
            }
        });
        observer.observe({ entryTypes: ['layout-shift'] });
    }

    reportMetrics() {
        // Send metrics to analytics or logging service
        console.log('Performance Metrics:', this.metrics);
        
        // You can extend this to send to your analytics service
        // analytics.track('page_performance', this.metrics);
    }
}

// ===== DEBOUNCE AND THROTTLE UTILITIES =====

function debounce(func, wait, immediate = false) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            timeout = null;
            if (!immediate) func.apply(this, args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func.apply(this, args);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function executedFunction(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// ===== INITIALIZATION =====

document.addEventListener('DOMContentLoaded', function() {
    // Initialize performance optimizations
    const lazyLoader = new LazyLoader();
    const imageOptimizer = new ImageOptimizer();
    const performanceMonitor = new PerformanceMonitor();
    
    // Make API cache available globally
    window.apiCache = new APICache();
    
    // Initialize responsive table optimization
    initializeResponsiveTables();
    
    // Initialize mobile-specific optimizations
    if (window.innerWidth < 768) {
        initializeMobileOptimizations();
    }
    
    // Optimize form submissions
    document.querySelectorAll('form').forEach(form => {
        // Skip forms with data-no-form-handler attribute
        if (form.hasAttribute('data-no-form-handler')) {
            return;
        }
        
        const submitButton = form.querySelector('button[type="submit"]');
        if (submitButton) {
            // Store original text
            submitButton.setAttribute('data-original-text', submitButton.innerHTML);
            
            form.addEventListener('submit', function() {
                submitButton.disabled = true;
                submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Procesando...';
                
                // Re-enable after 5 seconds as fallback
                setTimeout(() => {
                    submitButton.disabled = false;
                    submitButton.innerHTML = submitButton.getAttribute('data-original-text') || 'Enviar';
                }, 5000);
            });
        }
    });
    
    // Optimize search inputs with debouncing
    document.querySelectorAll('input[type="search"], .search-input').forEach(input => {
        const form = input.closest('form');
        if (form) {
            const debouncedSubmit = debounce(() => {
                form.submit();
            }, 500);
            
            input.addEventListener('input', debouncedSubmit);
        }
    });
    
    // Add loading states to buttons
    document.querySelectorAll('.btn[data-loading]').forEach(button => {
        button.addEventListener('click', function() {
            const originalText = this.innerHTML;
            this.setAttribute('data-original-text', originalText);
            this.disabled = true;
            this.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Cargando...';
        });
    });
    
    // Preload critical resources
    preloadCriticalResources();
    
    // Initialize service worker if available
    if ('serviceWorker' in navigator) {
        registerServiceWorker();
    }
    
    // Initialize viewport-based optimizations
    initializeViewportOptimizations();
    
    // Initialize connection-aware loading
    initializeConnectionAwareLoading();
});

// ===== RESPONSIVE TABLE OPTIMIZATION =====

function initializeResponsiveTables() {
    const tables = document.querySelectorAll('.table-responsive table');
    
    tables.forEach(table => {
        // Add data-label attributes for mobile stacking
        const headers = table.querySelectorAll('thead th');
        const rows = table.querySelectorAll('tbody tr');
        
        rows.forEach(row => {
            const cells = row.querySelectorAll('td');
            cells.forEach((cell, index) => {
                if (headers[index]) {
                    cell.setAttribute('data-label', headers[index].textContent.trim());
                }
            });
        });
        
        // Add responsive class for mobile stacking
        if (window.innerWidth < 768) {
            table.classList.add('table-stack');
        }
    });
}

// ===== MOBILE-SPECIFIC OPTIMIZATIONS =====

function initializeMobileOptimizations() {
    // Convert button groups to mobile-friendly layout
    document.querySelectorAll('.btn-group').forEach(group => {
        if (window.innerWidth < 576) {
            group.classList.add('btn-group-mobile');
            group.classList.remove('btn-group');
        }
    });
    
    // Optimize dropdown menus for touch
    document.querySelectorAll('.dropdown-menu').forEach(menu => {
        menu.style.minWidth = '280px';
        
        // Add touch-friendly spacing
        const items = menu.querySelectorAll('.dropdown-item');
        items.forEach(item => {
            item.style.padding = '0.75rem 1rem';
            item.style.fontSize = '1rem';
        });
    });
    
    // Optimize modal dialogs for mobile
    document.querySelectorAll('.modal-dialog').forEach(dialog => {
        dialog.classList.add('modal-fullscreen-sm-down');
    });
    
    // Add swipe gestures for carousels and tabs
    initializeSwipeGestures();
}

// ===== SWIPE GESTURES =====

function initializeSwipeGestures() {
    let startX = 0;
    let startY = 0;
    
    document.addEventListener('touchstart', function(e) {
        startX = e.touches[0].clientX;
        startY = e.touches[0].clientY;
    });
    
    document.addEventListener('touchend', function(e) {
        if (!startX || !startY) return;
        
        const endX = e.changedTouches[0].clientX;
        const endY = e.changedTouches[0].clientY;
        
        const diffX = startX - endX;
        const diffY = startY - endY;
        
        // Only process horizontal swipes
        if (Math.abs(diffX) > Math.abs(diffY) && Math.abs(diffX) > 50) {
            const target = e.target.closest('.carousel, .tab-content');
            
            if (target) {
                if (diffX > 0) {
                    // Swipe left - next
                    const nextBtn = target.querySelector('.carousel-control-next, .nav-link[data-bs-target]');
                    if (nextBtn) nextBtn.click();
                } else {
                    // Swipe right - previous
                    const prevBtn = target.querySelector('.carousel-control-prev');
                    if (prevBtn) prevBtn.click();
                }
            }
        }
        
        startX = 0;
        startY = 0;
    });
}

// ===== VIEWPORT-BASED OPTIMIZATIONS =====

function initializeViewportOptimizations() {
    // Adjust content based on viewport height
    const vh = window.innerHeight * 0.01;
    document.documentElement.style.setProperty('--vh', `${vh}px`);
    
    // Update on resize
    window.addEventListener('resize', throttle(() => {
        const vh = window.innerHeight * 0.01;
        document.documentElement.style.setProperty('--vh', `${vh}px`);
        
        // Re-initialize responsive tables if needed
        if (window.innerWidth < 768) {
            document.querySelectorAll('.table-responsive table').forEach(table => {
                table.classList.add('table-stack');
            });
        } else {
            document.querySelectorAll('.table-stack').forEach(table => {
                table.classList.remove('table-stack');
            });
        }
    }, 250));
}

// ===== CONNECTION-AWARE LOADING =====

function initializeConnectionAwareLoading() {
    if ('connection' in navigator) {
        const connection = navigator.connection;
        
        // Adjust loading strategy based on connection
        if (connection.effectiveType === 'slow-2g' || connection.effectiveType === '2g') {
            // Disable non-critical features for slow connections
            document.querySelectorAll('.lazy-placeholder').forEach(placeholder => {
                placeholder.style.display = 'none';
            });
            
            // Reduce image quality
            document.querySelectorAll('img').forEach(img => {
                if (img.src && !img.src.includes('low-quality')) {
                    const lowQualitySrc = img.src.replace(/\.(jpg|jpeg|png)$/i, '-low.$1');
                    img.src = lowQualitySrc;
                }
            });
        }
        
        // Monitor connection changes
        connection.addEventListener('change', () => {
            console.log('Connection changed:', connection.effectiveType);
            
            // Adjust caching strategy
            if (window.apiCache) {
                if (connection.effectiveType === 'slow-2g' || connection.effectiveType === '2g') {
                    window.apiCache.cache.maxAge = 10 * 60 * 1000; // 10 minutes for slow connections
                } else {
                    window.apiCache.cache.maxAge = 5 * 60 * 1000; // 5 minutes for fast connections
                }
            }
        });
    }
}

// ===== RESOURCE PRELOADING =====

function preloadCriticalResources() {
    const criticalResources = [
        '/static/frontend/css/main.css',
        '/static/frontend/js/main.js'
    ];
    
    criticalResources.forEach(resource => {
        const link = document.createElement('link');
        link.rel = 'preload';
        link.href = resource;
        link.as = resource.endsWith('.css') ? 'style' : 'script';
        document.head.appendChild(link);
    });
}

// ===== SERVICE WORKER REGISTRATION =====

async function registerServiceWorker() {
    try {
        const registration = await navigator.serviceWorker.register('/static/frontend/js/sw.js', {
            scope: '/'
        });
        console.log('Service Worker registered successfully:', registration);
        
        // Listen for updates
        registration.addEventListener('updatefound', () => {
            const newWorker = registration.installing;
            newWorker.addEventListener('statechange', () => {
                if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                    console.log('New service worker available');
                    // Optionally notify user about update
                }
            });
        });
        
    } catch (error) {
        console.log('Service Worker registration failed:', error);
    }
}

// ===== EXPORT FOR MODULE USAGE =====

if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        LazyLoader,
        CacheManager,
        APICache,
        ImageOptimizer,
        PerformanceMonitor,
        debounce,
        throttle
    };
}
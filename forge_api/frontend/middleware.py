"""
Custom middleware for frontend optimizations
"""
import re
from django.utils.cache import patch_cache_control
from django.utils.deprecation import MiddlewareMixin


class StaticFilesCacheMiddleware(MiddlewareMixin):
    """
    Middleware to add appropriate cache headers for static files
    """
    
    # Static file patterns that should be cached for a long time
    LONG_CACHE_PATTERNS = [
        r'\.css$',
        r'\.js$',
        r'\.png$',
        r'\.jpg$',
        r'\.jpeg$',
        r'\.gif$',
        r'\.svg$',
        r'\.ico$',
        r'\.woff$',
        r'\.woff2$',
        r'\.ttf$',
        r'\.eot$',
    ]
    
    # Files that should have shorter cache times
    SHORT_CACHE_PATTERNS = [
        r'manifest\.json$',
        r'sw\.js$',
    ]
    
    def process_response(self, request, response):
        # Only process static file requests
        if not request.path.startswith('/static/'):
            return response
        
        # Check if it's a static file that should be cached
        path = request.path.lower()
        
        # Long cache for static assets (1 year)
        if any(re.search(pattern, path) for pattern in self.LONG_CACHE_PATTERNS):
            patch_cache_control(
                response,
                max_age=31536000,  # 1 year
                public=True,
                immutable=True
            )
            response['Vary'] = 'Accept-Encoding'
            
        # Short cache for dynamic static files (1 hour)
        elif any(re.search(pattern, path) for pattern in self.SHORT_CACHE_PATTERNS):
            patch_cache_control(
                response,
                max_age=3600,  # 1 hour
                public=True
            )
            
        # Add compression hints
        if path.endswith(('.css', '.js', '.json')):
            response['Content-Encoding'] = 'gzip'
            
        return response


class PerformanceMiddleware(MiddlewareMixin):
    """
    Middleware to add performance-related headers
    """
    
    def process_response(self, request, response):
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Add performance hints
        if request.path.startswith('/static/'):
            # Preload critical resources
            if 'main.css' in request.path:
                response['Link'] = '</static/frontend/js/main.js>; rel=preload; as=script'
            elif 'main.js' in request.path:
                response['Link'] = '</static/frontend/css/main.css>; rel=preload; as=style'
        
        # Add resource hints for HTML pages
        elif response.get('Content-Type', '').startswith('text/html'):
            # DNS prefetch for external resources
            response['Link'] = (
                '<https://cdn.jsdelivr.net>; rel=dns-prefetch, '
                '<https://fonts.googleapis.com>; rel=dns-prefetch'
            )
            
        return response


class CompressionMiddleware(MiddlewareMixin):
    """
    Middleware to handle compression for better performance
    """
    
    COMPRESSIBLE_TYPES = [
        'text/html',
        'text/css',
        'text/javascript',
        'application/javascript',
        'application/json',
        'text/xml',
        'application/xml',
        'image/svg+xml',
    ]
    
    def process_response(self, request, response):
        # Check if response should be compressed
        # FileResponse doesn't have 'content' attribute, check first
        if not hasattr(response, 'content'):
            return response
            
        content_type = response.get('Content-Type', '').split(';')[0]
        
        if (content_type in self.COMPRESSIBLE_TYPES and 
            'gzip' in request.META.get('HTTP_ACCEPT_ENCODING', '') and
            len(response.content) > 1024):  # Only compress if > 1KB
            
            # Add compression headers
            response['Vary'] = 'Accept-Encoding'
            
        return response


class MobileOptimizationMiddleware(MiddlewareMixin):
    """
    Middleware to optimize responses for mobile devices
    """
    
    MOBILE_USER_AGENTS = [
        'Mobile', 'Android', 'iPhone', 'iPad', 'Windows Phone'
    ]
    
    def process_request(self, request):
        # Detect mobile devices
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        request.is_mobile = any(agent in user_agent for agent in self.MOBILE_USER_AGENTS)
        
        # Set viewport width for mobile
        if request.is_mobile:
            request.viewport_width = 375  # iPhone width
        else:
            request.viewport_width = 1200  # Desktop width
            
    def process_response(self, request, response):
        # Add mobile-specific headers
        if hasattr(request, 'is_mobile') and request.is_mobile:
            response['Viewport-Width'] = str(request.viewport_width)
            
            # Suggest resource loading strategy for mobile
            if response.get('Content-Type', '').startswith('text/html'):
                response['Save-Data'] = 'on'
                
        return response
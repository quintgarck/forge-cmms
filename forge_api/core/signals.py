"""
Signal handlers for cache invalidation
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from django.urls import reverse
from .models import Supplier, PurchaseOrder


@receiver([post_save, post_delete], sender=Supplier)
def invalidate_supplier_cache(sender, instance, **kwargs):
    """
    Invalidate cache when supplier is saved or deleted
    This handles Django's view cache layer
    """
    try:
        from django.core.cache.utils import make_template_fragment_key
        from django.contrib.sessions.models import Session
        
        # Invalidate the supplier list view cache
        # The cache key pattern for cache_page decorator is:
        # 'views.decorators.cache.cache_page.{KEY_PREFIX}.{LANGUAGE}.{SITE_ID}.{PATH}.{QUERY_STRING}.{SESSION_KEY}'
        # Since we can't easily predict all variations, we'll try common patterns
        
        # For supplier list view with cache prefix 'supplier_list_authenticated'
        # We'll try to clear related cache keys
        cache_patterns_to_clear = [
            '*supplier_list_authenticated*',  # Wildcard pattern for the cached page
            f'*suppliers*',  # Pattern for supplier list pages
        ]
        
        # If we have access to cache backend that supports keys(), clear more specifically
        if hasattr(cache, 'keys'):
            for pattern in cache_patterns_to_clear:
                try:
                    keys = cache.keys(pattern)
                    if keys:
                        cache.delete_many(keys)
                except AttributeError:
                    # Some cache backends don't support keys() method
                    pass
        
        # As a fallback, we can also try to clear specific known cache prefixes
        # that might be used by cache_page
        cache.delete_many([
            'views.decorators.cache.cache_page.supplier_list_authenticated.views.decorators.cache.cache_page.supplier_list_authenticated',
            'views.decorators.cache.cache_page.supplier_list_authenticated.views.decorators.cache.cache_page.supplier_list_authenticated.en',
            'views.decorators.cache.cache_page.supplier_list_authenticated.views.decorators.cache.cache_page.supplier_list_authenticated.es',
        ])
        
        # Also clear the supplier detail page cache for this specific supplier
        # This is more difficult to predict with cache_page, so we'll rely on API cache invalidation
        
    except Exception as e:
        # Log error but don't break the save operation
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to invalidate supplier cache: {e}")


@receiver([post_save, post_delete], sender=PurchaseOrder)
def invalidate_purchase_order_cache(sender, instance, **kwargs):
    """
    Invalidate cache when purchase order is saved or deleted
    This handles Django's view cache layer
    """
    try:
        from django.core.cache.utils import make_template_fragment_key
        
        # For purchase orders, invalidate related cache entries
        cache_patterns_to_clear = [
            '*purchase-orders*',  # Pattern for purchase order related pages
            '*purchase_order*',   # Alternative pattern
        ]
        
        # If we have access to cache backend that supports keys(), clear more specifically
        if hasattr(cache, 'keys'):
            for pattern in cache_patterns_to_clear:
                try:
                    keys = cache.keys(pattern)
                    if keys:
                        cache.delete_many(keys)
                except AttributeError:
                    # Some cache backends don't support keys() method
                    pass
        
        # As a fallback, try to clear specific known cache prefixes
        cache.delete_many([
            'views.decorators.cache.cache_page.purchase_order_list.views.decorators.cache.cache_page.purchase_order_list',
            'views.decorators.cache.cache_page.purchase_order_list.views.decorators.cache.cache_page.purchase_order_list.en',
            'views.decorators.cache.cache_page.purchase_order_list.views.decorators.cache.cache_page.purchase_order_list.es',
        ])
        
    except Exception as e:
        # Log error but don't break the save operation
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to invalidate purchase order cache: {e}")
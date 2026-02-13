"""
Unified Search Service - Service for searching across all catalogs (inventory, OEM, equivalences).
"""
import logging
from django.db.models import Q, Sum
from django.core.cache import cache

logger = logging.getLogger(__name__)


class UnifiedSearchService:
    """
    Service for unified search across all catalogs.
    
    Searches in:
    - ProductMaster (inventory)
    - OEMCatalogItem (OEM catalog)
    - OEMEquivalence (OEM ↔ Aftermarket equivalences)
    - Equipment (client vehicles/equipment)
    """
    
    CACHE_TIMEOUT = 300  # 5 minutes
    
    def __init__(self, user=None):
        """
        Initialize the service.
        
        Args:
            user: Optional Django user for permission filtering
        """
        self.user = user
    
    def search(self, query, search_type='all', filters=None, limit=50):
        """
        Perform unified search across all catalogs.
        
        Args:
            query: Search query string
            search_type: Type of search ('all', 'products', 'oem', 'equivalences', 'equipment')
            filters: Optional dict of filters to apply
            limit: Maximum number of results per category
        
        Returns:
            dict with results from each category
        """
        if not query or len(query) < 2:
            return {
                'query': query,
                'error': 'Query must be at least 2 characters',
                'results': {}
            }
        
        filters = filters or {}
        
        results = {
            'query': query,
            'search_type': search_type,
            'total_count': 0,
            'results': {}
        }
        
        # Build cache key
        cache_key = f"unified_search_{query}_{search_type}_{hash(str(filters))}"
        
        # Try cache first (for non-filtered searches)
        if not filters and search_type == 'all':
            cached_results = cache.get(cache_key)
            if cached_results:
                return cached_results
        
        # Search in each category
        if search_type in ['all', 'products']:
            results['results']['products'] = self._search_products(query, filters, limit)
        
        if search_type in ['all', 'oem']:
            results['results']['oem_items'] = self._search_oem_catalog(query, filters, limit)
        
        if search_type in ['all', 'equivalences']:
            results['results']['equivalences'] = self._search_equivalences(query, filters, limit)
        
        if search_type in ['all', 'equipment']:
            results['results']['equipment'] = self._search_equipment(query, filters, limit)
        
        # Calculate totals
        results['total_count'] = sum(
            len(results['results'].get(cat, [])) 
            for cat in results['results']
        )
        
        # Cache results
        if not filters and search_type == 'all':
            cache.set(cache_key, results, self.CACHE_TIMEOUT)
        
        return results
    
    def _search_products(self, query, filters, limit):
        """Search in ProductMaster (inventory)"""
        from core.models import ProductMaster, Stock
        
        products = ProductMaster.objects.filter(is_active=True)
        
        # Text search
        products = products.filter(
            Q(internal_sku__icontains=query) |
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(brand__icontains=query) |
            Q(oem_ref__icontains=query) |
            Q(barcode__icontains=query) |
            Q(supplier_mpn__icontains=query)
        )
        
        # Apply filters
        if filters.get('brand'):
            products = products.filter(brand__icontains=filters['brand'])
        if filters.get('group_code'):
            products = products.filter(group_code=filters['group_code'])
        if filters.get('source_code'):
            products = products.filter(source_code=filters['source_code'])
        if filters.get('has_stock') is not None:
            if filters['has_stock']:
                products = products.filter(
                    stock__qty_on_hand__gt=0
                ).distinct()
        
        # Get stock info and format results
        results = []
        for product in products[:limit]:
            # Get stock summary
            stock_info = Stock.objects.filter(
                product=product.internal_sku
            ).aggregate(
                total_qty=Sum('qty_on_hand'),
                available_qty=Sum('qty_available')
            )
            
            results.append({
                'type': 'product',
                'id': product.internal_sku,
                'sku': product.internal_sku,
                'name': product.name,
                'brand': product.brand,
                'oem_ref': product.oem_ref,
                'group_code': product.group_code,
                'stock': {
                    'total': stock_info['total_qty'] or 0,
                    'available': stock_info['available_qty'] or 0
                },
                'price': str(product.standard_cost),
                'url': f'/inventory/products/{product.internal_sku}/',
                'search_highlight': self._highlight_match(query, product.name or product.internal_sku)
            })
        
        return results
    
    def _search_oem_catalog(self, query, filters, limit):
        """Search in OEM Catalog Items"""
        from core.models import OEMCatalogItem
        
        items = OEMCatalogItem.objects.filter(is_active=True)
        
        # Text search
        items = items.filter(
            Q(part_number__icontains=query) |
            Q(description_es__icontains=query) |
            Q(description_en__icontains=query) |
            Q(oem_code__name__icontains=query)
        )
        
        # Apply filters
        if filters.get('oem_code'):
            items = items.filter(oem_code__oem_code=filters['oem_code'])
        if filters.get('item_type'):
            items = items.filter(item_type=filters['item_type'])
        
        results = []
        for item in items[:limit]:
            description = item.description_es or item.description_en or ''
            
            results.append({
                'type': 'oem',
                'id': item.catalog_id,
                'part_number': item.part_number,
                'brand': item.oem_code.name if item.oem_code else '',
                'brand_code': item.oem_code.oem_code if item.oem_code else '',
                'description': description,
                'item_type': item.item_type,
                'year_start': item.year_start,
                'year_end': item.year_end,
                'list_price': str(item.list_price) if item.list_price else None,
                'url': f'/oem/catalog/{item.catalog_id}/',
                'search_highlight': self._highlight_match(query, item.part_number)
            })
        
        return results
    
    def _search_equivalences(self, query, filters, limit):
        """Search in OEM Equivalences"""
        from core.models import OEMEquivalence
        
        equivalences = OEMEquivalence.objects.all()
        
        # Text search
        equivalences = equivalences.filter(
            Q(oem_part_number__icontains=query) |
            Q(aftermarket_sku__icontains=query) |
            Q(oem_code__name__icontains=query) |
            Q(notes__icontains=query)
        )
        
        # Apply filters
        if filters.get('oem_code'):
            equivalences = equivalences.filter(oem_code__oem_code=filters['oem_code'])
        if filters.get('equivalence_type'):
            equivalences = equivalences.filter(equivalence_type=filters['equivalence_type'])
        if filters.get('min_confidence'):
            equivalences = equivalences.filter(
                confidence_score__gte=int(filters['min_confidence'])
            )
        
        results = []
        for eq in equivalences[:limit]:
            results.append({
                'type': 'equivalence',
                'id': eq.equivalence_id,
                'oem_part_number': eq.oem_part_number,
                'oem_brand': eq.oem_code.name if eq.oem_code else '',
                'aftermarket_sku': eq.aftermarket_sku,
                'equivalence_type': eq.equivalence_type,
                'confidence_score': eq.confidence_score,
                'verified': bool(eq.verified_date),
                'url': f'/oem/equivalences/{eq.equivalence_id}/',
                'search_highlight': self._highlight_match(
                    query, 
                    eq.aftermarket_sku or eq.oem_part_number
                )
            })
        
        return results
    
    def _search_equipment(self, query, filters, limit):
        """Search in Equipment (client vehicles/equipment)"""
        from core.models import Equipment, Client
        
        equipment = Equipment.objects.all()
        
        # Text search
        equipment = equipment.filter(
            Q(equipment_code__icontains=query) |
            Q(brand__icontains=query) |
            Q(model__icontains=query) |
            Q(vin__icontains=query) |
            Q(license_plate__icontains=query) |
            Q(serial_number__icontains=query)
        )
        
        # Apply filters
        if filters.get('brand'):
            equipment = equipment.filter(brand__icontains=filters['brand'])
        if filters.get('year'):
            equipment = equipment.filter(year=filters['year'])
        if filters.get('status'):
            equipment = equipment.filter(status=filters['status'])
        
        results = []
        for equip in equipment[:limit]:
            # Get client info
            client_info = None
            if equip.client_id:
                try:
                    client = Client.objects.get(client_id=equip.client_id)
                    client_info = {
                        'id': client.client_id,
                        'name': client.name,
                        'code': client.client_code
                    }
                except Client.DoesNotExist:
                    pass
            
            results.append({
                'type': 'equipment',
                'id': equip.equipment_id,
                'code': equip.equipment_code,
                'brand': equip.brand,
                'model': equip.model,
                'year': equip.year,
                'vin': equip.vin,
                'license_plate': equip.license_plate,
                'status': equip.status,
                'client': client_info,
                'url': f'/equipment/{equip.equipment_id}/',
                'search_highlight': self._highlight_match(
                    query, 
                    f"{equip.brand} {equip.model}" if equip.brand and equip.model else equip.equipment_code
                )
            })
        
        return results
    
    def _highlight_match(self, query, text):
        """Highlight matching text"""
        if not text or not query:
            return text
        
        text_lower = text.lower()
        query_lower = query.lower()
        start = text_lower.find(query_lower)
        
        if start != -1:
            end = start + len(query)
            return f"{text[:start]}<mark>{text[start:end]}</mark>{text[end:]}"
        
        return text
    
    def get_quick_suggestions(self, query, limit=5):
        """
        Get quick search suggestions for autocomplete.
        
        Args:
            query: Partial query string
            limit: Maximum suggestions per category
        
        Returns:
            dict with suggestions
        """
        if not query or len(query) < 2:
            return {'suggestions': []}
        
        suggestions = {
            'query': query,
            'suggestions': []
        }
        
        # Search products
        from core.models import ProductMaster
        products = ProductMaster.objects.filter(
            is_active=True,
            internal_sku__istartswith=query.upper()
        )[:limit]
        
        for product in products:
            suggestions['suggestions'].append({
                'type': 'product',
                'text': f"{product.internal_sku} - {product.name[:30]}",
                'url': f'/inventory/products/{product.internal_sku}/'
            })
        
        # Search OEM parts
        from core.models import OEMCatalogItem
        oem_parts = OEMCatalogItem.objects.filter(
            is_active=True,
            part_number__istartswith=query.upper()
        )[:limit]
        
        for part in oem_parts:
            suggestions['suggestions'].append({
                'type': 'oem',
                'text': f"{part.part_number} - {part.oem_code.name if part.oem_code else ''}",
                'url': f'/oem/catalog/{part.catalog_id}/'
            })
        
        return suggestions
    
    def get_search_statistics(self):
        """
        Get search/usage statistics.
        
        Returns:
            dict with statistics
        """
        from core.models import ProductMaster, OEMCatalogItem, OEMEquivalence, Equipment
        
        return {
            'products_count': ProductMaster.objects.filter(is_active=True).count(),
            'oem_items_count': OEMCatalogItem.objects.filter(is_active=True).count(),
            'equivalences_count': OEMEquivalence.objects.count(),
            'equipment_count': Equipment.objects.filter(status='ACTIVO').count(),
            'categories': {
                'products': 'Inventario de productos',
                'oem_items': 'Catálogo OEM',
                'equivalences': 'Equivalencias OEM ↔ Aftermarket',
                'equipment': 'Equipos/Vehículos'
            }
        }
    
    def clear_cache(self):
        """Clear the search cache"""
        # Clear all unified search cache keys
        cache.clear()
        logger.info("Unified search cache cleared")
        return True

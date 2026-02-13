"""
Unified Search Views - Views for unified search across all catalogs.
"""
import logging
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from ..services.unified_search_service import UnifiedSearchService

logger = logging.getLogger(__name__)


class UnifiedSearchView(LoginRequiredMixin, TemplateView):
    """
    Vista para búsqueda unificada en todos los catálogos.
    
    Permite buscar en:
    - Inventario (ProductMaster)
    - Catálogo OEM (OEMCatalogItem)
    - Equivalencias (OEMEquivalence)
    - Equipos (Equipment)
    """
    template_name = 'frontend/search/unified_search.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get search query
        query = self.request.GET.get('q', '').strip()
        search_type = self.request.GET.get('type', 'all')
        
        context.update({
            'query': query,
            'search_type': search_type,
            'search_types': [
                {'value': 'all', 'label': 'Todos'},
                {'value': 'products', 'label': 'Inventario'},
                {'value': 'oem', 'label': 'Catálogo OEM'},
                {'value': 'equivalences', 'label': 'Equivalencias'},
                {'value': 'equipment', 'label': 'Equipos'},
            ]
        })
        
        # Perform search if query provided
        if query and len(query) >= 2:
            service = UnifiedSearchService()
            filters = {}
            
            # Get filters from request
            brand_filter = self.request.GET.get('brand')
            if brand_filter:
                filters['brand'] = brand_filter
            
            results = service.search(query, search_type, filters)
            context['results'] = results
        
        return context


class UnifiedSearchAPIView(APIView):
    """
    API para búsqueda unificada.
    
    GET params:
    - q: Search query (required, min 2 chars)
    - type: Search type (all, products, oem, equivalences, equipment)
    - limit: Max results per category (default 50)
    """
    
    def get(self, request):
        """Handle search requests"""
        query = request.query_params.get('q', '').strip()
        search_type = request.query_params.get('type', 'all')
        limit = int(request.query_params.get('limit', 50))
        
        if not query:
            return Response({
                'error': 'Query parameter "q" is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if len(query) < 2:
            return Response({
                'error': 'Query must be at least 2 characters'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Build filters
        filters = {}
        brand_filter = request.query_params.get('brand')
        if brand_filter:
            filters['brand'] = brand_filter
        
        oem_code_filter = request.query_params.get('oem_code')
        if oem_code_filter:
            filters['oem_code'] = oem_code_filter
        
        # Perform search
        service = UnifiedSearchService(user=request.user)
        results = service.search(query, search_type, filters, limit)
        
        return Response(results)


class UnifiedSearchSuggestionsView(APIView):
    """
    API para obtener sugerencias de búsqueda (autocomplete).
    """
    
    def get(self, request):
        """Get search suggestions"""
        query = request.query_params.get('q', '').strip()
        limit = int(request.query_params.get('limit', 5))
        
        if not query or len(query) < 2:
            return Response({'suggestions': []})
        
        service = UnifiedSearchService()
        suggestions = service.get_quick_suggestions(query, limit)
        
        return Response(suggestions)


class UnifiedSearchStatsView(APIView):
    """
    API para obtener estadísticas de búsqueda.
    """
    
    def get(self, request):
        """Get search statistics"""
        service = UnifiedSearchService()
        stats = service.get_search_statistics()
        
        return Response(stats)


class UnifiedSearchCacheClearView(APIView):
    """
    API para limpiar caché de búsqueda.
    """
    
    def post(self, request):
        """Clear search cache"""
        service = UnifiedSearchService()
        success = service.clear_cache()
        
        if success:
            return Response({'message': 'Cache cleared successfully'})
        else:
            return Response(
                {'error': 'Failed to clear cache'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


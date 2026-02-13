"""
OEM Import Views - Views for importing OEM data to inventory.
"""
import logging
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import TemplateView, FormView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from core.models import OEMBrand, ProductMaster
from ..services.oem_integration_service import OEMIntegrationService
from ..mixins import APIClientMixin

logger = logging.getLogger(__name__)


class OEMImportView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """
    Vista para importar datos OEM a inventario.
    
    Funcionalidades:
    - Ver estado de importación por marca
    - Importar items individuales
    - Importar por marca (bulk)
    - Ver historial de importaciones
    """
    template_name = 'frontend/oem/oem_import.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get brands with statistics
        brands = self._get_brands_with_stats()
        
        # Get import service
        service = OEMIntegrationService(api_client=self.get_api_client())
        import_status = service.get_import_status()
        
        context.update({
            'brands': brands,
            'import_status': import_status,
            'total_products': ProductMaster.objects.filter(source_code='OEM').count(),
        })
        
        return context
    
    def _get_brands_with_stats(self):
        """Get OEM brands with import statistics"""
        brands = OEMBrand.objects.filter(is_active=True).order_by('name')
        
        result = []
        for brand in brands:
            result.append({
                'id': brand.brand_id,
                'code': brand.oem_code,
                'name': brand.name,
                'type': brand.brand_type,
                'country': brand.country,
            })
        
        return result
    
    def post(self, request, *args, **kwargs):
        """Handle import actions"""
        import_type = request.POST.get('import_type')
        
        service = OEMIntegrationService(api_client=self.get_api_client())
        
        try:
            if import_type == 'single':
                # Import single OEM item
                oem_catalog_item_id = request.POST.get('oem_catalog_item_id')
                supplier_id = request.POST.get('supplier_id')
                
                if not oem_catalog_item_id:
                    messages.error(request, 'ID de item OEM es requerido')
                    return self.get(request)
                
                product = service.import_oem_to_product_master(
                    oem_catalog_item_id,
                    supplier_id=supplier_id if supplier_id else None
                )
                
                messages.success(
                    request, 
                    f'Producto importado: {product.internal_sku}'
                )
            
            elif import_type == 'brand':
                # Import all items from a brand
                oem_brand_code = request.POST.get('oem_brand_code')
                supplier_id = request.POST.get('supplier_id')
                
                if not oem_brand_code:
                    messages.error(request, 'Código de marca OEM es requerido')
                    return self.get(request)
                
                result = service.bulk_import_by_brand(
                    oem_brand_code,
                    supplier_id=supplier_id if supplier_id else None
                )
                
                messages.success(
                    request, 
                    f'Importación completada: {result["imported"]} items, {result["skipped"]} omitidos'
                )
            
            elif import_type == 'sync_prices':
                # Sync prices from OEM
                oem_brand_code = request.POST.get('oem_brand_code')
                
                result = service.sync_prices_from_oem(oem_brand_code if oem_brand_code else None)
                
                messages.success(
                    request,
                    f'Precios sincronizados: {result["updated"]} productos actualizados'
                )
            
            else:
                messages.error(request, f'Tipo de importación desconocido: {import_type}')
        
        except Exception as e:
            logger.exception("Error during OEM import")
            messages.error(request, f'Error durante importación: {str(e)}')
        
        return self.get(request)


class OEMImportAPIView(APIView):
    """
    API para operaciones de importación OEM.
    """
    
    def get(self, request):
        """Get import status and statistics"""
        service = OEMIntegrationService()
        status_data = service.get_import_status()
        
        return Response(status_data)
    
    def post(self, request):
        """Handle import operations"""
        import_type = request.data.get('import_type')
        
        service = OEMIntegrationService()
        
        try:
            if import_type == 'single':
                oem_catalog_item_id = request.data.get('oem_catalog_item_id')
                supplier_id = request.data.get('supplier_id')
                
                if not oem_catalog_item_id:
                    return Response(
                        {'error': 'oem_catalog_item_id is required'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                product = service.import_oem_to_product_master(
                    oem_catalog_item_id,
                    supplier_id=supplier_id
                )
                
                return Response({
                    'message': 'Product imported successfully',
                    'product': {
                        'internal_sku': product.internal_sku,
                        'name': product.name,
                        'brand': product.brand,
                    }
                })
            
            elif import_type == 'brand':
                oem_brand_code = request.data.get('oem_brand_code')
                supplier_id = request.data.get('supplier_id')
                batch_size = request.data.get('batch_size', 100)
                
                if not oem_brand_code:
                    return Response(
                        {'error': 'oem_brand_code is required'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                result = service.bulk_import_by_brand(
                    oem_brand_code,
                    batch_size=batch_size,
                    supplier_id=supplier_id
                )
                
                return Response(result)
            
            elif import_type == 'sync_prices':
                oem_brand_code = request.data.get('oem_brand_code')
                
                result = service.sync_prices_from_oem(oem_brand_code)
                
                return Response(result)
            
            else:
                return Response(
                    {'error': f'Unknown import type: {import_type}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        except Exception as e:
            logger.exception("Error in OEM import API")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


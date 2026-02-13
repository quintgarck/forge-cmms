"""
Fitment Views - API views for equipment-product compatibility (fitment).
"""
import logging
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Sum, Count, Case, When, IntegerField
from django.shortcuts import get_object_or_404

from core.models import Fitment, Equipment, ProductMaster, OEMCatalogItem, OEMEquivalence
from core.serializers.main_serializers import FitmentSerializer

logger = logging.getLogger(__name__)


class FitmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing fitment (equipment-product compatibility).
    
    Provides CRUD operations and additional actions:
    - list: List all fitments with filtering
    - retrieve: Get single fitment details
    - create: Create new fitment
    - update: Update fitment
    - partial_update: Partial update fitment
    - delete: Delete fitment
    - by_equipment: Get fitments for specific equipment
    - by_product: Get fitments for specific product
    - auto_create: Auto-create fitments based on compatibility
    - bulk_create: Create multiple fitments at once
    """
    queryset = Fitment.objects.select_related(
        'equipment', 'verified_by'
    ).all()
    serializer_class = FitmentSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    
    filterset_fields = {
        'equipment__brand': ['exact', 'icontains'],
        'equipment__model': ['icontains'],
        'equipment__year': ['gte', 'lte', 'exact'],
        'equipment__equipment_id': ['exact'],
        'internal_sku': ['exact', 'icontains'],
        'score': ['gte', 'lte', 'exact'],
        'is_primary_fit': ['exact'],
    }
    
    search_fields = [
        'equipment__brand',
        'equipment__model',
        'internal_sku',
        'equipment__vin'
    ]
    
    ordering_fields = [
        'score',
        'created_at',
        'equipment__brand',
        'equipment__model'
    ]
    
    ordering = ['-score', '-created_at']
    
    def get_queryset(self):
        """Filter queryset based on query parameters"""
        queryset = super().get_queryset()
        
        # Filter by primary fit
        is_primary = self.request.query_params.get('is_primary')
        if is_primary is not None:
            queryset = queryset.filter(is_primary_fit=is_primary.lower() == 'true')
        
        # Filter by minimum score
        min_score = self.request.query_params.get('min_score')
        if min_score:
            queryset = queryset.filter(score__gte=int(min_score))
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def by_equipment(self, request):
        """
        Get all fitments for a specific equipment.
        Query params: equipment_id (required)
        """
        equipment_id = request.query_params.get('equipment_id')
        if not equipment_id:
            return Response(
                {'error': 'equipment_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            equipment = Equipment.objects.get(equipment_id=equipment_id)
        except Equipment.DoesNotExist:
            return Response(
                {'error': 'Equipment not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        fitments = self.get_queryset().filter(equipment=equipment)
        
        # Get equipment info
        equipment_info = {
            'id': equipment.equipment_id,
            'code': equipment.equipment_code,
            'brand': equipment.brand,
            'model': equipment.model,
            'year': equipment.year,
            'vin': equipment.vin,
        }
        
        # Get product details for each fitment
        fitment_data = []
        for fitment in fitments:
            product_info = None
            if fitment.internal_sku:
                try:
                    product = ProductMaster.objects.get(internal_sku=fitment.internal_sku)
                    product_info = {
                        'sku': product.internal_sku,
                        'name': product.name,
                        'brand': product.brand,
                        'oem_ref': product.oem_ref,
                    }
                except ProductMaster.DoesNotExist:
                    pass
            
            fitment_data.append({
                'fitment_id': fitment.fitment_id,
                'internal_sku': fitment.internal_sku,
                'product_info': product_info,
                'score': fitment.score,
                'is_primary': fitment.is_primary_fit,
                'notes': fitment.notes,
            })
        
        return Response({
            'equipment': equipment_info,
            'count': fitments.count(),
            'fitments': fitment_data
        })
    
    @action(detail=False, methods=['get'])
    def by_product(self, request):
        """
        Get all fitments for a specific product.
        Query params: internal_sku (required)
        """
        internal_sku = request.query_params.get('internal_sku')
        if not internal_sku:
            return Response(
                {'error': 'internal_sku parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            product = ProductMaster.objects.get(internal_sku=internal_sku)
        except ProductMaster.DoesNotExist:
            return Response(
                {'error': 'Product not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        fitments = self.get_queryset().filter(internal_sku=internal_sku)
        
        # Get product info
        product_info = {
            'sku': product.internal_sku,
            'name': product.name,
            'brand': product.brand,
            'oem_ref': product.oem_ref,
        }
        
        equipment_list = []
        for fitment in fitments:
            equipment_list.append({
                'fitment_id': fitment.fitment_id,
                'equipment': {
                    'id': fitment.equipment.equipment_id,
                    'code': fitment.equipment.equipment_code,
                    'brand': fitment.equipment.brand,
                    'model': fitment.equipment.model,
                    'year': fitment.equipment.year,
                },
                'score': fitment.score,
                'is_primary': fitment.is_primary_fit,
            })
        
        return Response({
            'product': product_info,
            'count': fitments.count(),
            'equipment': equipment_list
        })
    
    @action(detail=False, methods=['post'])
    def auto_create(self, request):
        """
        Auto-create fitments based on equipment compatibility.
        Body: {'equipment_id': int, 'category': str, 'oem_part_number': str}
        """
        equipment_id = request.data.get('equipment_id')
        if not equipment_id:
            return Response(
                {'error': 'equipment_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            equipment = Equipment.objects.get(equipment_id=equipment_id)
        except Equipment.DoesNotExist:
            return Response(
                {'error': 'Equipment not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        created_fitments = self._auto_create_fitments(equipment)
        
        return Response({
            'message': f'{len(created_fitments)} fitments created successfully',
            'equipment_id': equipment_id,
            'count': len(created_fitments)
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """
        Create multiple fitments at once.
        Body: {'fitments': [...]}
        """
        fitments_data = request.data.get('fitments', [])
        if not fitments_data:
            return Response(
                {'error': 'fitments list is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        created = []
        errors = []
        
        for i, fitment_data in enumerate(fitments_data):
            try:
                equipment_id = fitment_data.get('equipment_id')
                equipment = Equipment.objects.get(equipment_id=equipment_id)
                
                fitment = Fitment.objects.create(
                    internal_sku=fitment_data.get('internal_sku'),
                    equipment=equipment,
                    score=fitment_data.get('score', 50),
                    notes=fitment_data.get('notes', ''),
                    is_primary_fit=fitment_data.get('is_primary_fit', False),
                )
                created.append({
                    'fitment_id': fitment.fitment_id,
                    'equipment_id': equipment_id,
                    'internal_sku': fitment.internal_sku
                })
            except Exception as e:
                errors.append({
                    'index': i,
                    'error': str(e)
                })
        
        return Response({
            'message': f'{len(created)} fitments created',
            'created': created,
            'errors': errors if errors else None
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get fitment statistics.
        """
        queryset = self.get_queryset()
        
        stats = {
            'total': queryset.count(),
            'by_score_ranges': {
                'high': queryset.filter(score__gte=80).count(),
                'medium': queryset.filter(score__gte=50, score__lt=80).count(),
                'low': queryset.filter(score__lt=50).count(),
            },
            'primary_fit_count': queryset.filter(is_primary_fit=True).count(),
            'equipment_coverage': queryset.values('equipment').distinct().count(),
        }
        
        return Response(stats)
    
    def _auto_create_fitments(self, equipment):
        """Auto-create fitments based on equipment compatibility"""
        created = []
        
        # Strategy 1: Search by ProductMaster brand match
        products = ProductMaster.objects.filter(
            Q(brand__icontains=equipment.brand) |
            Q(oem_ref__icontains=equipment.model)
        ).filter(is_active=True)[:100]  # Limit results
        
        for product in products:
            score = self._calculate_compatibility_score(product, equipment)
            
            # Check if fitment already exists
            exists = Fitment.objects.filter(
                internal_sku=product.internal_sku,
                equipment=equipment
            ).exists()
            
            if not exists:
                fitment = Fitment.objects.create(
                    internal_sku=product.internal_sku,
                    equipment=equipment,
                    score=score,
                    is_primary_fit=score >= 90,
                    notes=f'Auto-creado por compatibilidad (brand match)'
                )
                created.append(fitment)
        
        # Strategy 2: Search by OEM Catalog Items
        oem_items = OEMCatalogItem.objects.filter(
            Q(oem_code__name__icontains=equipment.brand)
        ).filter(
            Q(year_start__isnull=True) | Q(year_start__lte=equipment.year),
            Q(year_end__isnull=True) | Q(year_end__gte=equipment.year)
        ).filter(is_active=True)[:50]
        
        for oem_item in oem_items:
            # Check if there's already a product for this OEM
            product = ProductMaster.objects.filter(
                oem_ref=oem_item.part_number
            ).first()
            
            if product:
                exists = Fitment.objects.filter(
                    internal_sku=product.internal_sku,
                    equipment=equipment
                ).exists()
                
                if not exists:
                    # Calculate score from OEM data
                    score = self._calculate_oem_compatibility_score(oem_item, equipment)
                    
                    fitment = Fitment.objects.create(
                        internal_sku=product.internal_sku,
                        equipment=equipment,
                        score=score,
                        is_primary_fit=score >= 90,
                        notes=f'Auto-creado desde catálogo OEM: {oem_item.part_number}'
                    )
                    created.append(fitment)
        
        logger.info(f'Auto-created {len(created)} fitments for equipment {equipment.equipment_code}')
        return created
    
    def _calculate_compatibility_score(self, product, equipment):
        """Calculate compatibility score between product and equipment"""
        score = 50  # Base score
        
        # Brand match
        if product.brand and equipment.brand:
            if product.brand.lower() == equipment.brand.lower():
                score += 30
        
        # OEM reference match
        if product.oem_ref:
            if equipment.model and equipment.model.lower() in product.oem_ref.lower():
                score += 10
            if equipment.vin and equipment.vin[:8] in product.oem_ref:
                score += 10
        
        return min(score, 100)
    
    def _calculate_oem_compatibility_score(self, oem_item, equipment):
        """Calculate compatibility score based on OEM catalog data"""
        score = 50
        
        # Brand match
        if oem_item.oem_code and oem_item.oem_code.name:
            if oem_item.oem_code.name.lower() == equipment.brand.lower():
                score += 30
        
        # Year range match
        if oem_item.year_start and oem_item.year_end:
            if oem_item.year_start <= equipment.year <= oem_item.year_end:
                score += 20
        elif oem_item.year_start:
            if oem_item.year_start <= equipment.year:
                score += 10
        
        return min(score, 100)


class FitmentAutoCreateByModelView(APIView):
    """
    API view to auto-create fitments for all equipment of a specific model.
    """
    
    def post(self, request):
        """Create fitments for all equipment matching criteria"""
        brand = request.data.get('brand')
        model_pattern = request.data.get('model_pattern')
        year = request.data.get('year')
        
        if not brand and not model_pattern:
            return Response(
                {'error': 'brand or model_pattern is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Build queryset for equipment
        equipment_qs = Equipment.objects.all()
        
        if brand:
            equipment_qs = equipment_qs.filter(brand__icontains=brand)
        if model_pattern:
            equipment_qs = equipment_qs.filter(model__icontains=model_pattern)
        if year:
            equipment_qs = equipment_qs.filter(year=year)
        
        total_created = 0
        errors = []
        
        for equipment in equipment_qs:
            try:
                # Use FitmentViewSet's auto_create method
                fitment_view = FitmentViewSet()
                fitment_view.request = request
                fitment_view.format_kwarg = None
                
                # Call the internal method
                created = fitment_view._auto_create_fitments(equipment)
                total_created += len(created)
            except Exception as e:
                errors.append({
                    'equipment_id': equipment.equipment_id,
                    'error': str(e)
                })
        
        return Response({
            'message': f'Fitments created: {total_created}',
            'equipment_processed': equipment_qs.count(),
            'total_created': total_created,
            'errors': errors if errors else None
        })


class FitmentCompatibilityCheckView(APIView):
    """
    API view to check if a specific product fits a specific equipment.
    """
    
    def get(self, request):
        """Check compatibility between product and equipment"""
        internal_sku = request.query_params.get('internal_sku')
        equipment_id = request.query_params.get('equipment_id')
        
        if not internal_sku or not equipment_id:
            return Response(
                {'error': 'internal_sku and equipment_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            product = ProductMaster.objects.get(internal_sku=internal_sku)
        except ProductMaster.DoesNotExist:
            return Response(
                {'error': 'Product not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            equipment = Equipment.objects.get(equipment_id=equipment_id)
        except Equipment.DoesNotExist:
            return Response(
                {'error': 'Equipment not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check existing fitment
        existing_fitment = Fitment.objects.filter(
            internal_sku=internal_sku,
            equipment=equipment_id
        ).first()
        
        if existing_fitment:
            return Response({
                'compatible': True,
                'fitment_id': existing_fitment.fitment_id,
                'score': existing_fitment.score,
                'is_primary': existing_fitment.is_primary_fit,
                'existing': True
            })
        
        # Calculate compatibility score
        fitment_view = FitmentViewSet()
        calculated_score = fitment_view._calculate_compatibility_score(product, equipment)
        
        return Response({
            'compatible': calculated_score >= 50,
            'score': calculated_score,
            'existing': False,
            'message': 'No existing fitment found. Would you like to create one?'
        })

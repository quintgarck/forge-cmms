"""
OEM Equivalence Views - API views for OEM to Aftermarket part equivalences.
"""
import logging
from django.utils import timezone
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.shortcuts import get_object_or_404

from core.models import OEMEquivalence, OEMBrand, Technician
from core.serializers.oem_serializers import (
    OEMEquivalenceSerializer,
    OEMEquivalenceCreateSerializer,
    OEMEquivalenceBulkCreateSerializer
)

logger = logging.getLogger(__name__)


class OEMEquivalenceViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing OEM to Aftermarket part equivalences.
    
    Provides CRUD operations and additional actions:
    - list: List all equivalences with filtering
    - retrieve: Get single equivalence details
    - create: Create new equivalence
    - update: Update equivalence
    - partial_update: Partial update equivalence
    - delete: Delete equivalence
    - by_oem: Get equivalences for specific OEM part number
    - by_aftermarket: Search equivalences by aftermarket SKU
    - bulk_create: Create multiple equivalences at once
    """
    queryset = OEMEquivalence.objects.select_related(
        'oem_code', 'verified_by'
    ).all()
    serializer_class = OEMEquivalenceSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    
    filterset_fields = {
        'oem_code__oem_code': ['exact'],
        'oem_code__name': ['icontains'],
        'oem_part_number': ['exact', 'icontains'],
        'equivalence_type': ['exact', 'in'],
        'confidence_score': ['gte', 'lte', 'exact'],
        'aftermarket_sku': ['exact', 'icontains'],
        'is_active': ['exact'],
    }
    
    search_fields = [
        'oem_part_number',
        'aftermarket_sku',
        'notes',
        'oem_code__name'
    ]
    
    ordering_fields = [
        'confidence_score',
        'created_at',
        'oem_part_number',
        'equivalence_type'
    ]
    
    ordering = ['-confidence_score', '-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action in ['create', 'update', 'partial_update', 'bulk_create']:
            return OEMEquivalenceCreateSerializer
        return OEMEquivalenceSerializer
    
    def get_queryset(self):
        """Filter queryset based on query parameters"""
        queryset = super().get_queryset()
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset
    
    def perform_create(self, serializer):
        """Handle equivalence creation with automatic verification tracking"""
        # Get the technician from the request (assumes authentication)
        technician = None
        if hasattr(self.request.user, 'technician'):
            technician = self.request.user.technician
        elif hasattr(self.request, 'tech_id'):
            try:
                technician = Technician.objects.get(technician_id=self.request.tech_id)
            except Technician.DoesNotExist:
                pass
        
        serializer.save(verified_by=technician)
        logger.info(f"OEM Equivalence created: {serializer.instance}")
    
    @action(detail=False, methods=['get'])
    def by_oem_part(self, request):
        """
        Get all equivalences for a specific OEM part number.
        Query params: oem_part (required)
        """
        oem_part = request.query_params.get('oem_part')
        if not oem_part:
            return Response(
                {'error': 'oem_part parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        equivalences = self.get_queryset().filter(
            oem_part_number__icontains=oem_part
        )
        
        serializer = self.get_serializer(equivalences, many=True)
        return Response({
            'oem_part_number': oem_part,
            'count': equivalences.count(),
            'results': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def by_aftermarket(self, request):
        """
        Search equivalences by aftermarket SKU.
        Query params: aftermarket (required)
        """
        aftermarket = request.query_params.get('aftermarket')
        if not aftermarket:
            return Response(
                {'error': 'aftermarket parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        equivalences = self.get_queryset().filter(
            aftermarket_sku__icontains=aftermarket
        )
        
        serializer = self.get_serializer(equivalences, many=True)
        return Response({
            'aftermarket_sku': aftermarket,
            'count': equivalences.count(),
            'results': serializer.data
        })
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """
        Create multiple equivalences at once.
        Body: {'equivalences': [...]}
        """
        serializer = OEMEquivalenceBulkCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        equivalences = serializer.save()
        output_serializer = self.get_serializer(equivalences, many=True)
        
        return Response(
            {
                'message': f'{len(equivalences)} equivalences created successfully',
                'results': output_serializer.data
            },
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['get'])
    def by_confidence(self, request):
        """
        Get equivalences filtered by confidence score range.
        Query params: min_confidence, max_confidence
        """
        min_conf = request.query_params.get('min_confidence', '0')
        max_conf = request.query_params.get('max_confidence', '100')
        
        try:
            min_conf = int(min_conf)
            max_conf = int(max_conf)
        except ValueError:
            return Response(
                {'error': 'Invalid confidence score values'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        equivalences = self.get_queryset().filter(
            confidence_score__gte=min_conf,
            confidence_score__lte=max_conf
        )
        
        serializer = self.get_serializer(equivalences, many=True)
        return Response({
            'min_confidence': min_conf,
            'max_confidence': max_conf,
            'count': equivalences.count(),
            'results': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get statistics about equivalences.
        """
        queryset = self.get_queryset()
        
        stats = {
            'total': queryset.count(),
            'by_type': {},
            'by_confidence_ranges': {
                'high': queryset.filter(confidence_score__gte=80).count(),
                'medium': queryset.filter(
                    confidence_score__gte=50, 
                    confidence_score__lt=80
                ).count(),
                'low': queryset.filter(confidence_score__lt=50).count(),
            },
            'top_brands': [],
        }
        
        # Count by equivalence type
        for eq_type, eq_label in OEMEquivalence.EQUIVALENCE_TYPES:
            stats['by_type'][eq_type] = queryset.filter(
                equivalence_type=eq_type
            ).count()
        
        # Top brands with most equivalences
        from django.db.models import Count
        top_brands = queryset.values('oem_code__name').annotate(
            count=Count('equivalence_id')
        ).order_by('-count')[:5]
        
        stats['top_brands'] = list(top_brands)
        
        return Response(stats)
    
    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """
        Mark an equivalence as verified.
        Body: {'notes': '...'}
        """
        equivalence = get_object_or_404(self.get_queryset(), pk=pk)
        
        technician = None
        if hasattr(self.request.user, 'technician'):
            technician = self.request.user.technician
        
        equivalence.verified_by = technician
        equivalence.verified_date = timezone.now().date()
        if 'notes' in request.data:
            equivalence.notes = request.data.get('notes')
        
        equivalence.save()
        
        serializer = self.get_serializer(equivalence)
        return Response({
            'message': 'Equivalence verified successfully',
            'equivalence': serializer.data
        })
    
    def destroy(self, request, *args, **kwargs):
        """Log deletion of equivalences"""
        instance = self.get_object()
        oem_part = instance.oem_part_number
        aftermarket = instance.aftermarket_sku or 'N/A'
        
        logger.info(f"OEM Equivalence deleted: {oem_part} -> {aftermarket}")
        
        return super().destroy(request, *args, **kwargs)


class OEMEquivalenceSearchView(APIView):
    """
    API view for searching equivalences with advanced filtering.
    """
    
    def get(self, request):
        """Handle search requests"""
        query = request.query_params.get('q', '').strip()
        search_type = request.query_params.get('type', 'all')
        
        if not query:
            return Response({
                'error': 'Search query "q" is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        queryset = OEMEquivalence.objects.select_related('oem_code')
        results = []
        
        if search_type in ['all', 'oem']:
            # Search by OEM part number
            oem_results = queryset.filter(
                Q(oem_part_number__icontains=query) |
                Q(oem_code__name__icontains=query)
            )
            results.extend([
                {
                    'type': 'oem',
                    'part_number': eq.oem_part_number,
                    'brand': eq.oem_code.name,
                    'confidence': eq.confidence_score,
                    'url': f'/api/oem/equivalences/{eq.equivalence_id}/'
                }
                for eq in oem_results[:20]
            ])
        
        if search_type in ['all', 'aftermarket']:
            # Search by aftermarket SKU
            aftermarket_results = queryset.filter(
                aftermarket_sku__icontains=query
            )
            results.extend([
                {
                    'type': 'aftermarket',
                    'aftermarket_sku': eq.aftermarket_sku,
                    'oem_part': eq.oem_part_number,
                    'brand': eq.oem_code.name,
                    'confidence': eq.confidence_score,
                    'url': f'/api/oem/equivalences/{eq.equivalence_id}/'
                }
                for eq in aftermarket_results[:20]
            ])
        
        return Response({
            'query': query,
            'type': search_type,
            'count': len(results),
            'results': results
        })


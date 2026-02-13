"""
ForgeDB API REST - OEM Views
Automotive Workshop Management System
"""

from rest_framework import viewsets, permissions
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from ..models import OEMBrand, OEMCatalogItem, OEMEquivalence
from ..serializers import (
    OEMBrandSerializer, OEMCatalogItemSerializer, OEMEquivalenceSerializer
)


class OEMBrandViewSet(viewsets.ModelViewSet):
    """ViewSet for managing OEM Brands"""
    queryset = OEMBrand.objects.all()
    serializer_class = OEMBrandSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active', 'country']
    search_fields = ['oem_code', 'name', 'country']
    ordering = ['name']


class OEMCatalogItemViewSet(viewsets.ModelViewSet):
    """ViewSet for managing OEM Catalog Items"""
    queryset = OEMCatalogItem.objects.all().select_related('oem_code', 'group_code')
    serializer_class = OEMCatalogItemSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]  # Allow read without auth for debugging
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['oem_code', 'group_code', 'is_discontinued', 'is_active', 'item_type']
    search_fields = ['part_number', 'description_es', 'description_en']
    ordering_fields = ['oem_code', 'part_number', 'created_at']
    ordering = ['oem_code', 'part_number']


class OEMEquivalenceViewSet(viewsets.ModelViewSet):
    """ViewSet for managing OEM Equivalences"""
    queryset = OEMEquivalence.objects.all().select_related('oem_code', 'verified_by')
    serializer_class = OEMEquivalenceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['oem_code', 'equivalence_type', 'verified_by']
    search_fields = ['oem_part_number', 'aftermarket_sku', 'notes']
    ordering_fields = ['oem_code', 'oem_part_number', 'confidence_score']
    ordering = ['oem_code', 'oem_part_number']


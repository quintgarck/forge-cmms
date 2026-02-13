"""
ForgeDB API REST - Product Master Views
Automotive Workshop Management System
"""

from rest_framework import viewsets, permissions
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from ..models import ProductMaster
from ..serializers import ProductMasterSerializer
from ..permissions import CanManageInventory


class ProductMasterViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Product Master records.
    
    Provides CRUD operations for product master records with appropriate permissions,
    filtering, search, and ordering capabilities.
    """
    queryset = ProductMaster.objects.all()
    serializer_class = ProductMasterSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageInventory]
    
    # Filtering, search, and ordering
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['group_code', 'brand']
    search_fields = ['product_code', 'barcode', 'name', 'description']
    ordering_fields = ['product_code', 'name', 'created_at', 'updated_at']
    ordering = ['product_code']
    
    def perform_create(self, serializer):
        """Save the product master record"""
        serializer.save()
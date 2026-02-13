"""
ForgeDB API REST - Warehouse Views
Automotive Workshop Management System
"""

from rest_framework import viewsets, permissions
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from ..models import Warehouse
from ..serializers import WarehouseSerializer
from ..permissions import CanManageInventory


class WarehouseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Warehouses.
    
    Provides CRUD operations for warehouse records with appropriate permissions,
    filtering, search, and ordering capabilities.
    """
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageInventory]
    
    # Filtering, search, and ordering
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active', 'type']
    search_fields = ['warehouse_code', 'name', 'description']
    ordering_fields = ['warehouse_code', 'name', 'created_at']
    ordering = ['warehouse_code']
    
    def perform_create(self, serializer):
        """Save the warehouse record"""
        serializer.save()
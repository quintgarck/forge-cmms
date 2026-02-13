"""
ForgeDB API REST - Stock Views
Automotive Workshop Management System
"""

from rest_framework import viewsets, permissions
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from ..models import Stock
from ..serializers import StockSerializer
from ..permissions import CanManageInventory


class StockViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Stock records.
    
    Provides CRUD operations for stock records with appropriate permissions,
    filtering, search, and ordering capabilities.
    """
    queryset = Stock.objects.all().select_related('warehouse', 'product')
    serializer_class = StockSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageInventory]
    
    # Filtering, search, and ordering
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['warehouse', 'product', 'qty_on_hand', 'qty_reserved']
    search_fields = ['product__product_code', 'product__name']
    ordering_fields = ['qty_on_hand', 'qty_reserved', 'last_movement_date', 'created_at']
    ordering = ['-last_movement_date']
    
    def perform_create(self, serializer):
        """Save the stock record"""
        serializer.save()
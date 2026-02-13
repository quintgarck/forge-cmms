"""
ForgeDB API REST - Additional Inventory Views
Automotive Workshop Management System
"""

from rest_framework import viewsets, permissions
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from ..models import Bin, PriceList, ProductPrice, PurchaseOrder, POItem
from ..serializers import (
    BinSerializer, PriceListSerializer, ProductPriceSerializer,
    PurchaseOrderSerializer, POItemSerializer
)


class BinViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Bins"""
    queryset = Bin.objects.all().select_related('warehouse_code')
    serializer_class = BinSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['warehouse_code', 'zone', 'is_active', 'hazard_level']
    search_fields = ['bin_code', 'description', 'zone', 'aisle']
    ordering_fields = ['warehouse_code', 'zone', 'aisle', 'rack', 'level']
    ordering = ['warehouse_code', 'zone', 'aisle', 'rack', 'level', 'position']


class PriceListViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Price Lists"""
    queryset = PriceList.objects.all()
    serializer_class = PriceListSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['currency_code', 'is_active', 'is_tax_included']
    search_fields = ['price_list_code', 'name', 'description']
    ordering_fields = ['price_list_code', 'name', 'created_at']
    ordering = ['price_list_code']


class ProductPriceViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Product Prices"""
    queryset = ProductPrice.objects.all().select_related('price_list')
    serializer_class = ProductPriceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['price_list', 'internal_sku']
    ordering_fields = ['price_list', 'internal_sku', 'valid_from']
    ordering = ['price_list', 'internal_sku', '-valid_from']


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Purchase Orders"""
    queryset = PurchaseOrder.objects.all().select_related('supplier', 'created_by', 'approved_by')
    serializer_class = PurchaseOrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['supplier', 'status', 'created_by', 'approved_by']
    search_fields = ['po_number', 'notes']
    ordering_fields = ['order_date', 'po_number', 'created_at']
    ordering = ['-order_date', 'po_number']


class POItemViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Purchase Order Items"""
    queryset = POItem.objects.all().select_related('po')
    serializer_class = POItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['po', 'internal_sku']
    ordering = ['po', 'po_item_id']


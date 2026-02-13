"""
ForgeDB API REST - Additional Service Views
Automotive Workshop Management System
"""

from rest_framework import viewsets, permissions
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from ..models import (
    WOItem, WOService, FlatRateStandard, ServiceChecklist,
    InvoiceItem, Payment, Quote, QuoteItem
)
from ..serializers import (
    WOItemSerializer, WOServiceSerializer, FlatRateStandardSerializer,
    ServiceChecklistSerializer, InvoiceItemSerializer, PaymentSerializer,
    QuoteSerializer, QuoteItemSerializer
)


class WOItemViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Work Order Items"""
    queryset = WOItem.objects.all().select_related('wo')
    serializer_class = WOItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['wo', 'internal_sku', 'status']
    ordering = ['wo', 'item_id']


class WOServiceViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Work Order Services"""
    queryset = WOService.objects.all().select_related('wo', 'flat_rate', 'technician')
    serializer_class = WOServiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['wo', 'technician', 'completion_status', 'flat_rate']
    search_fields = ['description', 'service_code']
    ordering_fields = ['wo', 'service_id', 'created_at']
    ordering = ['wo', 'service_id']


class FlatRateStandardViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Flat Rate Standards"""
    queryset = FlatRateStandard.objects.all().select_related('equipment_type', 'group_code')
    serializer_class = FlatRateStandardSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['equipment_type', 'group_code', 'is_active']
    search_fields = ['service_code', 'description_es', 'description_en']
    ordering = ['service_code']


class ServiceChecklistViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Service Checklists"""
    queryset = ServiceChecklist.objects.all().select_related('flat_rate')
    serializer_class = ServiceChecklistSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['flat_rate', 'is_critical']
    search_fields = ['description', 'expected_result', 'tool_required']
    ordering_fields = ['flat_rate', 'sequence_no']
    ordering = ['flat_rate', 'sequence_no']


class InvoiceItemViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Invoice Items"""
    queryset = InvoiceItem.objects.all().select_related('invoice')
    serializer_class = InvoiceItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['invoice', 'internal_sku']
    search_fields = ['description']
    ordering = ['invoice', 'invoice_item_id']


class PaymentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Payments"""
    queryset = Payment.objects.all().select_related('invoice')
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['invoice', 'payment_method', 'currency_code']
    search_fields = ['reference_number', 'notes']
    ordering_fields = ['payment_date', 'created_at']
    ordering = ['-payment_date', 'invoice']


class QuoteViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Quotes"""
    queryset = Quote.objects.all().select_related('client', 'equipment', 'created_by', 'converted_to_wo').prefetch_related('items')
    serializer_class = QuoteSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['client', 'equipment', 'status', 'created_by']
    search_fields = ['quote_number', 'notes']
    ordering_fields = ['quote_date', 'created_at', 'total']
    ordering = ['-quote_date', '-quote_number']


class QuoteItemViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Quote Items"""
    queryset = QuoteItem.objects.all().select_related('quote', 'flat_rate')
    serializer_class = QuoteItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['quote', 'flat_rate', 'service_code']
    search_fields = ['description', 'service_code']
    ordering = ['quote', 'quote_item_id']

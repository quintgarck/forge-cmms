"""
ForgeDB API REST - Invoice Views
Automotive Workshop Management System
"""

from rest_framework import viewsets, permissions
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from ..models import Invoice
from ..serializers import InvoiceSerializer
from ..permissions import IsTechnicianOrReadOnly
from ..pagination import OptimizedCursorPagination


class InvoiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Invoices.
    
    Provides CRUD operations for invoice records with appropriate permissions,
    filtering, search, and ordering capabilities.
    """
    queryset = Invoice.objects.all().prefetch_related('invoiceitem_set', 'payment_set')
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated, IsTechnicianOrReadOnly]
    pagination_class = OptimizedCursorPagination
    
    # Filtering, search, and ordering
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'client_id', 'wo_id']
    search_fields = ['invoice_number', 'notes']
    ordering_fields = ['issue_date', 'due_date', 'total_amount', 'created_at']
    ordering = ['-issue_date']
    
    def perform_create(self, serializer):
        """Invoice creation without created_by field"""
        serializer.save()
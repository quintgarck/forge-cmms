"""
ForgeDB API REST - Transaction Views
Automotive Workshop Management System
"""

from rest_framework import viewsets, permissions
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from ..models import Transaction
from ..serializers import TransactionSerializer
from ..permissions import CanManageInventory
from ..pagination import OptimizedCursorPagination


class TransactionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Transaction records.
    
    Provides CRUD operations for transaction records with appropriate permissions,
    filtering, search, and ordering capabilities.
    """
    queryset = Transaction.objects.all().select_related('warehouse', 'product', 'created_by')
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageInventory]
    pagination_class = OptimizedCursorPagination
    
    # Filtering, search, and ordering
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['transaction_type', 'warehouse', 'product', 'reference_type']
    search_fields = ['reference_number', 'notes']
    ordering_fields = ['transaction_date', 'quantity', 'total_cost']
    ordering = ['-transaction_date']
    
    def perform_create(self, serializer):
        """Set created_by to current user on creation"""
        serializer.save(created_by=self.request.user)
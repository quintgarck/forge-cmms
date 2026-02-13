"""
ForgeDB API REST - Work Order Views
Automotive Workshop Management System
"""

from rest_framework import viewsets, permissions
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from ..models import WorkOrder
from ..serializers import WorkOrderSerializer
from ..permissions import IsTechnicianOrReadOnly
from ..pagination import OptimizedCursorPagination


class WorkOrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Work Orders.
    
    Provides CRUD operations for work order records with appropriate permissions,
    filtering, search, and ordering capabilities.
    """
    queryset = WorkOrder.objects.all().prefetch_related('invoiceitem_set', 'transaction_set')
    serializer_class = WorkOrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsTechnicianOrReadOnly]
    pagination_class = OptimizedCursorPagination
    
    # Filtering, search, and ordering
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'priority', 'client_id', 'equipment_id', 'technician_id']
    search_fields = ['wo_number', 'description', 'complaint', 'resolution']
    ordering_fields = ['created_at', 'updated_at', 'appointment_date', 'actual_completion_date']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        """Set created_by to current user ID on creation"""
        user_id = self.request.user.id if self.request.user.is_authenticated else None
        serializer.save(created_by=user_id)
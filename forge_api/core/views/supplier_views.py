"""
ForgeDB API REST - Supplier Views
Automotive Workshop Management System
"""

from rest_framework import viewsets, permissions
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from ..models import Supplier
from ..serializers import SupplierSerializer


class SupplierViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Suppliers"""
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'is_active', 'is_preferred', 'country']
    search_fields = ['supplier_code', 'name', 'contact_person', 'contact_email', 'contact_phone']
    ordering_fields = ['name', 'supplier_code', 'created_at', 'rating']
    ordering = ['name']
    
    def perform_create(self, serializer):
        """Save the supplier record"""
        serializer.save()
    
    def perform_update(self, serializer):
        """Update the supplier record"""
        serializer.save()


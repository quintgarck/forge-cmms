"""
ForgeDB API REST - Equipment Views
Automotive Workshop Management System
"""

from rest_framework import viewsets, permissions
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from ..models import Equipment
from ..serializers import EquipmentSerializer
from ..permissions import CanManageClients


class EquipmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Equipment (vehicles).
    
    Provides CRUD operations for equipment records with appropriate permissions,
    filtering, search, and ordering capabilities.
    """
    queryset = Equipment.objects.all()
    serializer_class = EquipmentSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageClients]
    
    # Filtering, search, and ordering
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['client_id', 'status', 'year', 'brand', 'model', 'fuel_code']
    search_fields = ['equipment_code', 'vin', 'license_plate', 'brand', 'model']
    ordering_fields = ['year', 'brand', 'model', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        """Save the equipment record"""
        serializer.save()
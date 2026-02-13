"""
ForgeDB API REST - Fitment Views
Automotive Workshop Management System
"""

from rest_framework import viewsets, permissions
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from ..models import Fitment
from ..serializers import FitmentSerializer


class FitmentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Fitments"""
    queryset = Fitment.objects.all().select_related('equipment', 'verified_by')
    serializer_class = FitmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['equipment', 'is_primary_fit', 'verified_by']
    search_fields = ['internal_sku', 'notes']
    ordering_fields = ['equipment', 'score', 'created_at']
    ordering = ['equipment', '-is_primary_fit', '-score']
    
    def perform_create(self, serializer):
        """Save the fitment record"""
        serializer.save()


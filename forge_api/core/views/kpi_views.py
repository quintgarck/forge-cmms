"""
ForgeDB API REST - KPI Views
Automotive Workshop Management System
"""

from rest_framework import viewsets, permissions
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from ..models import WOMetric
from ..serializers import WOMetricSerializer


class WOMetricViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Work Order Metrics"""
    queryset = WOMetric.objects.all().select_related('wo')
    serializer_class = WOMetricSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['wo']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']


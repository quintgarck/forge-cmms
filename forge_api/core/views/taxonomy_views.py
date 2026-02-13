"""
ForgeDB API REST - Taxonomy Views
Automotive Workshop Management System
"""

from rest_framework import viewsets, permissions
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db import models

from ..models import TaxonomySystem, TaxonomySubsystem, TaxonomyGroup
from ..serializers import (
    TaxonomySystemSerializer, TaxonomySubsystemSerializer, TaxonomyGroupSerializer
)


class TaxonomySystemViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Taxonomy Systems"""
    queryset = TaxonomySystem.objects.prefetch_related(
        'taxonomysubsystem_set',  # Prefetch subsystems to avoid N+1
    ).annotate(
        subsystems_count=models.Count('taxonomysubsystem', distinct=True)
    )
    serializer_class = TaxonomySystemSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['system_code', 'name_es', 'name_en']
    ordering_fields = ['sort_order', 'system_code', 'category']
    ordering = ['sort_order', 'system_code']
    
    def get_serializer_class(self):
        # Use different serializers for list vs detail
        if self.action == 'list':
            from ..serializers import TaxonomySystemListSerializer
            return TaxonomySystemListSerializer
        return TaxonomySystemSerializer


class TaxonomySubsystemViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Taxonomy Subsystems"""
    queryset = TaxonomySubsystem.objects.select_related(
        'system_code'
    ).prefetch_related(
        'taxonomygroup_set'  # Prefetch groups to avoid N+1
    ).annotate(
        groups_count=models.Count('taxonomygroup', distinct=True)
    )
    serializer_class = TaxonomySubsystemSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['system_code']
    search_fields = ['subsystem_code', 'name_es', 'name_en']
    ordering_fields = ['system_code', 'sort_order', 'subsystem_code']
    ordering = ['system_code', 'sort_order', 'subsystem_code']
    
    def get_serializer_class(self):
        # Use different serializers for list vs detail
        if self.action == 'list':
            from ..serializers import TaxonomySubsystemListSerializer
            return TaxonomySubsystemListSerializer
        return TaxonomySubsystemSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Optimize for list view
        if self.action == 'list':
            queryset = queryset.only(
                'subsystem_code', 'system_code', 'name_es', 'name_en',
                'sort_order', 'created_at'
            )
        return queryset


class TaxonomyGroupViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Taxonomy Groups"""
    queryset = TaxonomyGroup.objects.select_related(
        'subsystem_code', 'system_code'
    ).annotate(
        # Add any calculated fields if needed
        full_path=models.F('system_code__name_es')
    )
    serializer_class = TaxonomyGroupSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['system_code', 'subsystem_code', 'is_active']
    search_fields = ['group_code', 'name_es', 'name_en', 'description']
    ordering_fields = ['system_code', 'subsystem_code', 'name_es']
    ordering = ['system_code', 'subsystem_code', 'name_es']
    
    def get_serializer_class(self):
        # Use different serializers for list vs detail
        if self.action == 'list':
            from ..serializers import TaxonomyGroupListSerializer
            return TaxonomyGroupListSerializer
        return TaxonomyGroupSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Optimize for list view
        if self.action == 'list':
            queryset = queryset.only(
                'group_code', 'subsystem_code', 'system_code',
                'name_es', 'name_en', 'description', 'is_active',
                'requires_position', 'requires_color', 'requires_finish', 
                'requires_side', 'sort_order', 'created_at', 'updated_at'
            )
        return queryset


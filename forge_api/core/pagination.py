"""
Custom pagination classes for ForgeDB API.

Provides optimized pagination for large datasets with cursor-based pagination
and enhanced page number pagination.
"""
from rest_framework.pagination import PageNumberPagination, CursorPagination
from rest_framework.response import Response
from collections import OrderedDict


class OptimizedPageNumberPagination(PageNumberPagination):
    """
    Enhanced page number pagination with configurable page size
    and optimized metadata.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        """Return paginated response with enhanced metadata."""
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('page_size', self.page_size),
            ('current_page', self.page.number),
            ('total_pages', self.page.paginator.num_pages),
            ('results', data)
        ]))


class LargeResultsSetPagination(PageNumberPagination):
    """
    Pagination for large result sets (50 items per page).
    """
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


class OptimizedCursorPagination(CursorPagination):
    """
    Cursor-based pagination for very large datasets.
    
    Benefits:
    - Constant time complexity O(1) for pagination
    - Works well with real-time data
    - Prevents "page drift" when new items are added
    
    Use for:
    - Work orders list
    - Invoices list
    - Transaction history
    - Audit logs
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    ordering = '-created_at'  # Default ordering
    
    def get_paginated_response(self, data):
        """Return cursor-paginated response with metadata."""
        return Response(OrderedDict([
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('page_size', self.page_size),
            ('results', data)
        ]))


class SmallResultsSetPagination(PageNumberPagination):
    """
    Pagination for small result sets (10 items per page).
    
    Use for:
    - Dashboard recent items
    - Notifications
    - Alerts
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50

"""
ForgeDB API REST - Stored Procedures Views
API endpoints that execute PostgreSQL stored procedures and functions

This module provides API endpoints for executing the complex business logic
implemented as stored procedures in the ForgeDB PostgreSQL database.
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import connection
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import json
import logging

from ..authentication import CanManageInventory, IsTechnicianOrReadOnly

logger = logging.getLogger(__name__)


@swagger_auto_schema(
    method='post',
    operation_description="Reserve stock for work order",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['wo_id', 'internal_sku', 'qty_needed'],
        properties={
            'wo_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Work order ID'),
            'internal_sku': openapi.Schema(type=openapi.TYPE_STRING, description='Product SKU'),
            'qty_needed': openapi.Schema(type=openapi.TYPE_NUMBER, description='Quantity needed'),
            'warehouse_code': openapi.Schema(type=openapi.TYPE_STRING, description='Warehouse code (optional)')
        }
    ),
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'stock_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'reserved_qty': openapi.Schema(type=openapi.TYPE_INTEGER),
                'wo_item_id': openapi.Schema(type=openapi.TYPE_INTEGER)
            }
        ),
        400: 'Bad request',
        401: 'Unauthorized',
        403: 'Insufficient permissions'
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, CanManageInventory])
def reserve_stock(request):
    """
    Reserve stock for a work order
    """
    try:
        wo_id = request.data.get('wo_id')
        internal_sku = request.data.get('internal_sku')
        qty_needed = request.data.get('qty_needed')
        warehouse_code = request.data.get('warehouse_code')

        if not all([wo_id, internal_sku, qty_needed]):
            return Response(
                {'error': 'wo_id, internal_sku, and qty_needed are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        with connection.cursor() as cursor:
            cursor.callproc('inv.reserve_stock_for_wo', [wo_id, internal_sku, qty_needed, warehouse_code])
            result = cursor.fetchone()

            if result and len(result) > 0:
                return Response(json.loads(result[0]), status=status.HTTP_200_OK)
            else:
                return Response(
                    {'error': 'No result returned from stored procedure'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

    except Exception as e:
        logger.error(f"Error reserving stock: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Import endpoints from other modules
from .inventory_stored_procedures_views import (
    release_reserved_stock,
    auto_replenishment,
    calculate_inventory_aging
)

from .workorder_stored_procedures_views import (
    advance_work_order_status,
    add_service_to_work_order,
    create_invoice_from_work_order
)

from .analytics_stored_procedures_views import (
    abc_analysis_inventory,
    technician_productivity_report,
    demand_forecasting,
    financial_kpi_dashboard
)
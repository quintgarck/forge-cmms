"""
ForgeDB API REST - Inventory Services Views
API endpoints for executing PostgreSQL stored procedures related to inventory management
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
    operation_description="Release reserved stock",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['wo_id', 'internal_sku'],
        properties={
            'wo_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Work order ID'),
            'internal_sku': openapi.Schema(type=openapi.TYPE_STRING, description='Product SKU'),
            'warehouse_code': openapi.Schema(type=openapi.TYPE_STRING, description='Warehouse code (optional)')
        }
    ),
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'released_qty': openapi.Schema(type=openapi.TYPE_INTEGER),
                'available_qty': openapi.Schema(type=openapi.TYPE_INTEGER)
            }
        ),
        400: 'Bad request',
        401: 'Unauthorized',
        403: 'Insufficient permissions'
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, CanManageInventory])
def release_reserved_stock(request):
    """
    Release previously reserved stock
    """
    try:
        wo_id = request.data.get('wo_id')
        internal_sku = request.data.get('internal_sku')
        warehouse_code = request.data.get('warehouse_code')

        if not all([wo_id, internal_sku]):
            return Response(
                {'error': 'wo_id and internal_sku are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        with connection.cursor() as cursor:
            cursor.callproc('inv.release_reserved_stock_for_wo', [wo_id, internal_sku, warehouse_code])
            result = cursor.fetchone()

            if result and len(result) > 0:
                return Response(json.loads(result[0]), status=status.HTTP_200_OK)
            else:
                return Response(
                    {'error': 'No result returned from stored procedure'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

    except Exception as e:
        logger.error(f"Error releasing reserved stock: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='post',
    operation_description="Automatic replenishment based on stock levels",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'warehouse_code': openapi.Schema(type=openapi.TYPE_STRING, description='Warehouse code (optional)'),
            'auto_order_threshold': openapi.Schema(type=openapi.TYPE_NUMBER, description='Threshold to trigger auto-order')
        }
    ),
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'items_processed': openapi.Schema(type=openapi.TYPE_INTEGER),
                'orders_created': openapi.Schema(type=openapi.TYPE_INTEGER),
                'items_ordered': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING))
            }
        ),
        400: 'Bad request',
        401: 'Unauthorized',
        403: 'Insufficient permissions'
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, CanManageInventory])
def auto_replenishment(request):
    """
    Trigger automatic replenishment based on stock levels
    """
    try:
        warehouse_code = request.data.get('warehouse_code')
        auto_order_threshold = request.data.get('auto_order_threshold', 0.8)

        with connection.cursor() as cursor:
            cursor.callproc('inv.auto_replenishment', [warehouse_code, auto_order_threshold])
            result = cursor.fetchone()

            if result and len(result) > 0:
                return Response(json.loads(result[0]), status=status.HTTP_200_OK)
            else:
                return Response(
                    {'error': 'No result returned from stored procedure'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

    except Exception as e:
        logger.error(f"Error in auto replenishment: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_description="Calculate inventory aging report",
    manual_parameters=[
        openapi.Parameter(
            'warehouse_code', 
            openapi.IN_QUERY, 
            description="Warehouse code to filter", 
            type=openapi.TYPE_STRING
        ),
        openapi.Parameter(
            'months', 
            openapi.IN_QUERY, 
            description="Number of months to consider", 
            type=openapi.TYPE_INTEGER,
            default=12
        )
    ],
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Items(
                type=openapi.TYPE_OBJECT,
                properties={
                    'internal_sku': openapi.Schema(type=openapi.TYPE_STRING),
                    'product_name': openapi.Schema(type=openapi.TYPE_STRING),
                    'warehouse_code': openapi.Schema(type=openapi.TYPE_STRING),
                    'quantity': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'age_days': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'age_category': openapi.Schema(type=openapi.TYPE_STRING),
                    'valuation': openapi.Schema(type=openapi.TYPE_NUMBER)
                }
            )
        ),
        400: 'Bad request',
        401: 'Unauthorized',
        403: 'Insufficient permissions'
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated, CanManageInventory])
def calculate_inventory_aging(request):
    """
    Calculate and return inventory aging report
    """
    try:
        warehouse_code = request.query_params.get('warehouse_code')
        months = request.query_params.get('months', 12)

        with connection.cursor() as cursor:
            cursor.callproc('inv.calculate_inventory_age', [warehouse_code, months])
            results = []
            for row in cursor.fetchall():
                if len(row) > 0 and row[0]:
                    results.append(json.loads(row[0]))

            return Response(results, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error calculating inventory aging: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
"""
ForgeDB API REST - Work Order Services Views
API endpoints for executing PostgreSQL stored procedures related to work order management
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

from ..authentication import IsWorkshopAdmin, IsTechnicianOrReadOnly

logger = logging.getLogger(__name__)


@swagger_auto_schema(
    method='post',
    operation_description="Advance work order status",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['wo_id', 'new_status'],
        properties={
            'wo_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Work order ID'),
            'new_status': openapi.Schema(type=openapi.TYPE_STRING, description='New status for the work order'),
            'notes': openapi.Schema(type=openapi.TYPE_STRING, description='Additional notes'),
            'completed_date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, description='Completion date (if status is completed)')
        }
    ),
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'old_status': openapi.Schema(type=openapi.TYPE_STRING),
                'new_status': openapi.Schema(type=openapi.TYPE_STRING),
                'timestamp': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                'updated_by': openapi.Schema(type=openapi.TYPE_INTEGER)
            }
        ),
        400: 'Bad request',
        401: 'Unauthorized',
        403: 'Insufficient permissions'
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsWorkshopAdmin])
def advance_work_order_status(request):
    """
    Advance the status of a work order
    """
    try:
        wo_id = request.data.get('wo_id')
        new_status = request.data.get('new_status')
        notes = request.data.get('notes', '')
        completed_date = request.data.get('completed_date')

        if not all([wo_id, new_status]):
            return Response(
                {'error': 'wo_id and new_status are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        with connection.cursor() as cursor:
            cursor.callproc('svc.advance_work_order_status', [wo_id, new_status, notes, completed_date])
            result = cursor.fetchone()

            if result and len(result) > 0:
                return Response(json.loads(result[0]), status=status.HTTP_200_OK)
            else:
                return Response(
                    {'error': 'No result returned from stored procedure'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

    except Exception as e:
        logger.error(f"Error advancing work order status: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='post',
    operation_description="Add service to work order",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['wo_id', 'service_code', 'quantity', 'unit_price'],
        properties={
            'wo_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Work order ID'),
            'service_code': openapi.Schema(type=openapi.TYPE_STRING, description='Service code'),
            'quantity': openapi.Schema(type=openapi.TYPE_NUMBER, description='Quantity'),
            'unit_price': openapi.Schema(type=openapi.TYPE_NUMBER, description='Unit price'),
            'description': openapi.Schema(type=openapi.TYPE_STRING, description='Description of the service'),
            'assigned_technician_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Assigned technician ID')
        }
    ),
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'wo_item_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'added_service': openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                    'service_code': openapi.Schema(type=openapi.TYPE_STRING),
                    'quantity': openapi.Schema(type=openapi.TYPE_NUMBER),
                    'unit_price': openapi.Schema(type=openapi.TYPE_NUMBER),
                    'total_price': openapi.Schema(type=openapi.TYPE_NUMBER)
                }),
                'timestamp': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME)
            }
        ),
        400: 'Bad request',
        401: 'Unauthorized',
        403: 'Insufficient permissions'
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsWorkshopAdmin])
def add_service_to_work_order(request):
    """
    Add a service to a work order
    """
    try:
        wo_id = request.data.get('wo_id')
        service_code = request.data.get('service_code')
        quantity = request.data.get('quantity')
        unit_price = request.data.get('unit_price')
        description = request.data.get('description', '')
        assigned_technician_id = request.data.get('assigned_technician_id')

        if not all([wo_id, service_code, quantity, unit_price]):
            return Response(
                {'error': 'wo_id, service_code, quantity, and unit_price are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        with connection.cursor() as cursor:
            cursor.callproc('svc.add_service_to_wo', [
                wo_id, service_code, quantity, unit_price, description, assigned_technician_id
            ])
            result = cursor.fetchone()

            if result and len(result) > 0:
                return Response(json.loads(result[0]), status=status.HTTP_200_OK)
            else:
                return Response(
                    {'error': 'No result returned from stored procedure'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

    except Exception as e:
        logger.error(f"Error adding service to work order: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='post',
    operation_description="Create invoice from completed work order",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['wo_id'],
        properties={
            'wo_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Work order ID'),
            'invoice_date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, description='Invoice date'),
            'due_date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, description='Due date'),
            'notes': openapi.Schema(type=openapi.TYPE_STRING, description='Notes for the invoice')
        }
    ),
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'invoice_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'invoice_number': openapi.Schema(type=openapi.TYPE_STRING),
                'total_amount': openapi.Schema(type=openapi.TYPE_NUMBER),
                'associated_wo': openapi.Schema(type=openapi.TYPE_INTEGER)
            }
        ),
        400: 'Bad request',
        401: 'Unauthorized',
        403: 'Insufficient permissions'
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsWorkshopAdmin])
def create_invoice_from_work_order(request):
    """
    Create an invoice from a completed work order
    """
    try:
        wo_id = request.data.get('wo_id')
        invoice_date = request.data.get('invoice_date')
        due_date = request.data.get('due_date')
        notes = request.data.get('notes', '')

        if not wo_id:
            return Response(
                {'error': 'wo_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        with connection.cursor() as cursor:
            cursor.callproc('svc.create_invoice_from_wo', [wo_id, invoice_date, due_date, notes])
            result = cursor.fetchone()

            if result and len(result) > 0:
                return Response(json.loads(result[0]), status=status.HTTP_200_OK)
            else:
                return Response(
                    {'error': 'No result returned from stored procedure'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

    except Exception as e:
        logger.error(f"Error creating invoice from work order: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
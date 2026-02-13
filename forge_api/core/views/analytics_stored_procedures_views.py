"""
ForgeDB API REST - Analytics Services Views
API endpoints for executing PostgreSQL stored procedures related to analytics and reporting
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

from ..authentication import CanViewReports, IsTechnicianOrReadOnly

logger = logging.getLogger(__name__)


@swagger_auto_schema(
    method='get',
    operation_description="ABC Analysis of inventory",
    manual_parameters=[
        openapi.Parameter(
            'warehouse_code', 
            openapi.IN_QUERY, 
            description="Warehouse code to filter", 
            type=openapi.TYPE_STRING
        ),
        openapi.Parameter(
            'period_months', 
            openapi.IN_QUERY, 
            description="Number of months to analyze", 
            type=openapi.TYPE_INTEGER,
            default=12
        ),
        openapi.Parameter(
            'metric', 
            openapi.IN_QUERY, 
            description="Metric to analyze (value, volume, quantity)", 
            type=openapi.TYPE_STRING,
            enum=['value', 'volume', 'quantity']
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
                    'category': openapi.Schema(type=openapi.TYPE_STRING),
                    'annual_value': openapi.Schema(type=openapi.TYPE_NUMBER),
                    'percentage': openapi.Schema(type=openapi.TYPE_NUMBER),
                    'cumulative_percentage': openapi.Schema(type=openapi.TYPE_NUMBER),
                    'abc_class': openapi.Schema(type=openapi.TYPE_STRING, enum=['A', 'B', 'C']),
                    'recommendation': openapi.Schema(type=openapi.TYPE_STRING)
                }
            )
        ),
        400: 'Bad request',
        401: 'Unauthorized',
        403: 'Insufficient permissions'
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated, CanViewReports])
def abc_analysis_inventory(request):
    """
    Perform ABC analysis of inventory items
    """
    try:
        warehouse_code = request.query_params.get('warehouse_code')
        period_months = request.query_params.get('period_months', 12)
        metric = request.query_params.get('metric', 'value')

        with connection.cursor() as cursor:
            cursor.callproc('kpi.abc_inventory_analysis', [warehouse_code, int(period_months), metric])
            results = []
            for row in cursor.fetchall():
                if len(row) > 0 and row[0]:
                    results.append(json.loads(row[0]))
            
            return Response(results, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error performing ABC analysis: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_description="Technician productivity report",
    manual_parameters=[
        openapi.Parameter(
            'date_from', 
            openapi.IN_QUERY, 
            description="Start date for analysis", 
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_DATE
        ),
        openapi.Parameter(
            'date_to', 
            openapi.IN_QUERY, 
            description="End date for analysis", 
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_DATE
        ),
        openapi.Parameter(
            'department', 
            openapi.IN_QUERY, 
            description="Department filter", 
            type=openapi.TYPE_STRING
        )
    ],
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Items(
                type=openapi.TYPE_OBJECT,
                properties={
                    'technician_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'technician_name': openapi.Schema(type=openapi.TYPE_STRING),
                    'department': openapi.Schema(type=openapi.TYPE_STRING),
                    'total_work_orders': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'completed_orders': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'completion_rate': openapi.Schema(type=openapi.TYPE_NUMBER),
                    'labor_revenue': openapi.Schema(type=openapi.TYPE_NUMBER),
                    'avg_completion_time': openapi.Schema(type=openapi.TYPE_NUMBER)
                }
            )
        ),
        400: 'Bad request',
        401: 'Unauthorized',
        403: 'Insufficient permissions'
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated, CanViewReports])
def technician_productivity_report(request):
    """
    Generate technician productivity report
    """
    try:
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        department = request.query_params.get('department')

        with connection.cursor() as cursor:
            cursor.callproc('kpi.generate_technician_productivity_report', [date_from, date_to, department])
            results = []
            for row in cursor.fetchall():
                if len(row) > 0 and row[0]:
                    results.append(json.loads(row[0]))
            
            return Response(results, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error generating technician productivity report: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_description="Demand forecasting",
    manual_parameters=[
        openapi.Parameter(
            'product_category', 
            openapi.IN_QUERY, 
            description="Product category to filter", 
            type=openapi.TYPE_STRING
        ),
        openapi.Parameter(
            'forecast_horizon_months', 
            openapi.IN_QUERY, 
            description="Number of months ahead to forecast", 
            type=openapi.TYPE_INTEGER,
            default=3
        ),
        openapi.Parameter(
            'confidence_level', 
            openapi.IN_QUERY, 
            description="Confidence level for prediction (0.8 = 80%)", 
            type=openapi.TYPE_NUMBER,
            default=0.8
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
                    'predicted_demand': openapi.Schema(type=openapi.TYPE_NUMBER),
                    'confidence_level': openapi.Schema(type=openapi.TYPE_NUMBER),
                    'reorder_recommendation': openapi.Schema(type=openapi.TYPE_STRING, enum=['YES', 'NO', 'CONSIDER']),
                    'forecast_date_start': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
                    'forecast_date_end': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE)
                }
            )
        ),
        400: 'Bad request',
        401: 'Unauthorized',
        403: 'Insufficient permissions'
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated, CanViewReports])
def demand_forecasting(request):
    """
    Generate demand forecasting report
    """
    try:
        product_category = request.query_params.get('product_category')
        forecast_horizon_months = request.query_params.get('forecast_horizon_months', 3)
        confidence_level = request.query_params.get('confidence_level', 0.8)

        with connection.cursor() as cursor:
            cursor.callproc('kpi.demand_forecasting', [
                product_category, int(forecast_horizon_months), float(confidence_level)
            ])
            results = []
            for row in cursor.fetchall():
                if len(row) > 0 and row[0]:
                    results.append(json.loads(row[0]))
            
            return Response(results, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error generating demand forecasting: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@swagger_auto_schema(
    method='get',
    operation_description="Financial KPI Dashboard",
    manual_parameters=[
        openapi.Parameter(
            'date_from', 
            openapi.IN_QUERY, 
            description="Start date for analysis", 
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_DATE
        ),
        openapi.Parameter(
            'date_to', 
            openapi.IN_QUERY, 
            description="End date for analysis", 
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_DATE
        ),
        openapi.Parameter(
            'department', 
            openapi.IN_QUERY, 
            description="Department filter", 
            type=openapi.TYPE_STRING
        )
    ],
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'period_revenue': openapi.Schema(type=openapi.TYPE_NUMBER),
                'period_expenses': openapi.Schema(type=openapi.TYPE_NUMBER),
                'net_profit': openapi.Schema(type=openapi.TYPE_NUMBER),
                'gross_profit_margin': openapi.Schema(type=openapi.TYPE_NUMBER),
                'operational_expense_ratio': openapi.Schema(type=openapi.TYPE_NUMBER),
                'cash_flow': openapi.Schema(type=openapi.TYPE_NUMBER),
                'inventory_turnover': openapi.Schema(type=openapi.TYPE_NUMBER),
                'return_on_assets': openapi.Schema(type=openapi.TYPE_NUMBER)
            }
        ),
        400: 'Bad request',
        401: 'Unauthorized',
        403: 'Insufficient permissions'
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated, CanViewReports])
def financial_kpi_dashboard(request):
    """
    Generate financial KPI dashboard
    """
    try:
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        department = request.query_params.get('department')

        with connection.cursor() as cursor:
            cursor.callproc('kpi.generate_financial_kpis', [date_from, date_to, department])
            result = cursor.fetchone()
            
            if result and len(result) > 0 and result[0]:
                return Response(json.loads(result[0]), status=status.HTTP_200_OK)
            else:
                return Response(
                    {'error': 'No result returned from stored procedure'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

    except Exception as e:
        logger.error(f"Error generating financial KPI dashboard: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
"""
Health check views for API monitoring
"""
from django.http import JsonResponse
from django.db import connection
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
import time
from datetime import datetime


class HealthCheckView(APIView):
    """
    Simple health check endpoint
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """
        Basic health check
        """
        return Response({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'message': 'API is running'
        })


class DetailedHealthCheckView(APIView):
    """
    Detailed health check with database connectivity
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """
        Comprehensive health check
        """
        start_time = time.time()
        
        health_data = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'checks': {},
            'response_time_ms': 0
        }
        
        # Database check
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            health_data['checks']['database'] = {
                'status': 'healthy',
                'message': 'Database connection successful'
            }
        except Exception as e:
            health_data['checks']['database'] = {
                'status': 'unhealthy',
                'message': f'Database connection failed: {str(e)}'
            }
            health_data['status'] = 'unhealthy'
        
        # API endpoints check
        health_data['checks']['api'] = {
            'status': 'healthy',
            'message': 'API endpoints are responding'
        }
        
        # Calculate response time
        health_data['response_time_ms'] = round((time.time() - start_time) * 1000, 2)
        
        # Return appropriate status code
        status_code = status.HTTP_200_OK if health_data['status'] == 'healthy' else status.HTTP_503_SERVICE_UNAVAILABLE
        
        return Response(health_data, status=status_code)


@method_decorator(csrf_exempt, name='dispatch')
class SimpleHealthView(View):
    """
    Very simple health check for load balancers
    """
    
    def get(self, request):
        return JsonResponse({'status': 'ok'})
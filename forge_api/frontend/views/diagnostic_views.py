"""
Diagnostic views for API connectivity and system health
"""
import json
import time
from datetime import datetime, timedelta
from django.shortcuts import render
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import requests
import logging

from ..services.api_client import ForgeAPIClient, APIException

logger = logging.getLogger(__name__)


class APIDiagnosticView(LoginRequiredMixin, TemplateView):
    """
    Comprehensive API diagnostic page
    """
    template_name = 'frontend/diagnostic/api_diagnostic.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get API client
        api_client = ForgeAPIClient(self.request)
        
        # Basic system info
        context.update({
            'api_base_url': api_client.base_url,
            'current_time': datetime.now(),
            'user_authenticated': self.request.user.is_authenticated,
            'user_info': {
                'username': self.request.user.username,
                'email': self.request.user.email,
                'is_staff': self.request.user.is_staff,
            } if self.request.user.is_authenticated else None,
        })
        
        return context


class APIHealthCheckView(LoginRequiredMixin, TemplateView):
    """
    API health check endpoint for diagnostics
    """
    
    def get(self, request, *args, **kwargs):
        """
        Perform comprehensive API health check
        """
        api_client = ForgeAPIClient(request)
        results = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'unknown',
            'tests': {},
            'performance': {},
            'errors': []
        }
        
        start_time = time.time()
        
        try:
            # Test 1: Basic connectivity
            results['tests']['connectivity'] = self._test_connectivity(api_client)
            
            # Test 2: Authentication
            results['tests']['authentication'] = self._test_authentication(api_client)
            
            # Test 3: Core endpoints
            results['tests']['endpoints'] = self._test_core_endpoints(api_client)
            
            # Test 4: Database connectivity
            results['tests']['database'] = self._test_database_connectivity(api_client)
            
            # Test 5: Performance metrics
            results['performance'] = self._measure_performance(api_client)
            
            # Determine overall status
            results['overall_status'] = self._determine_overall_status(results['tests'])
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            results['errors'].append(f"Health check failed: {str(e)}")
            results['overall_status'] = 'error'
        
        # Calculate total execution time
        results['execution_time'] = round((time.time() - start_time) * 1000, 2)  # ms
        
        return JsonResponse(results)
    
    def _test_connectivity(self, api_client):
        """Test basic API connectivity"""
        test_result = {
            'status': 'unknown',
            'message': '',
            'response_time': None,
            'details': {}
        }
        
        try:
            start_time = time.time()
            
            # Try to reach a simple endpoint
            response = api_client.get('health/')
            response_time = round((time.time() - start_time) * 1000, 2)
            
            if response.status_code == 200:
                test_result.update({
                    'status': 'success',
                    'message': 'API is reachable',
                    'response_time': response_time,
                    'details': {
                        'status_code': response.status_code,
                        'content_type': response.headers.get('Content-Type', 'unknown')
                    }
                })
            else:
                test_result.update({
                    'status': 'warning',
                    'message': f'API responded with status {response.status_code}',
                    'response_time': response_time,
                    'details': {'status_code': response.status_code}
                })
                
        except requests.exceptions.ConnectionError:
            test_result.update({
                'status': 'error',
                'message': 'Cannot connect to API server',
                'details': {'error_type': 'ConnectionError'}
            })
        except requests.exceptions.Timeout:
            test_result.update({
                'status': 'error',
                'message': 'API request timed out',
                'details': {'error_type': 'Timeout'}
            })
        except Exception as e:
            test_result.update({
                'status': 'error',
                'message': f'Connectivity test failed: {str(e)}',
                'details': {'error_type': type(e).__name__}
            })
        
        return test_result
    
    def _test_authentication(self, api_client):
        """Test authentication system"""
        test_result = {
            'status': 'unknown',
            'message': '',
            'details': {}
        }
        
        try:
            # Check if user has valid tokens
            tokens = api_client.auth_service.get_user_tokens(api_client.request)
            
            if tokens['access']:
                # Try to access a protected endpoint
                response = api_client.get('auth/user/')
                
                if response.status_code == 200:
                    user_data = response.json()
                    test_result.update({
                        'status': 'success',
                        'message': 'Authentication is working',
                        'details': {
                            'user_id': user_data.get('id'),
                            'username': user_data.get('username'),
                            'token_present': True
                        }
                    })
                elif response.status_code == 401:
                    test_result.update({
                        'status': 'warning',
                        'message': 'Token expired or invalid',
                        'details': {'status_code': 401, 'token_present': True}
                    })
                else:
                    test_result.update({
                        'status': 'error',
                        'message': f'Authentication endpoint returned {response.status_code}',
                        'details': {'status_code': response.status_code}
                    })
            else:
                test_result.update({
                    'status': 'warning',
                    'message': 'No authentication token found',
                    'details': {'token_present': False}
                })
                
        except APIException as e:
            test_result.update({
                'status': 'error',
                'message': f'Authentication test failed: {e.get_user_message()}',
                'details': {'error_type': 'APIException', 'status_code': e.status_code}
            })
        except Exception as e:
            test_result.update({
                'status': 'error',
                'message': f'Authentication test failed: {str(e)}',
                'details': {'error_type': type(e).__name__}
            })
        
        return test_result
    
    def _test_core_endpoints(self, api_client):
        """Test core API endpoints"""
        endpoints_to_test = [
            ('clients/', 'Clients API'),
            ('products/', 'Products API'),
            ('workorders/', 'Work Orders API'),
            ('equipment/', 'Equipment API'),
            ('dashboard/summary/', 'Dashboard API'),
        ]
        
        results = {}
        
        for endpoint, name in endpoints_to_test:
            result = {
                'status': 'unknown',
                'message': '',
                'response_time': None,
                'details': {}
            }
            
            try:
                start_time = time.time()
                response = api_client.get(endpoint)
                response_time = round((time.time() - start_time) * 1000, 2)
                
                if response.status_code == 200:
                    data = response.json()
                    result.update({
                        'status': 'success',
                        'message': f'{name} is working',
                        'response_time': response_time,
                        'details': {
                            'status_code': 200,
                            'data_count': len(data.get('results', data)) if isinstance(data, dict) else len(data) if isinstance(data, list) else 'unknown'
                        }
                    })
                elif response.status_code == 401:
                    result.update({
                        'status': 'warning',
                        'message': f'{name} requires authentication',
                        'response_time': response_time,
                        'details': {'status_code': 401}
                    })
                else:
                    result.update({
                        'status': 'error',
                        'message': f'{name} returned status {response.status_code}',
                        'response_time': response_time,
                        'details': {'status_code': response.status_code}
                    })
                    
            except APIException as e:
                result.update({
                    'status': 'error',
                    'message': f'{name} failed: {e.get_user_message()}',
                    'details': {'error_type': 'APIException', 'status_code': e.status_code}
                })
            except Exception as e:
                result.update({
                    'status': 'error',
                    'message': f'{name} failed: {str(e)}',
                    'details': {'error_type': type(e).__name__}
                })
            
            results[endpoint.replace('/', '_').rstrip('_')] = result
        
        return results
    
    def _test_database_connectivity(self, api_client):
        """Test database connectivity through API"""
        test_result = {
            'status': 'unknown',
            'message': '',
            'details': {}
        }
        
        try:
            # Try to get a simple count from the database
            response = api_client.get('clients/?limit=1')
            
            if response.status_code == 200:
                data = response.json()
                test_result.update({
                    'status': 'success',
                    'message': 'Database is accessible',
                    'details': {
                        'total_clients': data.get('count', 'unknown'),
                        'response_format': 'paginated' if 'results' in data else 'direct'
                    }
                })
            elif response.status_code == 500:
                test_result.update({
                    'status': 'error',
                    'message': 'Database connection error (500)',
                    'details': {'status_code': 500}
                })
            else:
                test_result.update({
                    'status': 'warning',
                    'message': f'Database test returned status {response.status_code}',
                    'details': {'status_code': response.status_code}
                })
                
        except Exception as e:
            test_result.update({
                'status': 'error',
                'message': f'Database test failed: {str(e)}',
                'details': {'error_type': type(e).__name__}
            })
        
        return test_result
    
    def _measure_performance(self, api_client):
        """Measure API performance metrics"""
        metrics = {
            'average_response_time': None,
            'fastest_response': None,
            'slowest_response': None,
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0
        }
        
        # Test endpoints for performance
        test_endpoints = ['clients/?limit=5', 'products/?limit=5', 'dashboard/summary/']
        response_times = []
        
        for endpoint in test_endpoints:
            try:
                start_time = time.time()
                response = api_client.get(endpoint)
                response_time = (time.time() - start_time) * 1000  # ms
                
                response_times.append(response_time)
                metrics['total_requests'] += 1
                
                if response.status_code == 200:
                    metrics['successful_requests'] += 1
                else:
                    metrics['failed_requests'] += 1
                    
            except Exception:
                metrics['total_requests'] += 1
                metrics['failed_requests'] += 1
        
        if response_times:
            metrics.update({
                'average_response_time': round(sum(response_times) / len(response_times), 2),
                'fastest_response': round(min(response_times), 2),
                'slowest_response': round(max(response_times), 2)
            })
        
        return metrics
    
    def _determine_overall_status(self, tests):
        """Determine overall system status based on test results"""
        statuses = []
        
        # Collect all test statuses
        for test_name, test_result in tests.items():
            if isinstance(test_result, dict) and 'status' in test_result:
                statuses.append(test_result['status'])
            elif isinstance(test_result, dict):
                # Handle nested test results (like endpoints)
                for sub_test_name, sub_test_result in test_result.items():
                    if isinstance(sub_test_result, dict) and 'status' in sub_test_result:
                        statuses.append(sub_test_result['status'])
        
        # Determine overall status
        if 'error' in statuses:
            return 'error'
        elif 'warning' in statuses:
            return 'warning'
        elif 'success' in statuses:
            return 'success'
        else:
            return 'unknown'


@method_decorator(csrf_exempt, name='dispatch')
class APIConnectionMonitorView(LoginRequiredMixin, TemplateView):
    """
    Real-time API connection monitoring
    """
    
    def post(self, request, *args, **kwargs):
        """
        Monitor API connection status in real-time
        """
        try:
            data = json.loads(request.body)
            endpoint = data.get('endpoint', 'health/')
            
            api_client = ForgeAPIClient(request)
            
            start_time = time.time()
            
            try:
                response = api_client.get(endpoint)
                response_time = round((time.time() - start_time) * 1000, 2)
                
                result = {
                    'status': 'success' if response.status_code == 200 else 'warning',
                    'status_code': response.status_code,
                    'response_time': response_time,
                    'timestamp': datetime.now().isoformat(),
                    'endpoint': endpoint,
                    'message': 'OK' if response.status_code == 200 else f'Status {response.status_code}'
                }
                
            except requests.exceptions.ConnectionError:
                result = {
                    'status': 'error',
                    'status_code': None,
                    'response_time': None,
                    'timestamp': datetime.now().isoformat(),
                    'endpoint': endpoint,
                    'message': 'Connection failed'
                }
            except requests.exceptions.Timeout:
                result = {
                    'status': 'error',
                    'status_code': None,
                    'response_time': None,
                    'timestamp': datetime.now().isoformat(),
                    'endpoint': endpoint,
                    'message': 'Request timeout'
                }
            except Exception as e:
                result = {
                    'status': 'error',
                    'status_code': None,
                    'response_time': None,
                    'timestamp': datetime.now().isoformat(),
                    'endpoint': endpoint,
                    'message': str(e)
                }
            
            return JsonResponse(result)
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Monitor request failed: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }, status=400)


class APIErrorRateTrackingView(LoginRequiredMixin, TemplateView):
    """
    Track API error rates and response times
    """
    
    def get(self, request, *args, **kwargs):
        """
        Get API error rate and performance statistics
        """
        # This would typically connect to a logging/metrics system
        # For now, we'll simulate some data
        
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        # Simulate metrics (in a real implementation, this would query logs/metrics)
        metrics = {
            'time_range': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat()
            },
            'total_requests': 1250,
            'successful_requests': 1180,
            'failed_requests': 70,
            'error_rate': 5.6,  # percentage
            'average_response_time': 245.5,  # ms
            'p95_response_time': 890.2,  # ms
            'p99_response_time': 1250.8,  # ms
            'endpoints': {
                'clients/': {
                    'requests': 450,
                    'errors': 12,
                    'avg_response_time': 180.5
                },
                'products/': {
                    'requests': 320,
                    'errors': 8,
                    'avg_response_time': 165.2
                },
                'workorders/': {
                    'requests': 280,
                    'errors': 25,
                    'avg_response_time': 320.8
                },
                'dashboard/': {
                    'requests': 200,
                    'errors': 25,
                    'avg_response_time': 420.1
                }
            },
            'error_types': {
                '500': 35,
                '404': 20,
                '401': 10,
                '400': 5
            }
        }
        
        return JsonResponse(metrics)
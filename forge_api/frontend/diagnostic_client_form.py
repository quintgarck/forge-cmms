"""
Diagnostic tools for client form API integration debugging.
"""
import json
import logging
from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from .services.api_client import ForgeAPIClient, APIException
from .forms import ClientForm

logger = logging.getLogger(__name__)


class ClientFormDiagnosticView(LoginRequiredMixin, View):
    """
    Diagnostic view for testing client form API integration.
    """
    login_url = 'frontend:login'
    
    def get(self, request, *args, **kwargs):
        """Display diagnostic interface."""
        context = {
            'title': 'Diagnóstico de Formulario de Clientes',
            'api_base_url': self._get_api_base_url(request),
        }
        
        # Test API connectivity
        try:
            api_client = ForgeAPIClient(request=request)
            context['api_available'] = api_client.health_check()
        except Exception as e:
            context['api_available'] = False
            context['api_error'] = str(e)
        
        return render(request, 'frontend/diagnostic/client_form_diagnostic.html', context)
    
    def post(self, request, *args, **kwargs):
        """Handle diagnostic tests."""
        test_type = request.POST.get('test_type')
        
        if test_type == 'test_form_validation':
            return self._test_form_validation(request)
        elif test_type == 'test_api_connectivity':
            return self._test_api_connectivity(request)
        elif test_type == 'test_client_creation':
            return self._test_client_creation(request)
        elif test_type == 'test_error_handling':
            return self._test_error_handling(request)
        else:
            return JsonResponse({'error': 'Tipo de prueba no válido'}, status=400)
    
    def _get_api_base_url(self, request):
        """Get API base URL for display."""
        scheme = 'https' if request.is_secure() else 'http'
        host = request.get_host()
        if host == 'testserver':
            host = 'localhost:8000'
        return f"{scheme}://{host}/api/v1/"
    
    def _test_form_validation(self, request):
        """Test Django form validation."""
        try:
            # Test with valid data
            valid_data = {
                'client_code': 'TEST-001',
                'type': 'individual',
                'name': 'Cliente de Prueba',
                'email': 'test@example.com',
                'phone': '1234567890',
                'address': 'Dirección de prueba',
                'credit_limit': '1000.00'
            }
            
            form = ClientForm(data=valid_data)
            valid_result = form.is_valid()
            
            # Test with invalid data
            invalid_data = {
                'client_code': '',  # Required field empty
                'type': 'individual',
                'name': 'A',  # Too short
                'email': 'invalid-email',  # Invalid format
                'phone': '123',  # Too short
                'credit_limit': '-100'  # Negative value
            }
            
            invalid_form = ClientForm(data=invalid_data)
            invalid_result = invalid_form.is_valid()
            
            return JsonResponse({
                'success': True,
                'valid_form': {
                    'is_valid': valid_result,
                    'errors': dict(form.errors) if not valid_result else {}
                },
                'invalid_form': {
                    'is_valid': invalid_result,
                    'errors': dict(invalid_form.errors)
                }
            })
            
        except Exception as e:
            logger.error(f"Form validation test error: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    def _test_api_connectivity(self, request):
        """Test API connectivity and authentication."""
        try:
            api_client = ForgeAPIClient(request=request)
            
            # Test health check
            health_check = api_client.health_check()
            
            # Test authentication status
            auth_token = request.session.get('auth_token')
            has_auth = bool(auth_token)
            
            # Test a simple API call
            try:
                dashboard_data = api_client.get('dashboard/')
                api_call_success = True
                api_response = "API call successful"
            except APIException as e:
                api_call_success = False
                api_response = f"API Error: {e.status_code} - {e.message}"
            except Exception as e:
                api_call_success = False
                api_response = f"Connection Error: {str(e)}"
            
            return JsonResponse({
                'success': True,
                'health_check': health_check,
                'has_authentication': has_auth,
                'api_call_success': api_call_success,
                'api_response': api_response,
                'base_url': api_client.base_url
            })
            
        except Exception as e:
            logger.error(f"API connectivity test error: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    def _test_client_creation(self, request):
        """Test client creation through API."""
        try:
            api_client = ForgeAPIClient(request=request)
            
            # Test data for client creation
            test_client_data = {
                'client_code': f'DIAG-{request.user.id}-001',
                'type': 'individual',
                'name': 'Cliente Diagnóstico',
                'email': f'diagnostic-{request.user.id}@test.com',
                'phone': '1234567890',
                'address': 'Dirección de prueba para diagnóstico',
                'credit_limit': 500.00
            }
            
            # Attempt to create client
            try:
                result = api_client.create_client(test_client_data)
                
                # If successful, try to retrieve the created client
                try:
                    created_client = api_client.get_client(result['id'])
                    retrieval_success = True
                    
                    # Clean up - delete the test client
                    try:
                        api_client.delete_client(result['id'])
                        cleanup_success = True
                    except:
                        cleanup_success = False
                        
                except APIException:
                    retrieval_success = False
                    cleanup_success = False
                
                return JsonResponse({
                    'success': True,
                    'creation_success': True,
                    'created_client_id': result.get('id'),
                    'retrieval_success': retrieval_success,
                    'cleanup_success': cleanup_success,
                    'message': 'Cliente de prueba creado y eliminado exitosamente'
                })
                
            except APIException as e:
                return JsonResponse({
                    'success': True,
                    'creation_success': False,
                    'error_code': e.status_code,
                    'error_message': e.message,
                    'error_details': e.response_data
                })
                
        except Exception as e:
            logger.error(f"Client creation test error: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    def _test_error_handling(self, request):
        """Test error handling scenarios."""
        try:
            api_client = ForgeAPIClient(request=request)
            
            test_results = {}
            
            # Test 1: Invalid data (should return 400)
            try:
                invalid_data = {
                    'client_code': '',  # Empty required field
                    'name': '',  # Empty required field
                    'email': 'invalid-email'  # Invalid format
                }
                api_client.create_client(invalid_data)
                test_results['invalid_data'] = {'success': False, 'message': 'Should have failed'}
            except APIException as e:
                test_results['invalid_data'] = {
                    'success': True,
                    'status_code': e.status_code,
                    'message': e.message,
                    'expected': e.status_code == 400
                }
            
            # Test 2: Non-existent client retrieval (should return 404)
            try:
                api_client.get_client(99999)  # Non-existent ID
                test_results['not_found'] = {'success': False, 'message': 'Should have failed'}
            except APIException as e:
                test_results['not_found'] = {
                    'success': True,
                    'status_code': e.status_code,
                    'message': e.message,
                    'expected': e.status_code == 404
                }
            
            # Test 3: Malformed request
            try:
                # This should test the API client's error handling
                malformed_data = {'invalid_field': 'test'}
                api_client.create_client(malformed_data)
                test_results['malformed'] = {'success': False, 'message': 'Should have failed'}
            except APIException as e:
                test_results['malformed'] = {
                    'success': True,
                    'status_code': e.status_code,
                    'message': e.message,
                    'expected': e.status_code in [400, 422]
                }
            
            return JsonResponse({
                'success': True,
                'test_results': test_results
            })
            
        except Exception as e:
            logger.error(f"Error handling test error: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            })


class ClientFormDebugView(LoginRequiredMixin, View):
    """
    Debug view for real-time client form debugging.
    """
    login_url = 'frontend:login'
    
    def post(self, request, *args, **kwargs):
        """Handle debug form submission."""
        try:
            # Get form data
            form_data = request.POST.dict()
            form_data.pop('csrfmiddlewaretoken', None)
            
            # Validate form
            form = ClientForm(data=form_data)
            form_valid = form.is_valid()
            
            debug_info = {
                'form_data': form_data,
                'form_valid': form_valid,
                'form_errors': dict(form.errors) if not form_valid else {},
                'cleaned_data': form.cleaned_data if form_valid else {}
            }
            
            # If form is valid, test API call
            if form_valid:
                try:
                    api_client = ForgeAPIClient(request=request)
                    
                    # Prepare API data
                    api_data = {
                        'client_code': form.cleaned_data['client_code'],
                        'type': form.cleaned_data['type'],
                        'name': form.cleaned_data['name'],
                        'email': form.cleaned_data['email'],
                        'phone': form.cleaned_data['phone'],
                        'address': form.cleaned_data['address'] or '',
                        'credit_limit': float(form.cleaned_data['credit_limit'] or 0),
                    }
                    
                    debug_info['api_data'] = api_data
                    
                    # Test API call (dry run - don't actually create)
                    debug_info['api_test'] = {
                        'would_send': api_data,
                        'endpoint': 'clients/',
                        'method': 'POST'
                    }
                    
                except Exception as api_error:
                    debug_info['api_error'] = str(api_error)
            
            return JsonResponse({
                'success': True,
                'debug_info': debug_info
            })
            
        except Exception as e:
            logger.error(f"Debug form error: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
"""
ForgeDB API Client Service

This service handles all communication with the ForgeDB REST API backend,
including authentication, session management, and CRUD operations.
"""
import requests
import logging
from typing import Dict, Any, Optional, List, Union
from django.conf import settings
from django.core.cache import cache
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class APIException(Exception):
    """Custom exception for API-related errors."""
    
    def __init__(self, message: str, status_code: int = None, response_data: Dict = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data or {}
        super().__init__(self.message)


class BaseAPIClient:
    """Base HTTP client for ForgeDB backend communication.

    This class is responsible for setting up the underlying HTTP session,
    base URL, timeout and retry configuration. Higher-level clients
    (like ForgeAPIClient) should focus on domain-specific concerns.
    """

    def __init__(self, base_url: str, timeout: Optional[int] = None, max_retries: Optional[int] = None):
        self.base_url = base_url
        self.session = requests.Session()
        self.timeout = timeout if timeout is not None else getattr(settings, 'API_TIMEOUT', 30)
        self.max_retries = max_retries if max_retries is not None else getattr(settings, 'API_MAX_RETRIES', 3)

        # Configure session headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'ForgeDB-Frontend/1.0'
        })

    def _log_request(self, method: str, url: str, data: Dict = None):
        """Log API request for debugging."""
        logger.debug(f"API Request: {method} {url}")
        if data and logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Request data: {json.dumps(data, indent=2)}")
    
    def _log_response(self, response: requests.Response):
        """Log API response for debugging."""
        logger.debug(f"API Response: {response.status_code} {response.url}")
        if logger.isEnabledFor(logging.DEBUG):
            try:
                logger.debug(f"Response data: {json.dumps(response.json(), indent=2)}")
            except (ValueError, json.JSONDecodeError):
                logger.debug(f"Response text: {response.text[:500]}")
    
    def _handle_network_error(self, error: requests.RequestException, attempt: int) -> bool:
        """Handle network errors with appropriate retry logic."""
        # Don't retry on the last attempt
        if attempt >= self.max_retries - 1:
            return False
        
        # Determine if error is retryable
        if isinstance(error, requests.exceptions.Timeout):
            logger.warning(f"Request timeout on attempt {attempt + 1}, retrying...")
            return True
        if isinstance(error, requests.exceptions.ConnectionError):
            logger.warning(f"Connection error on attempt {attempt + 1}, retrying...")
            return True
        if isinstance(error, requests.exceptions.HTTPError):
            # Don't retry client errors (4xx), but retry server errors (5xx)
            if hasattr(error, 'response') and error.response:
                status_code = error.response.status_code
                if 500 <= status_code < 600:
                    logger.warning(f"Server error {status_code} on attempt {attempt + 1}, retrying...")
                    return True
            return False
        
        # For other network errors, retry
        logger.warning(f"Network error on attempt {attempt + 1}: {type(error).__name__}, retrying...")
        return True
    
    def _extract_error_message(self, error_data: Dict) -> str:
        """Extract a user-friendly error message from API error response."""
        if isinstance(error_data, dict):
            # Try common error message fields
            for field in ['detail', 'message', 'error', 'non_field_errors']:
                if field in error_data:
                    error_value = error_data[field]
                    if isinstance(error_value, list):
                        return '; '.join(str(err) for err in error_value)
                    return str(error_value)
            
            # If it's field validation errors, format them nicely
            field_errors = []
            for field, errors in error_data.items():
                if field in ['detail', 'message', 'error', 'non_field_errors']:
                    continue  # Already handled above
                
                if isinstance(errors, list):
                    field_name = field.replace('_', ' ').title()
                    error_messages = [str(err) for err in errors]
                    field_errors.append(f"{field_name}: {'; '.join(error_messages)}")
                else:
                    field_name = field.replace('_', ' ').title()
                    field_errors.append(f"{field_name}: {str(errors)}")
            
            if field_errors:
                return '; '.join(field_errors)
        
        # Fallback to string representation
        error_str = str(error_data)
        
        # Truncate very long error messages
        if len(error_str) > 200:
            error_str = error_str[:200] + "..."
        
        return error_str


class ForgeAPIClient(BaseAPIClient):
    """
    Comprehensive API client for ForgeDB backend communication.
    
    Features:
    - JWT token management with automatic refresh
    - Session management and caching
    - Comprehensive error handling
    - Request/response logging
    - Retry logic for failed requests
    """
    
    def __init__(self, base_url: str = None, request=None):
        """Initialize the API client.
        
        Args:
            base_url: Base URL for the API. If None, will be constructed from request.
            request: Django request object for session management.
        """
        self.request = request
        resolved_base_url = base_url or self._get_base_url()
        super().__init__(resolved_base_url)
        
        # Set authentication if available
        if self.request and hasattr(self.request, 'session'):
            self._set_auth_headers()
        
    def _get_base_url(self) -> str:
        """Get the base URL for API requests."""
        if self.request:
            scheme = 'https' if self.request.is_secure() else 'http'
            host = self.request.get_host()
            
            # Handle testserver in testing environment
            if host == 'testserver':
                host = 'localhost:8000'
            
            return f"{scheme}://{host}/api/v1/"
        return getattr(settings, 'API_BASE_URL', 'http://localhost:8000/api/v1/')
    
    def _set_auth_headers(self):
        """Set authentication headers from session."""
        if not self.request or not hasattr(self.request, 'session'):
            return
        
        # First, try to get JWT token from session
        token = self.request.session.get('auth_token')
        if token:
            self.session.headers['Authorization'] = f'Bearer {token}'
            logger.debug(f"Auth token set in API client headers: {token[:30]}...")
        else:
            # Remove authorization header if no token
            self.session.headers.pop('Authorization', None)
            logger.debug("No auth token found in session")
        
        # Also use session cookies for cross-site requests
        # This allows the API to recognize the Django session
        try:
            # Get session cookie
            session_key = self.request.session.session_key
            if session_key:
                # Set session cookie on the requests session
                domain = self.request.get_host().split(':')[0]
                self.session.cookies.set('sessionid', session_key, domain=domain)
                logger.debug(f"Session cookie set: sessionid={session_key[:20]}...")
        except Exception as e:
            logger.debug(f"Could not set session cookie: {e}")
    
    def _refresh_auth_headers(self):
        """Refresh authentication headers - call this before each request."""
        self._set_auth_headers()
    
    def _get_cache_key(self, endpoint: str, params: Dict = None) -> str:
        """Generate cache key for API responses."""
        key_parts = ['forge_api', endpoint.replace('/', '_')]
        if params:
            # Sort params for consistent cache keys
            sorted_params = sorted(params.items())
            params_str = '_'.join([f"{k}_{v}" for k, v in sorted_params])
            key_parts.append(params_str)
        return ':'.join(key_parts)
    
    def _invalidate_related_cache(self, endpoint: str):
        """Invalidate cache for related endpoints after mutations."""
        try:
            # Get all cache keys
            if hasattr(cache, 'keys'):
                # Redis or cache backend that supports keys()
                # Invalidate both general and specific cache keys
                base_pattern = f'forge_api*{endpoint.split("/")[0]}*'
                keys = cache.keys(base_pattern)
                if keys:
                    cache.delete_many(keys)
                
                # Also invalidate the specific endpoint key (e.g., forge_api:suppliers_1_)
                specific_pattern = f'forge_api:{endpoint.replace("/", "_")}*'
                specific_keys = cache.keys(specific_pattern)
                if specific_keys:
                    cache.delete_many(specific_keys)
                
                # Also invalidate the main list endpoint (e.g., when updating suppliers/1/, also clear suppliers/ cache)
                base_endpoint = endpoint.split('/')[0]
                list_pattern = f'forge_api:{base_endpoint}_*'
                list_keys = cache.keys(list_pattern)
                if list_keys:
                    cache.delete_many(list_keys)
            else:
                # Fallback: delete common cache keys manually
                # This is less efficient but works with all backends
                base_endpoint = endpoint.split('/')[0] if '/' in endpoint else endpoint
                common_keys = [
                    f'forge_api:{base_endpoint}',
                    f'forge_api:{base_endpoint}_',
                ]
                for key in common_keys:
                    cache.delete(key)
                
                # Also delete the specific endpoint key
                specific_key = f'forge_api:{endpoint.replace("/", "_")}'
                cache.delete(specific_key)
                
                # Also delete the main list cache key
                list_key = f'forge_api:{base_endpoint}_'  # This covers the main list
                cache.delete(list_key)
        except Exception as e:
            logger.warning(f"Failed to invalidate cache: {e}")
    
    def _log_request(self, method: str, url: str, data: Dict = None):
        """Log API request for debugging."""
        logger.debug(f"API Request: {method} {url}")
        if data and logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Request data: {json.dumps(data, indent=2)}")
    
    def _log_response(self, response: requests.Response):
        """Log API response for debugging."""
        logger.debug(f"API Response: {response.status_code} {response.url}")
        if logger.isEnabledFor(logging.DEBUG):
            try:
                logger.debug(f"Response data: {json.dumps(response.json(), indent=2)}")
            except (ValueError, json.JSONDecodeError):
                logger.debug(f"Response text: {response.text[:500]}")
    
    def _handle_auth_error(self, response: requests.Response):
        """Handle authentication errors and attempt token refresh."""
        if response.status_code == 401 and self.request:
            logger.info("Token expired or invalid, attempting refresh")
            logger.debug(f"Response content: {response.text}")
            
            refresh_token = self.request.session.get('refresh_token')
            if refresh_token:
                try:
                    # Attempt to refresh token
                    logger.debug(f"Attempting to refresh token with refresh token length: {len(refresh_token) if refresh_token else 0}")
                    
                    refresh_response = requests.post(
                        f"{self.base_url}auth/refresh/",
                        json={'refresh': refresh_token},
                        timeout=self.timeout,
                        headers={'Content-Type': 'application/json'}
                    )
                    
                    logger.debug(f"Token refresh response status: {refresh_response.status_code}")
                    
                    if refresh_response.status_code == 200:
                        token_data = refresh_response.json()
                        new_token = token_data.get('access')
                        new_refresh_token = token_data.get('refresh', refresh_token)

                        if new_token:
                            # Update session and headers
                            self.request.session['auth_token'] = new_token
                            if new_refresh_token != refresh_token:
                                self.request.session['refresh_token'] = new_refresh_token
                            self.request.session['token_timestamp'] = datetime.now().isoformat()

                            # Force session save to ensure persistence
                            if hasattr(self.request.session, 'save'):
                                self.request.session.save()

                            self.session.headers['Authorization'] = f'Bearer {new_token}'

                            logger.info("Token refreshed successfully in API client")
                            return True
                        else:
                            logger.error("No access token in refresh response")
                    elif refresh_response.status_code == 401:
                        logger.warning("Refresh token is invalid or expired")
                    else:
                        logger.warning(f"Token refresh failed with status {refresh_response.status_code}: {refresh_response.text}")
                        
                except requests.RequestException as e:
                    logger.error(f"Token refresh network error: {e}")
                except Exception as e:
                    logger.error(f"Token refresh unexpected error: {e}")
            else:
                logger.warning("No refresh token available for token refresh")
            
            # Clear invalid tokens
            logger.info("Clearing invalid tokens from session")
            self.request.session.pop('auth_token', None)
            self.request.session.pop('refresh_token', None)
            self.session.headers.pop('Authorization', None)
        
        return False
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Dict = None, 
        params: Dict = None,
        use_cache: bool = False,
        cache_timeout: int = 300
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the API with comprehensive error handling.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (without base URL)
            data: Request body data
            params: URL parameters
            use_cache: Whether to use caching for GET requests
            cache_timeout: Cache timeout in seconds
            
        Returns:
            Dict containing the API response
            
        Raises:
            APIException: For API-related errors
        """
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        # Ensure auth headers are set before each request
        self._set_auth_headers()
        
        # Check cache for GET requests
        if method == 'GET' and use_cache:
            cache_key = self._get_cache_key(endpoint, params)
            cached_response = cache.get(cache_key)
            if cached_response:
                logger.debug(f"Cache hit for {endpoint}")
                return cached_response
        
        self._log_request(method, url, data)
        
        # Retry logic
        for attempt in range(self.max_retries):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    json=data if data else None,
                    params=params,
                    timeout=self.timeout
                )
                
                self._log_response(response)
                
                # Handle authentication errors
                if response.status_code == 401:
                    if self._handle_auth_error(response) and attempt < self.max_retries - 1:
                        # Re-set auth headers after token refresh
                        self._set_auth_headers()
                        continue  # Retry with new token
                
                # Handle successful responses
                if 200 <= response.status_code < 300:
                    try:
                        result = response.json() if response.content else {}
                        
                        # Cache GET responses
                        if method == 'GET' and use_cache:
                            cache_key = self._get_cache_key(endpoint, params)
                            cache.set(cache_key, result, cache_timeout)
                        
                        # Invalidate related cache on POST/PUT/PATCH/DELETE
                        # This happens AFTER the request succeeds
                        if method in ['POST', 'PUT', 'PATCH', 'DELETE']:
                            # Invalidate the specific endpoint cache
                            self._invalidate_related_cache(endpoint)
                            
                            # Also invalidate any list endpoint cache for the same resource
                            # This ensures that after updating a currency, the list view is also refreshed
                            base_endpoint = endpoint.split('/')[0] if '/' in endpoint else endpoint
                            if base_endpoint:
                                list_cache_key = self._get_cache_key(f'{base_endpoint}/', None)
                                cache.delete(list_cache_key)
                                # Also delete any paginated list caches
                                for page in range(1, 100):  # Arbitrary max pages
                                    paginated_key = self._get_cache_key(f'{base_endpoint}/', {'page': page})
                                    if not cache.get(paginated_key):
                                        break
                                    cache.delete(paginated_key)
                        
                        return result
                        
                    except (ValueError, json.JSONDecodeError) as e:
                        logger.error(f"JSON decode error: {e}")
                        raise APIException(
                            "Invalid JSON response from server",
                            response.status_code,
                            {'raw_response': response.text}
                        )
                
                # Handle client errors (4xx)
                elif 400 <= response.status_code < 500:
                    try:
                        error_data = response.json()
                    except (ValueError, json.JSONDecodeError):
                        error_data = {'detail': response.text}
                    
                    error_message = self._extract_error_message(error_data)
                    raise APIException(error_message, response.status_code, error_data)
                
                # Handle server errors (5xx)
                elif response.status_code >= 500:
                    if attempt < self.max_retries - 1:
                        logger.warning(f"Server error {response.status_code}, retrying...")
                        continue
                    
                    # Try to get more error details from response
                    error_detail = 'Internal server error'
                    try:
                        error_data = response.json()
                        if isinstance(error_data, dict):
                            error_detail = self._extract_error_message(error_data)
                        else:
                            error_detail = str(error_data)
                    except (ValueError, json.JSONDecodeError):
                        error_detail = response.text[:500] if response.text else 'Internal server error'
                    
                    logger.error(f"Server error {response.status_code}: {error_detail}")
                    raise APIException(
                        f"Error del servidor ({response.status_code}): {error_detail}",
                        response.status_code,
                        {'detail': error_detail, 'response_text': response.text[:1000] if response.text else ''}
                    )
                
            except requests.RequestException as e:
                # Use the new network error handler
                if self._handle_network_error(e, attempt):
                    continue
                
                logger.error(f"Request failed after {self.max_retries} attempts: {e}")
                raise APIException(f"Network error: {str(e)}")
        
        raise APIException("Maximum retry attempts exceeded")
        
    
    # CRUD Operations
    def get(self, endpoint: str, params: Dict = None, use_cache: bool = False, cache_timeout: int = 300) -> Dict[str, Any]:
        """Make a GET request."""
        return self._make_request('GET', endpoint, params=params, use_cache=use_cache, cache_timeout=cache_timeout)
    
    def post(self, endpoint: str, data: Dict = None) -> Dict[str, Any]:
        """Make a POST request."""
        return self._make_request('POST', endpoint, data=data)
    
    def put(self, endpoint: str, data: Dict = None) -> Dict[str, Any]:
        """Make a PUT request."""
        return self._make_request('PUT', endpoint, data=data)
    
    def patch(self, endpoint: str, data: Dict = None) -> Dict[str, Any]:
        """Make a PATCH request."""
        return self._make_request('PATCH', endpoint, data=data)
    
    def delete(self, endpoint: str) -> Dict[str, Any]:
        """Make a DELETE request."""
        return self._make_request('DELETE', endpoint)
    
    # Specialized methods for common operations
    def get_paginated(self, endpoint: str, page: int = 1, page_size: int = 20, **filters) -> Dict[str, Any]:
        """Get paginated results from an endpoint."""
        params = {
            'page': page,
            'page_size': page_size,
            **filters
        }
        return self.get(endpoint, params=params, use_cache=True)
    
    def search(self, endpoint: str, query: str, limit: int = 10) -> Dict[str, Any]:
        """Search for items using a query string."""
        params = {
            'search': query,
            'limit': limit
        }
        return self.get(endpoint, params=params)
    
    def bulk_create(self, endpoint: str, items: List[Dict]) -> Dict[str, Any]:
        """Create multiple items in a single request."""
        return self.post(f"{endpoint}bulk_create/", data={'items': items})
    
    def bulk_update(self, endpoint: str, items: List[Dict]) -> Dict[str, Any]:
        """Update multiple items in a single request."""
        return self.post(f"{endpoint}bulk_update/", data={'items': items})
    
    # Entity-specific methods
    def get_clients(self, page: int = 1, search: str = None, **filters) -> Dict[str, Any]:
        """Get clients with optional filtering."""
        params = {'page': page}
        if search:
            params['search'] = search
        params.update(filters)
        return self.get('clients/', params=params, use_cache=True)
    
    def get_client(self, client_id: int) -> Dict[str, Any]:
        """Get a specific client by ID."""
        return self.get(f'clients/{client_id}/', use_cache=True)
    
    def create_client(self, client_data: Dict) -> Dict[str, Any]:
        """Create a new client."""
        return self.post('clients/', data=client_data)
    
    def update_client(self, client_id: int, client_data: Dict) -> Dict[str, Any]:
        """Update an existing client."""
        result = self.put(f'clients/{client_id}/', data=client_data)
        # Invalidar cache después de actualizar (compatible con LocMemCache)
        cache_key = f'forge_api:clients_{client_id}_'
        cache.delete(cache_key)
        return result
    
    def delete_client(self, client_id: int) -> Dict[str, Any]:
        """Delete a client."""
        return self.delete(f'clients/{client_id}/')
    
    def get_workorders(self, page: int = 1, client_id: int = None, status: str = None, **filters) -> Dict[str, Any]:
        """Get work orders with optional filtering."""
        params = {'page': page}
        if client_id:
            params['client'] = client_id
        if status:
            params['status'] = status
        params.update(filters)
        return self.get('work-orders/', params=params, use_cache=True)
    
    def get_workorder(self, workorder_id: int) -> Dict[str, Any]:
        """Get a specific work order by ID."""
        return self.get(f'work-orders/{workorder_id}/', use_cache=True)
    
    def create_workorder(self, workorder_data: Dict) -> Dict[str, Any]:
        """Create a new work order."""
        return self.post('work-orders/', data=workorder_data)
    
    def update_workorder(self, workorder_id: int, workorder_data: Dict) -> Dict[str, Any]:
        """Update an existing work order."""
        result = self.put(f'work-orders/{workorder_id}/', data=workorder_data)
        # Invalidate work order cache after update
        cache_key = f'forge_api:work-orders_{workorder_id}_'
        cache.delete(cache_key)
        return result
    
    def delete_workorder(self, workorder_id: int) -> bool:
        """Delete a work order."""
        return self.delete(f'work-orders/{workorder_id}/')

    def get_invoices(self, page: int = 1, client_id: int = None, status: str = None, **filters) -> Dict[str, Any]:
        """Get invoices with optional filtering."""
        params = {'page': page}
        if client_id:
            params['client'] = client_id
        if status:
            params['status'] = status
        params.update(filters)
        return self.get('invoices/', params=params, use_cache=True)

    def get_invoice(self, invoice_id: int) -> Dict[str, Any]:
        """Get detailed invoice information."""
        return self.get(f'invoices/{invoice_id}/', use_cache=True)

    def create_invoice(self, invoice_data: Dict) -> Dict[str, Any]:
        """Create a new invoice."""
        return self.post('invoices/', data=invoice_data)

    def update_invoice(self, invoice_id: int, invoice_data: Dict) -> Dict[str, Any]:
        """Update an existing invoice."""
        return self.put(f'invoices/{invoice_id}/', data=invoice_data)

    def delete_invoice(self, invoice_id: int) -> Dict[str, Any]:
        """Delete an invoice."""
        return self.delete(f'invoices/{invoice_id}/')
    
    # Quote methods (Tarea 6.4)
    def get_quotes(self, page: int = 1, client_id: int = None, status: str = None, **filters) -> Dict[str, Any]:
        """Get quotes with optional filtering."""
        params = {'page': page}
        if client_id:
            params['client_id'] = client_id
        if status:
            params['status'] = status
        params.update(filters)
        return self.get('quotes/', params=params)
    
    def get_quote(self, quote_id: int) -> Dict[str, Any]:
        """Get a specific quote by ID."""
        return self.get(f'quotes/{quote_id}/')
    
    def create_quote(self, quote_data: Dict) -> Dict[str, Any]:
        """Create a new quote."""
        return self.post('quotes/', data=quote_data)
    
    def update_quote(self, quote_id: int, quote_data: Dict) -> Dict[str, Any]:
        """Update an existing quote."""
        return self.put(f'quotes/{quote_id}/', data=quote_data)
    
    def delete_quote(self, quote_id: int) -> Dict[str, Any]:
        """Delete a quote."""
        return self.delete(f'quotes/{quote_id}/')
    
    def get_quote_items(self, quote_id: int = None, **filters) -> Dict[str, Any]:
        """Get quote items with optional filtering."""
        params = {}
        if quote_id:
            params['quote_id'] = quote_id
        params.update(filters)
        return self.get('quote-items/', params=params)
    
    def create_quote_item(self, item_data: Dict) -> Dict[str, Any]:
        """Create a new quote item."""
        return self.post('quote-items/', data=item_data)
    
    def update_quote_item(self, item_id: int, item_data: Dict) -> Dict[str, Any]:
        """Update an existing quote item."""
        return self.put(f'quote-items/{item_id}/', data=item_data)
    
    def delete_quote_item(self, item_id: int) -> Dict[str, Any]:
        """Delete a quote item."""
        return self.delete(f'quote-items/{item_id}/')
    
    def convert_quote_to_work_order(self, quote_id: int, wo_data: Dict = None) -> Dict[str, Any]:
        """Convert a quote to a work order."""
        endpoint = f'quotes/{quote_id}/convert-to-work-order/'
        return self.post(endpoint, data=wo_data or {})
    
    def get_equipment(self, page: int = 1, client_id: int = None, **filters) -> Dict[str, Any]:
        """Get equipment with optional filtering."""
        params = {'page': page}
        if client_id:
            params['client'] = client_id
        params.update(filters)
        return self.get('equipment/', params=params, use_cache=True)
    
    def get_equipment_detail(self, equipment_id: int) -> Dict[str, Any]:
        """Get detailed equipment information."""
        return self.get(f'equipment/{equipment_id}/', use_cache=True)
    
    def create_equipment(self, equipment_data: Dict) -> Dict[str, Any]:
        """Create a new equipment."""
        return self.post('equipment/', data=equipment_data)
    
    def update_equipment(self, equipment_id: int, equipment_data: Dict) -> Dict[str, Any]:
        """Update an existing equipment."""
        result = self.put(f'equipment/{equipment_id}/', data=equipment_data)
        # Invalidate equipment cache after update
        cache_key = f'forge_api:equipment_{equipment_id}_'
        cache.delete(cache_key)
        return result
    
    def delete_equipment(self, equipment_id: int) -> Dict[str, Any]:
        """Delete an equipment."""
        return self.delete(f'equipment/{equipment_id}/')
    
    def get_products(self, type: str = None, page: int = 1, page_size: int = 50, **filters) -> Dict[str, Any]:
        """Get products/services with optional filtering."""
        params = {'page': page, 'page_size': page_size}
        
        if type:
            params['type'] = type
        
        for key, value in filters.items():
            if value:
                params[key] = value
        
        return self.get('products/', params=params, use_cache=True)
    
    def get_technicians(self, page: int = 1, page_size: int = 50, **filters) -> Dict[str, Any]:
        """Get technicians with optional filtering."""
        params = {'page': page, 'page_size': page_size}
        
        for key, value in filters.items():
            if value:
                params[key] = value
        
        return self.get('technicians/', params=params, use_cache=False)
    
    def get_technician(self, technician_id: int) -> Dict[str, Any]:
        """Get detailed technician information."""
        return self.get(f'technicians/{technician_id}/', use_cache=False)

    def create_technician(self, technician_data: Dict) -> Dict[str, Any]:
        """Create a new technician."""
        return self.post('technicians/', data=technician_data)

    def update_technician(self, technician_id: int, technician_data: Dict) -> Dict[str, Any]:
        """Update an existing technician."""
        result = self.put(f'technicians/{technician_id}/', data=technician_data)
        # Invalidar cache después de actualizar (compatible con LocMemCache)
        cache_key = f'forge_api:technicians_{technician_id}_'
        cache.delete(cache_key)
        return result

    def delete_technician(self, technician_id: int) -> Dict[str, Any]:
        """Delete a technician."""
        return self.delete(f'technicians/{technician_id}/')

    def get_inventory(self, page: int = 1, low_stock: bool = None, **filters) -> Dict[str, Any]:
        """Get inventory items with optional filtering."""
        params = {'page': page}
        if low_stock is not None:
            params['low_stock'] = low_stock
        params.update(filters)
        return self.get('inventory/', params=params, use_cache=True)
    
    # Supplier methods
    def get_suppliers(self, page: int = 1, search: str = None, **filters) -> Dict[str, Any]:
        """Get suppliers with optional filtering."""
        params = {'page': page}
        if search:
            params['search'] = search
        params.update(filters)
        return self.get('suppliers/', params=params, use_cache=True)
    
    def get_supplier(self, supplier_id: int) -> Dict[str, Any]:
        """Get a specific supplier by ID."""
        return self.get(f'suppliers/{supplier_id}/', use_cache=True)
    
    def create_supplier(self, supplier_data: Dict) -> Dict[str, Any]:
        """Create a new supplier."""
        return self.post('suppliers/', data=supplier_data)
    
    def update_supplier(self, supplier_id: int, supplier_data: Dict) -> Dict[str, Any]:
        """Update an existing supplier."""
        return self.put(f'suppliers/{supplier_id}/', data=supplier_data)
    
    def delete_supplier(self, supplier_id: int) -> Dict[str, Any]:
        """Delete a supplier."""
        return self.delete(f'suppliers/{supplier_id}/')
    
    # Purchase Order methods
    def get_purchase_orders(self, page: int = 1, search: str = None, **filters) -> Dict[str, Any]:
        """Get purchase orders with optional filtering."""
        params = {'page': page}
        if search:
            params['search'] = search
        params.update(filters)
        return self.get('purchase-orders/', params=params, use_cache=True)
    
    def get_purchase_order(self, po_id: int) -> Dict[str, Any]:
        """Get a specific purchase order by ID."""
        return self.get(f'purchase-orders/{po_id}/', use_cache=True)
    
    def create_purchase_order(self, po_data: Dict) -> Dict[str, Any]:
        """Create a new purchase order."""
        return self.post('purchase-orders/', data=po_data)
    
    def update_purchase_order(self, po_id: int, po_data: Dict) -> Dict[str, Any]:
        """Update an existing purchase order."""
        return self.put(f'purchase-orders/{po_id}/', data=po_data)
    
    def delete_purchase_order(self, po_id: int) -> Dict[str, Any]:
        """Delete a purchase order."""
        return self.delete(f'purchase-orders/{po_id}/')
    
    # Purchase Order Item methods
    def get_po_items(self, po_id: int = None, **filters) -> Dict[str, Any]:
        """Get purchase order items with optional filtering."""
        params = {}
        if po_id:
            params['po'] = po_id
        params.update(filters)
        return self.get('po-items/', params=params)
    
    def get_po_item(self, item_id: int) -> Dict[str, Any]:
        """Get a specific purchase order item by ID."""
        return self.get(f'po-items/{item_id}/')
    
    def create_po_item(self, item_data: Dict) -> Dict[str, Any]:
        """Create a new purchase order item."""
        return self.post('po-items/', data=item_data)
    
    def update_po_item(self, item_id: int, item_data: Dict) -> Dict[str, Any]:
        """Update an existing purchase order item."""
        return self.put(f'po-items/{item_id}/', data=item_data)
    
    def delete_po_item(self, item_id: int) -> Dict[str, Any]:
        """Delete a purchase order item."""
        return self.delete(f'po-items/{item_id}/')
    
    # Equipment Type methods
    def get_equipment_types(self, page: int = 1, **filters) -> Dict[str, Any]:
        """Get equipment types with optional filtering."""
        params = {'page': page}
        params.update(filters)
        return self.get('equipment-types/', params=params, use_cache=True)
    
    def get_equipment_type(self, type_id: int) -> Dict[str, Any]:
        """Get a specific equipment type by ID."""
        return self.get(f'equipment-types/{type_id}/', use_cache=True)
    
    def create_equipment_type(self, type_data: Dict) -> Dict[str, Any]:
        """Create a new equipment type."""
        result = self.post('equipment-types/', data=type_data)
        # Immediately invalidate equipment types cache after creation
        cache.delete('forge_api:equipment-types')
        cache.delete('forge_api:equipment-types_')
        return result
    
    def update_equipment_type(self, type_id: int, type_data: Dict) -> Dict[str, Any]:
        """Update an existing equipment type."""
        result = self.put(f'equipment-types/{type_id}/', data=type_data)
        # Immediately invalidate equipment types cache after update
        cache.delete('forge_api:equipment-types')
        cache.delete('forge_api:equipment-types_')
        # Also invalidate the specific equipment type cache
        cache_key = f'forge_api:equipment-types_{type_id}_'
        cache.delete(cache_key)
        return result
    
    def delete_equipment_type(self, type_id: int) -> Dict[str, Any]:
        """Delete an equipment type."""
        return self.delete(f'equipment-types/{type_id}/')

    # Catalog Methods
    def get_fuel_codes(self, page: int = 1, **filters) -> Dict[str, Any]:
        """Get fuel codes with optional filtering."""
        params = {'page': page}
        params.update(filters)
        return self.get('fuel-codes/', params=params, use_cache=True)

    def get_aspiration_codes(self, page: int = 1, **filters) -> Dict[str, Any]:
        """Get aspiration codes with optional filtering."""
        params = {'page': page}
        params.update(filters)
        return self.get('aspiration-codes/', params=params, use_cache=True)

    def get_transmission_codes(self, page: int = 1, **filters) -> Dict[str, Any]:
        """Get transmission codes with optional filtering."""
        params = {'page': page}
        params.update(filters)
        return self.get('transmission-codes/', params=params, use_cache=True)

    def get_drivetrain_codes(self, page: int = 1, **filters) -> Dict[str, Any]:
        """Get drivetrain codes with optional filtering."""
        params = {'page': page}
        params.update(filters)
        return self.get('drivetrain-codes/', params=params, use_cache=True)

    def get_color_codes(self, page: int = 1, **filters) -> Dict[str, Any]:
        """Get color codes with optional filtering."""
        params = {'page': page}
        params.update(filters)
        return self.get('color-codes/', params=params, use_cache=True)
    
    # Currency methods
    def get_currencies(self, page: int = 1, **filters) -> Dict[str, Any]:
        """Get currencies with optional filtering."""
        params = {'page': page}
        params.update(filters)
        return self.get('currencies/', params=params, use_cache=True)
    
    def get_currency(self, currency_code: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Get a specific currency by code.
        
        Args:
            currency_code: The currency code (e.g., 'USD')
            use_cache: Whether to use caching (default True)
        """
        return self.get(f'currencies/{currency_code}/', use_cache=use_cache)
    
    def create_currency(self, currency_data: Dict) -> Dict[str, Any]:
        """Create a new currency."""
        return self.post('currencies/', data=currency_data)
    
    def update_currency(self, currency_code: str, currency_data: Dict) -> Dict[str, Any]:
        """Update an existing currency."""
        # Invalidate ALL currency caches aggressively
        # This includes: specific currency, list view, search results, etc.
        
        # Clear all possible cache keys for currencies
        cache_patterns = [
            'forge_api:currencies',
            'forge_api:currencies:',
            'forge_api:currencies_',
            'forge_api:currencies_list',
            'forge_api:currencies_list_',
            f'forge_api:currencies_{currency_code}_',
            f'forge_api:currencies_{currency_code}',
        ]
        
        for pattern in cache_patterns:
            try:
                # Try to delete using pattern matching
                if hasattr(cache, 'keys'):
                    keys = cache.keys(f'{pattern}*')
                    if keys:
                        cache.delete_many(keys)
                else:
                    # Fallback: try to delete specific keys
                    cache.delete(pattern)
            except Exception as e:
                logger.debug(f"Could not invalidate cache pattern {pattern}: {e}")
        
        # Also try to invalidate using the _invalidate_related_cache method
        try:
            self._invalidate_related_cache(f'currencies/{currency_code}')
        except Exception as e:
            logger.debug(f"Could not invalidate related cache: {e}")
        
        return self.put(f'currencies/{currency_code}/', data=currency_data)
    
    def delete_currency(self, currency_code: str) -> Dict[str, Any]:
        """Delete a currency."""
        return self.delete(f'currencies/{currency_code}/')
    
    def get_oem_brands(self, page: int = 1, page_size: int = 1000, **filters) -> Dict[str, Any]:
        """
        Get OEM brands (manufacturers/suppliers) with optional filtering.
        
        Common filters:
        - is_active=True
        - brand_type='VEHICLE_MFG' / 'EQUIPMENT_MFG' / 'MIXED'
        """
        params = {'page': page, 'page_size': page_size}
        params.update(filters)
        return self.get('oem-brands/', params=params, use_cache=True)
    
    def get_oem_catalog_items(self, page: int = 1, page_size: int = 1000, use_cache: bool = True, **filters) -> Dict[str, Any]:
        """
        Get OEM catalog items (models/parts) with optional filtering.
        
        Common filters:
        - oem_code=<brand oem_code>
        - item_type='VEHICLE_MODEL' / 'EQUIPMENT_MODEL' / 'PART'
        - is_active=True
        - is_discontinued=False
        """
        params = {'page': page, 'page_size': page_size}
        params.update(filters)
        return self.get('oem-catalog-items/', params=params, use_cache=use_cache)
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get dashboard KPI data."""
        return self.get('dashboard/', use_cache=True, cache_timeout=60)  # Cache for 1 minute
    
    # Utility methods
    def clear_cache(self, pattern: str = None):
        """Clear cached API responses - compatible con LocMemCache."""
        # LocMemCache no soporta delete_pattern, usamos delete() para claves específicas
        if pattern:
            # Eliminar clave específica basada en el patrón
            base_endpoint = pattern.rstrip('/').replace('/', '_')
            cache_key = f'forge_api:{base_endpoint}'
            cache.delete(cache_key)
        else:
            # No podemos limpar todo el cache de LocMemCache fácilmente
            # pero esto raramente se usa
            pass
    
    def health_check(self) -> bool:
        """Check if the API is accessible."""
        try:
            # Try multiple endpoints to get a better health check
            endpoints_to_check = [
                'health/',
                '',  # Root endpoint
                'auth/login/',  # Auth endpoint (should return method not allowed)
            ]
            
            for endpoint in endpoints_to_check:
                try:
                    response = requests.get(
                        f"{self.base_url}{endpoint}", 
                        timeout=5,
                        headers={'Accept': 'application/json'}
                    )
                    
                    # Accept 200, 405 (method not allowed), or 401 (unauthorized) as "healthy"
                    if response.status_code in [200, 401, 405]:
                        logger.debug(f"Health check passed on endpoint: {endpoint} (status: {response.status_code})")
                        return True
                        
                except requests.RequestException as e:
                    logger.debug(f"Health check failed on endpoint {endpoint}: {e}")
                    continue
            
            logger.warning("All health check endpoints failed")
            return False
            
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return False
    
    def is_api_available(self) -> bool:
        """
        Check if the API is available and responding.
        
        Returns:
            bool: True if API is available
        """
        try:
            response = requests.get(
                f"{self.base_url}health/", 
                timeout=5,
                headers={'Accept': 'application/json'}
            )
            
            if response.status_code == 200:
                logger.debug("API health check passed")
                return True
            else:
                logger.warning(f"API health check failed with status {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            logger.warning("API health check timed out")
            return False
        except requests.exceptions.ConnectionError:
            logger.warning("API health check connection failed")
            return False
        except requests.RequestException as e:
            logger.warning(f"API health check failed: {e}")
            return False
    
    # Maintenance Management Methods

    def get_maintenance_tasks(self, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get list of maintenance tasks with optional filtering.
        
        Args:
            params: Query parameters for filtering and pagination
            
        Returns:
            Dict containing maintenance tasks list and pagination info
        """
        try:
            response = self._make_request('GET', '/api/maintenance/', params=params)
            logger.info(f"Retrieved {len(response.get('results', []))} maintenance tasks")
            return response
        except APIException as e:
            logger.error(f"Failed to get maintenance tasks: {e.message}")
            raise

    def get_maintenance_task(self, maintenance_id: int) -> Dict[str, Any]:
        """
        Get detailed information for a specific maintenance task.
        
        Args:
            maintenance_id: ID of the maintenance task
            
        Returns:
            Dict containing maintenance task details
        """
        try:
            response = self._make_request('GET', f'/api/maintenance/{maintenance_id}/')
            logger.info(f"Retrieved maintenance task {maintenance_id}")
            return response
        except APIException as e:
            logger.error(f"Failed to get maintenance task {maintenance_id}: {e.message}")
            raise

    def create_maintenance_task(self, maintenance_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new maintenance task.
        
        Args:
            maintenance_data: Dict containing maintenance task information
            
        Returns:
            Dict containing created maintenance task data
        """
        try:
            response = self._make_request('POST', '/api/maintenance/', data=maintenance_data)
            logger.info(f"Created maintenance task: {response.get('title', 'Unknown')}")
            return response
        except APIException as e:
            logger.error(f"Failed to create maintenance task: {e.message}")
            raise

    def update_maintenance_task(self, maintenance_id: int, maintenance_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing maintenance task.
        
        Args:
            maintenance_id: ID of the maintenance task to update
            maintenance_data: Dict containing updated maintenance task information
            
        Returns:
            Dict containing updated maintenance task data
        """
        try:
            response = self._make_request('PUT', f'/api/maintenance/{maintenance_id}/', data=maintenance_data)
            logger.info(f"Updated maintenance task {maintenance_id}")
            return response
        except APIException as e:
            logger.error(f"Failed to update maintenance task {maintenance_id}: {e.message}")
            raise

    def delete_maintenance_task(self, maintenance_id: int) -> bool:
        """
        Delete a maintenance task.
        
        Args:
            maintenance_id: ID of the maintenance task to delete
            
        Returns:
            True if deletion was successful
        """
        try:
            self._make_request('DELETE', f'/api/maintenance/{maintenance_id}/')
            logger.info(f"Deleted maintenance task {maintenance_id}")
            return True
        except APIException as e:
            logger.error(f"Failed to delete maintenance task {maintenance_id}: {e.message}")
            raise

    def get_maintenance_history(self, equipment_id: int = None, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get maintenance history, optionally filtered by equipment.
        
        Args:
            equipment_id: Optional equipment ID to filter by
            params: Additional query parameters
            
        Returns:
            Dict containing maintenance history
        """
        try:
            endpoint = '/api/maintenance/history/'
            if equipment_id:
                endpoint = f'/api/equipment/{equipment_id}/maintenance-history/'
            
            response = self._make_request('GET', endpoint, params=params)
            logger.info(f"Retrieved maintenance history")
            return response
        except APIException as e:
            logger.error(f"Failed to get maintenance history: {e.message}")
            raise

    def get_maintenance_calendar(self, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """
        Get maintenance tasks for calendar view.
        
        Args:
            start_date: Start date in ISO format (optional)
            end_date: End date in ISO format (optional)
            
        Returns:
            List of maintenance tasks formatted for calendar
        """
        try:
            params = {}
            if start_date:
                params['start_date'] = start_date
            if end_date:
                params['end_date'] = end_date
                
            response = self._make_request('GET', '/api/maintenance/calendar/', params=params)
            logger.info(f"Retrieved maintenance calendar data")
            return response.get('results', [])
        except APIException as e:
            logger.error(f"Failed to get maintenance calendar: {e.message}")
            raise

    def update_maintenance_status(self, maintenance_id: int, status: str, notes: str = None) -> Dict[str, Any]:
        """
        Update maintenance task status.
        
        Args:
            maintenance_id: ID of the maintenance task
            status: New status (scheduled, in_progress, completed, cancelled)
            notes: Optional notes about the status change
            
        Returns:
            Dict containing updated maintenance task data
        """
        try:
            data = {'status': status}
            if notes:
                data['status_notes'] = notes
            if status == 'completed':
                data['completed_date'] = datetime.now().isoformat()
                
            response = self._make_request('PATCH', f'/api/maintenance/{maintenance_id}/status/', data=data)
            logger.info(f"Updated maintenance task {maintenance_id} status to {status}")
            return response
        except APIException as e:
            logger.error(f"Failed to update maintenance task {maintenance_id} status: {e.message}")
            raise 
   # Stock Management Methods

    def get_stock_levels(self, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get stock levels with optional filtering.
        
        Args:
            params: Query parameters for filtering and pagination
            
        Returns:
            Dict containing stock levels list and pagination info
        """
        try:
            response = self._make_request('GET', 'stock/', params=params)
            logger.info(f"Retrieved {len(response.get('results', []))} stock levels")
            return response
        except APIException as e:
            logger.error(f"Failed to get stock levels: {e.message}")
            raise

    def get_stock_movements(self, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get stock movements with optional filtering.
        
        Args:
            params: Query parameters for filtering and pagination
            
        Returns:
            Dict containing stock movements list and pagination info
        """
        try:
            response = self._make_request('GET', 'stock/movements/', params=params)
            logger.info(f"Retrieved {len(response.get('results', []))} stock movements")
            return response
        except APIException as e:
            logger.error(f"Failed to get stock movements: {e.message}")
            raise

    def create_stock_movement(self, movement_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new stock movement.
        
        Args:
            movement_data: Dict containing stock movement information
            
        Returns:
            Dict containing created stock movement data
        """
        try:
            response = self._make_request('POST', 'stock/movements/', data=movement_data)
            logger.info(f"Created stock movement for product {movement_data.get('product_id')}")
            return response
        except APIException as e:
            logger.error(f"Failed to create stock movement: {e.message}")
            raise

    def get_stock_alerts(self, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get stock alerts (low stock, out of stock, etc.).
        
        Args:
            params: Query parameters for filtering
            
        Returns:
            Dict containing stock alerts
        """
        try:
            response = self._make_request('GET', 'stock/alerts/', params=params)
            logger.info(f"Retrieved stock alerts")
            return response
        except APIException as e:
            logger.error(f"Failed to get stock alerts: {e.message}")
            raise

    def get_stock_dashboard(self) -> Dict[str, Any]:
        """
        Get stock dashboard data with KPIs and metrics.
        
        Returns:
            Dict containing dashboard data
        """
        try:
            response = self._make_request('GET', 'stock/dashboard/')
            logger.info(f"Retrieved stock dashboard data")
            return response
        except APIException as e:
            logger.error(f"Failed to get stock dashboard: {e.message}")
            raise

    def bulk_stock_adjustment(self, adjustment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform bulk stock adjustments.
        
        Args:
            adjustment_data: Dict containing adjustment information
            
        Returns:
            Dict containing adjustment results
        """
        try:
            response = self._make_request('POST', 'stock/bulk-adjustment/', data=adjustment_data)
            logger.info(f"Performed bulk stock adjustment")
            return response
        except APIException as e:
            logger.error(f"Failed to perform bulk stock adjustment: {e.message}")
            raise

    # Warehouse Management Methods

    def get_warehouses(self, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get list of warehouses with optional filtering.
        
        Args:
            params: Query parameters for filtering and pagination
            
        Returns:
            Dict containing warehouses list and pagination info
        """
        try:
            response = self._make_request('GET', 'warehouses/', params=params)
            logger.info(f"Retrieved {len(response.get('results', []))} warehouses")
            return response
        except APIException as e:
            logger.error(f"Failed to get warehouses: {e.message}")
            raise

    def get_warehouse(self, warehouse_id: int) -> Dict[str, Any]:
        """
        Get detailed information for a specific warehouse.
        
        Args:
            warehouse_id: ID of the warehouse
            
        Returns:
            Dict containing warehouse details
        """
        try:
            response = self._make_request('GET', f'warehouses/{warehouse_id}/')
            logger.info(f"Retrieved warehouse {warehouse_id}")
            return response
        except APIException as e:
            logger.error(f"Failed to get warehouse {warehouse_id}: {e.message}")
            raise

    def create_warehouse(self, warehouse_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new warehouse.
        
        Args:
            warehouse_data: Dict containing warehouse information
            
        Returns:
            Dict containing created warehouse data
        """
        try:
            response = self._make_request('POST', 'warehouses/', data=warehouse_data)
            logger.info(f"Created warehouse: {response.get('name', 'Unknown')}")
            return response
        except APIException as e:
            logger.error(f"Failed to create warehouse: {e.message}")
            raise

    def update_warehouse(self, warehouse_id: int, warehouse_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing warehouse.
        
        Args:
            warehouse_id: ID of the warehouse to update
            warehouse_data: Dict containing updated warehouse information
            
        Returns:
            Dict containing updated warehouse data
        """
        try:
            response = self._make_request('PUT', f'warehouses/{warehouse_id}/', data=warehouse_data)
            logger.info(f"Updated warehouse {warehouse_id}")
            return response
        except APIException as e:
            logger.error(f"Failed to update warehouse {warehouse_id}: {e.message}")
            raise

    def delete_warehouse(self, warehouse_id: int) -> bool:
        """
        Delete a warehouse.
        
        Args:
            warehouse_id: ID of the warehouse to delete
            
        Returns:
            True if deletion was successful
        """
        try:
            self._make_request('DELETE', f'warehouses/{warehouse_id}/')
            logger.info(f"Deleted warehouse {warehouse_id}")
            return True
        except APIException as e:
            logger.error(f"Failed to delete warehouse {warehouse_id}: {e.message}")
            raise

    def get_warehouse_stock(self, warehouse_id: int, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get stock levels for a specific warehouse.
        
        Args:
            warehouse_id: ID of the warehouse
            params: Query parameters for filtering
            
        Returns:
            Dict containing warehouse stock levels
        """
        try:
            response = self._make_request('GET', f'warehouses/{warehouse_id}/stock/', params=params)
            logger.info(f"Retrieved stock for warehouse {warehouse_id}")
            return response
        except APIException as e:
            logger.error(f"Failed to get warehouse {warehouse_id} stock: {e.message}")
            raise

    def transfer_stock(self, transfer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transfer stock between warehouses.
        
        Args:
            transfer_data: Dict containing transfer information
            
        Returns:
            Dict containing transfer results
        """
        try:
            response = self._make_request('POST', 'stock/transfer/', data=transfer_data)
            logger.info(f"Transferred stock between warehouses")
            return response
        except APIException as e:
            logger.error(f"Failed to transfer stock: {e.message}")
            raise

    def get_inventory_reports(self, report_type: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get inventory reports.
        
        Args:
            report_type: Type of report (valuation, movement, aging, etc.)
            params: Query parameters for report generation
            
        Returns:
            Dict containing report data
        """
        try:
            response = self._make_request('GET', f'inventory/reports/{report_type}/', params=params)
            logger.info(f"Retrieved {report_type} inventory report")
            return response
        except APIException as e:
            logger.error(f"Failed to get {report_type} report: {e.message}")
            raise 
   # Stock Management Methods

    def get_stock_summary(self) -> Dict[str, Any]:
        """
        Get stock summary statistics.
        
        Returns:
            Dict containing stock summary data
        """
        try:
            response = self._make_request('GET', 'stock/summary/')
            logger.info("Retrieved stock summary")
            return response
        except APIException as e:
            logger.error(f"Failed to get stock summary: {e.message}")
            raise

    def get_stock_items(self, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get list of stock items with optional filtering.
        
        Args:
            params: Query parameters for filtering and pagination
            
        Returns:
            Dict containing stock items list and pagination info
        """
        try:
            response = self._make_request('GET', 'stock/', params=params)
            logger.info(f"Retrieved {len(response.get('results', []))} stock items")
            return response
        except APIException as e:
            logger.error(f"Failed to get stock items: {e.message}")
            raise

    def get_low_stock_items(self, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get items with low stock levels.
        
        Args:
            params: Query parameters for filtering
            
        Returns:
            Dict containing low stock items
        """
        try:
            response = self._make_request('GET', 'stock/low-stock/', params=params)
            logger.info(f"Retrieved {len(response.get('results', []))} low stock items")
            return response
        except APIException as e:
            logger.error(f"Failed to get low stock items: {e.message}")
            raise

    def create_stock_movement(self, movement_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new stock movement.
        
        Args:
            movement_data: Dict containing movement information
            
        Returns:
            Dict containing created movement data
        """
        try:
            response = self._make_request('POST', 'stock/movements/', data=movement_data)
            logger.info(f"Created stock movement for product {movement_data.get('product_id')}")
            return response
        except APIException as e:
            logger.error(f"Failed to create stock movement: {e.message}")
            raise

    def get_stock_movements(self, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get list of stock movements with optional filtering.
        
        Args:
            params: Query parameters for filtering and pagination
            
        Returns:
            Dict containing movements list and pagination info
        """
        try:
            response = self._make_request('GET', 'stock/movements/', params=params)
            logger.info(f"Retrieved {len(response.get('results', []))} stock movements")
            return response
        except APIException as e:
            logger.error(f"Failed to get stock movements: {e.message}")
            raise

    def get_stock_movement(self, movement_id: int) -> Dict[str, Any]:
        """
        Get detailed information for a specific stock movement.
        
        Args:
            movement_id: ID of the stock movement
            
        Returns:
            Dict containing movement details
        """
        try:
            response = self._make_request('GET', f'stock/movements/{movement_id}/')
            logger.info(f"Retrieved stock movement {movement_id}")
            return response
        except APIException as e:
            logger.error(f"Failed to get stock movement {movement_id}: {e.message}")
            raise

    # Warehouse Management Methods

    def get_warehouses(self, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get list of warehouses with optional filtering.
        
        Args:
            params: Query parameters for filtering and pagination
            
        Returns:
            Dict containing warehouses list and pagination info
        """
        try:
            response = self._make_request('GET', 'warehouses/', params=params)
            logger.info(f"Retrieved {len(response.get('results', []))} warehouses")
            return response
        except APIException as e:
            logger.error(f"Failed to get warehouses: {e.message}")
            raise

    def get_warehouse_detail(self, warehouse_id: int) -> Dict[str, Any]:
        """
        Get detailed information for a specific warehouse.
        
        Args:
            warehouse_id: ID of the warehouse
            
        Returns:
            Dict containing warehouse details
        """
        try:
            response = self._make_request('GET', f'warehouses/{warehouse_id}/')
            logger.info(f"Retrieved warehouse {warehouse_id}")
            return response
        except APIException as e:
            logger.error(f"Failed to get warehouse {warehouse_id}: {e.message}")
            raise

    def create_warehouse(self, warehouse_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new warehouse.
        
        Args:
            warehouse_data: Dict containing warehouse information
            
        Returns:
            Dict containing created warehouse data
        """
        try:
            response = self._make_request('POST', 'warehouses/', data=warehouse_data)
            logger.info(f"Created warehouse: {response.get('name', 'Unknown')}")
            return response
        except APIException as e:
            logger.error(f"Failed to create warehouse: {e.message}")
            raise

    def update_warehouse(self, warehouse_id: int, warehouse_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing warehouse.
        
        Args:
            warehouse_id: ID of the warehouse to update
            warehouse_data: Dict containing updated warehouse information
            
        Returns:
            Dict containing updated warehouse data
        """
        try:
            response = self._make_request('PUT', f'warehouses/{warehouse_id}/', data=warehouse_data)
            logger.info(f"Updated warehouse {warehouse_id}")
            return response
        except APIException as e:
            logger.error(f"Failed to update warehouse {warehouse_id}: {e.message}")
            raise

    def delete_warehouse(self, warehouse_id: int) -> bool:
        """
        Delete a warehouse.
        
        Args:
            warehouse_id: ID of the warehouse to delete
            
        Returns:
            True if deletion was successful
        """
        try:
            self._make_request('DELETE', f'warehouses/{warehouse_id}/')
            logger.info(f"Deleted warehouse {warehouse_id}")
            return True
        except APIException as e:
            logger.error(f"Failed to delete warehouse {warehouse_id}: {e.message}")
            raise

    def get_warehouse_stock(self, warehouse_id: int, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get stock items for a specific warehouse.
        
        Args:
            warehouse_id: ID of the warehouse
            params: Additional query parameters
            
        Returns:
            Dict containing warehouse stock items
        """
        try:
            response = self._make_request('GET', f'warehouses/{warehouse_id}/stock/', params=params)
            logger.info(f"Retrieved stock for warehouse {warehouse_id}")
            return response
        except APIException as e:
            logger.error(f"Failed to get warehouse {warehouse_id} stock: {e.message}")
            raise

    def create_stock_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a stock alert configuration.
        
        Args:
            alert_data: Dict containing alert configuration
            
        Returns:
            Dict containing created alert data
        """
        try:
            response = self._make_request('POST', 'stock/alerts/', data=alert_data)
            logger.info(f"Created stock alert for product {alert_data.get('product_id')}")
            return response
        except APIException as e:
            logger.error(f"Failed to create stock alert: {e.message}")
            raise

    def get_stock_alerts(self, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get list of stock alerts.
        
        Args:
            params: Query parameters for filtering
            
        Returns:
            Dict containing stock alerts
        """
        try:
            response = self._make_request('GET', 'stock/alerts/', params=params)
            logger.info(f"Retrieved stock alerts")
            return response
        except APIException as e:
            logger.error(f"Failed to get stock alerts: {e.message}")
            raise
    
    def get_diagnostic_info(self) -> Dict[str, Any]:
        """
        Get comprehensive diagnostic information about the API client.
        
        Returns:
            Dict containing diagnostic information
        """
        diagnostic_info = {
            'base_url': self.base_url,
            'timeout': self.timeout,
            'max_retries': self.max_retries,
            'session_headers': dict(self.session.headers),
            'has_auth_token': 'Authorization' in self.session.headers,
            'request_available': self.request is not None,
        }
        
        if self.request and hasattr(self.request, 'session'):
            diagnostic_info.update({
                'session_auth_token': bool(self.request.session.get('auth_token')),
                'session_refresh_token': bool(self.request.session.get('refresh_token')),
                'token_timestamp': self.request.session.get('token_timestamp'),
                'user_authenticated': getattr(self.request, 'user', None) and self.request.user.is_authenticated,
                'user_id': getattr(self.request.user, 'id', None) if hasattr(self.request, 'user') else None,
            })
        
        # Test connectivity
        try:
            health_status = self.health_check()
            diagnostic_info['health_check'] = health_status
        except Exception as e:
            diagnostic_info['health_check'] = False
            diagnostic_info['health_check_error'] = str(e)
        
        # Test a simple API call
        try:
            test_response = self._make_request('GET', '', use_cache=False)
            diagnostic_info['api_root_accessible'] = True
            diagnostic_info['api_root_response'] = test_response
        except APIException as e:
            diagnostic_info['api_root_accessible'] = False
            diagnostic_info['api_root_error'] = {
                'status_code': e.status_code,
                'message': e.message,
                'response_data': e.response_data
            }
        except Exception as e:
            diagnostic_info['api_root_accessible'] = False
            diagnostic_info['api_root_error'] = str(e)
        
        return diagnostic_info
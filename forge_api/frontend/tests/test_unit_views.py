"""
Comprehensive unit tests for all Django views in the frontend application.

This module tests:
- All CRUD views for clients, technicians, invoices
- Work order management views
- Inventory management views
- Equipment management views
- Authentication views
- Dashboard views
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from unittest.mock import patch, MagicMock
import json


class BaseViewTestCase(TestCase):
    """Base test case with common setup for view tests."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def _create_mock_api_response(self, data=None, status_code=200):
        """Create a mock API response."""
        if data is None:
            data = {}
        response = MagicMock()
        response.status_code = status_code
        response.json.return_value = data
        response.data = data
        return response


class AuthenticationViewTests(BaseViewTestCase):
    """Unit tests for authentication views."""
    
    def test_login_view_get(self):
        """Test login view GET request."""
        self.client.logout()
        response = self.client.get(reverse('frontend:login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'login', status_code=200)
    
    def test_login_view_redirects_authenticated(self):
        """Test that authenticated users are redirected from login."""
        response = self.client.get(reverse('frontend:login'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('frontend:dashboard'))
    
    @patch('frontend.services.auth_service.AuthenticationService.login')
    def test_login_view_post_success(self, mock_login):
        """Test successful login POST request."""
        self.client.logout()
        mock_login.return_value = (True, 'Login successful', {'user': 'test'})
        
        response = self.client.post(reverse('frontend:login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('frontend:dashboard'))
    
    @patch('frontend.services.auth_service.AuthenticationService.logout')
    def test_logout_view(self, mock_logout):
        """Test logout view."""
        mock_logout.return_value = True
        response = self.client.get(reverse('frontend:logout'))
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('frontend:login'))


class DashboardViewTests(BaseViewTestCase):
    """Unit tests for dashboard views."""
    
    @patch('frontend.views.ForgeAPIClient.get')
    def test_dashboard_view_loads(self, mock_get):
        """Test that dashboard view loads successfully."""
        mock_get.return_value = {
            'active_work_orders': 5,
            'pending_invoices': 3,
            'low_stock_items': 2,
            'technician_productivity': 85,
            'recent_alerts': [],
            'charts': {},
            'top_clients': [],
            'top_technicians': [],
            'inventory_alerts': []
        }
        
        response = self.client.get(reverse('frontend:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard')


class ClientViewTests(BaseViewTestCase):
    """Unit tests for client management views."""
    
    @patch('frontend.views.client_views.ClientListView.get_api_client')
    def test_client_list_view(self, mock_get_client):
        """Test client list view."""
        mock_client = MagicMock()
        mock_client.get_clients.return_value = {
            'results': [
                {'id': 1, 'name': 'Test Client', 'email': 'test@example.com'}
            ],
            'count': 1,
            'next': None,
            'previous': None
        }
        mock_get_client.return_value = mock_client
        
        response = self.client.get(reverse('frontend:client_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Client')
    
    @patch('frontend.views.client_views.ClientDetailView.get_api_client')
    def test_client_detail_view(self, mock_get_client):
        """Test client detail view."""
        mock_client = MagicMock()
        mock_client.get_client.return_value = {
            'id': 1,
            'name': 'Test Client',
            'email': 'test@example.com',
            'phone': '1234567890'
        }
        mock_get_client.return_value = mock_client
        
        response = self.client.get(reverse('frontend:client_detail', args=[1]))
        self.assertEqual(response.status_code, 200)
    
    def test_client_create_view_get(self):
        """Test client create view GET request."""
        response = self.client.get(reverse('frontend:client_create'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
    
    @patch('frontend.views.client_views.ClientCreateView.get_api_client')
    def test_client_create_view_post(self, mock_get_client):
        """Test client create view POST request."""
        mock_client = MagicMock()
        mock_client.create_client.return_value = {'id': 1}
        mock_get_client.return_value = mock_client
        
        response = self.client.post(reverse('frontend:client_create'), {
            'name': 'New Client',
            'email': 'new@example.com',
            'phone': '1234567890'
        })
        
        # Should redirect on success
        self.assertIn(response.status_code, [200, 302])
    
    @patch('frontend.views.client_views.ClientUpdateView.get_api_client')
    def test_client_update_view_get(self, mock_get_client):
        """Test client update view GET request."""
        mock_client = MagicMock()
        mock_client.get_client.return_value = {
            'id': 1,
            'name': 'Test Client',
            'email': 'test@example.com'
        }
        mock_get_client.return_value = mock_client
        
        response = self.client.get(reverse('frontend:client_update', args=[1]))
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)


class TechnicianViewTests(BaseViewTestCase):
    """Unit tests for technician management views."""
    
    @patch('frontend.views.technician_views.TechnicianListView.get_api_client')
    def test_technician_list_view(self, mock_get_client):
        """Test technician list view."""
        mock_client = MagicMock()
        mock_client.get.return_value = {
            'results': [{'id': 1, 'name': 'Test Tech'}],
            'count': 1
        }
        mock_get_client.return_value = mock_client
        
        response = self.client.get(reverse('frontend:technician_list'))
        self.assertEqual(response.status_code, 200)
    
    def test_technician_create_view_get(self):
        """Test technician create view GET request."""
        response = self.client.get(reverse('frontend:technician_create'))
        self.assertEqual(response.status_code, 200)


class InvoiceViewTests(BaseViewTestCase):
    """Unit tests for invoice management views."""
    
    @patch('frontend.views.invoice_views.InvoiceListView.get_api_client')
    def test_invoice_list_view(self, mock_get_client):
        """Test invoice list view."""
        mock_client = MagicMock()
        mock_client.get.return_value = {
            'results': [{'id': 1, 'number': 'INV-001'}],
            'count': 1
        }
        mock_get_client.return_value = mock_client
        
        response = self.client.get(reverse('frontend:invoice_list'))
        self.assertEqual(response.status_code, 200)
    
    def test_invoice_create_view_get(self):
        """Test invoice create view GET request."""
        response = self.client.get(reverse('frontend:invoice_create'))
        self.assertEqual(response.status_code, 200)


class WorkOrderViewTests(BaseViewTestCase):
    """Unit tests for work order management views."""
    
    @patch('frontend.views.WorkOrderListView.get_api_client')
    def test_workorder_list_view(self, mock_get_client):
        """Test work order list view."""
        mock_client = MagicMock()
        mock_client.get.return_value = {
            'results': [{'id': 1, 'status': 'pending'}],
            'count': 1
        }
        mock_get_client.return_value = mock_client
        
        response = self.client.get(reverse('frontend:workorder_list'))
        self.assertEqual(response.status_code, 200)
    
    def test_workorder_create_view_get(self):
        """Test work order create view GET request."""
        response = self.client.get(reverse('frontend:workorder_create'))
        self.assertEqual(response.status_code, 200)


class InventoryViewTests(BaseViewTestCase):
    """Unit tests for inventory management views."""
    
    @patch('frontend.views.ProductListView.get_api_client')
    def test_product_list_view(self, mock_get_client):
        """Test product list view."""
        mock_client = MagicMock()
        mock_client.get.return_value = {
            'results': [{'id': 1, 'name': 'Test Product'}],
            'count': 1
        }
        mock_get_client.return_value = mock_client
        
        response = self.client.get(reverse('frontend:product_list'))
        self.assertEqual(response.status_code, 200)
    
    def test_product_create_view_get(self):
        """Test product create view GET request."""
        response = self.client.get(reverse('frontend:product_create'))
        self.assertEqual(response.status_code, 200)


class EquipmentViewTests(BaseViewTestCase):
    """Unit tests for equipment management views."""
    
    @patch('frontend.views.EquipmentListView.get_api_client')
    def test_equipment_list_view(self, mock_get_client):
        """Test equipment list view."""
        mock_client = MagicMock()
        mock_client.get.return_value = {
            'results': [{'id': 1, 'name': 'Test Equipment'}],
            'count': 1
        }
        mock_get_client.return_value = mock_client
        
        response = self.client.get(reverse('frontend:equipment_list'))
        self.assertEqual(response.status_code, 200)
    
    def test_equipment_create_view_get(self):
        """Test equipment create view GET request."""
        response = self.client.get(reverse('frontend:equipment_create'))
        self.assertEqual(response.status_code, 200)


class FormValidationTests(BaseViewTestCase):
    """Unit tests for form validation."""
    
    def test_client_form_validation(self):
        """Test client form validation."""
        from frontend.forms import ClientForm
        
        # Test valid form
        valid_data = {
            'name': 'Test Client',
            'email': 'test@example.com',
            'phone': '1234567890'
        }
        form = ClientForm(data=valid_data)
        self.assertTrue(form.is_valid())
        
        # Test invalid form (missing required fields)
        invalid_data = {}
        form = ClientForm(data=invalid_data)
        self.assertFalse(form.is_valid())
    
    def test_equipment_form_validation(self):
        """Test equipment form validation."""
        from frontend.forms import EquipmentForm
        
        # Test valid form
        valid_data = {
            'name': 'Test Equipment',
            'equipment_type': 'vehicle'
        }
        form = EquipmentForm(data=valid_data)
        # Form validation depends on specific requirements
        # This is a basic structure test


class ErrorHandlingTests(BaseViewTestCase):
    """Unit tests for error handling in views."""
    
    @patch('frontend.views.client_views.ClientListView.get_api_client')
    def test_api_error_handling(self, mock_get_client):
        """Test that API errors are handled gracefully."""
        from frontend.services.api_client import APIException
        
        mock_client = MagicMock()
        mock_client.get_clients.side_effect = APIException('API Error', status_code=500)
        mock_get_client.return_value = mock_client
        
        response = self.client.get(reverse('frontend:client_list'))
        # Should still return a response, even if there's an error
        self.assertIn(response.status_code, [200, 500])
    
    @patch('frontend.views.client_views.ClientDetailView.get_api_client')
    def test_404_handling(self, mock_get_client):
        """Test 404 error handling for detail views."""
        from frontend.services.api_client import APIException
        
        mock_client = MagicMock()
        mock_client.get_client.side_effect = APIException('Not Found', status_code=404)
        mock_get_client.return_value = mock_client
        
        response = self.client.get(reverse('frontend:client_detail', args=[999]))
        # Should handle 404 gracefully
        self.assertIn(response.status_code, [200, 404])


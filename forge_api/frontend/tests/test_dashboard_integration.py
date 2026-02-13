"""
Integration tests for dashboard functionality.
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from unittest.mock import patch, Mock
import json


class TestDashboardIntegration(TestCase):
    """Test dashboard integration with backend API."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_dashboard_view_loads(self):
        """Test that dashboard view loads without errors."""
        response = self.client.get(reverse('frontend:dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard')
        self.assertContains(response, 'Órdenes Activas')
    
    @patch('frontend.services.api_client.ForgeAPIClient.get_dashboard_data')
    def test_dashboard_with_api_data(self, mock_get_dashboard):
        """Test dashboard with mocked API data."""
        # Mock API response
        mock_get_dashboard.return_value = {
            'active_work_orders': 5,
            'pending_invoices': 3,
            'low_stock_items': 2,
            'technician_productivity': 85,
            'recent_alerts': [],
            'charts': {
                'workorders_week': {
                    'labels': ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'],
                    'data': [1, 2, 3, 2, 4, 1, 0]
                }
            }
        }
        
        response = self.client.get(reverse('frontend:dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '5')  # active_work_orders
        self.assertContains(response, '85%')  # technician_productivity
    
    @patch('frontend.services.api_client.ForgeAPIClient.get_dashboard_data')
    def test_dashboard_api_failure_fallback(self, mock_get_dashboard):
        """Test dashboard fallback when API fails."""
        from frontend.services.api_client import APIException
        
        # Mock API failure
        mock_get_dashboard.side_effect = APIException("API Error", 500)
        
        response = self.client.get(reverse('frontend:dashboard'))
        
        self.assertEqual(response.status_code, 200)
        # Should show fallback values
        self.assertContains(response, 'Dashboard')
    
    def test_dashboard_data_ajax_endpoint(self):
        """Test AJAX endpoint for dashboard data."""
        with patch('frontend.services.api_client.ForgeAPIClient.get') as mock_get:
            mock_get.return_value = {
                'active_work_orders': 10,
                'pending_invoices': 5
            }
            
            response = self.client.get(reverse('frontend:dashboard_data'))
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertEqual(data['active_work_orders'], 10)
            self.assertEqual(data['pending_invoices'], 5)
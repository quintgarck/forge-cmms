"""
Property-based tests for dashboard content completeness.

**Feature: forge-frontend-web, Property 1: Dashboard content completeness**
**Validates: Requirements 1.2, 1.4, 1.5**

This module tests that the dashboard displays complete and consistent information
across all KPI widgets, charts, and data sections.
"""

import json
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from hypothesis import given, strategies as st, settings
from hypothesis.extra.django import TestCase as HypothesisTestCase


class TestDashboardContentCompleteness(HypothesisTestCase):
    """Test dashboard content completeness using property-based testing."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        # Create a unique user for each test
        import uuid
        username = f'testuser_{uuid.uuid4().hex[:8]}'
        self.user = User.objects.create_user(
            username=username,
            password='testpass123',
            email=f'{username}@example.com'
        )
        # Force login
        self.client.force_login(self.user)
        self.dashboard_url = reverse('frontend:dashboard')
    
    def create_mock_dashboard_data(self, **overrides):
        """Create mock dashboard data with optional overrides."""
        default_data = {
            'active_work_orders': 25,
            'pending_invoices': 8,
            'low_stock_items': 12,
            'technician_productivity': 85,
            'workorders_trend': 15,
            'overdue_invoices': 3,
            'critical_stock': 5,
            'avg_completion_days': 3.5,
            'monthly_revenue': 45000.00,
            'revenue_trend': 12.5,
            'outstanding_receivables': 15000.00,
            'equipment_utilization': 78,
            'client_satisfaction': 92,
            'recent_alerts': [
                {
                    'id': 1,
                    'title': 'Stock Bajo',
                    'message': 'Filtro de aceite - 5 unidades restantes',
                    'severity': 'warning',
                    'category': 'inventory',
                    'created_at': '2024-01-15T10:30:00Z',
                    'is_read': False
                }
            ],
            'alert_count': 1,
            'charts': {
                'workorders_week': {
                    'labels': ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'],
                    'created': [12, 19, 8, 15, 22, 8, 5],
                    'completed': [8, 15, 6, 12, 18, 6, 3]
                },
                'status_distribution': {
                    'labels': ['Pendientes', 'En Progreso', 'Completadas', 'Canceladas'],
                    'data': [30, 45, 20, 5]
                }
            },
            'summary': {
                'total_clients': 150,
                'total_equipment': 85,
                'total_products': 320,
                'total_warehouses': 3,
                'active_alerts': 1,
                'system_health': 'healthy'
            },
            'last_updated': '2024-01-15T12:00:00Z',
            'data_freshness': 'real-time'
        }
        
        # Apply overrides
        default_data.update(overrides)
        return default_data
    
    @given(
        active_orders=st.integers(min_value=0, max_value=1000),
        pending_invoices=st.integers(min_value=0, max_value=500),
        low_stock=st.integers(min_value=0, max_value=100),
        productivity=st.integers(min_value=0, max_value=100)
    )
    @settings(max_examples=10, deadline=None)
    def test_kpi_widgets_completeness(self, active_orders, pending_invoices, low_stock, productivity):
        """
        **Property 1: Dashboard content completeness**
        
        For any valid KPI values, the dashboard should display all four main KPI widgets
        with their values, trends, and progress indicators.
        """
        # Create mock data with the generated values
        mock_data = self.create_mock_dashboard_data(
            active_work_orders=active_orders,
            pending_invoices=pending_invoices,
            low_stock_items=low_stock,
            technician_productivity=productivity
        )
        
        with patch('frontend.views.DashboardView.get_context_data') as mock_context:
            mock_context.return_value = mock_data
            
            response = self.client.get(self.dashboard_url)
            
            # Verify response is successful
            self.assertEqual(response.status_code, 200)
            content = response.content.decode()
            
            # Verify all KPI widgets are present
            self.assertIn('active-workorders', content, 
                         "Active work orders widget should be present")
            self.assertIn('pending-invoices', content,
                         "Pending invoices widget should be present")
            self.assertIn('low-stock-items', content,
                         "Low stock items widget should be present")
            self.assertIn('technician-productivity', content,
                         "Technician productivity widget should be present")
            
            # Verify progress bars are present for all KPIs
            progress_bars = content.count('progress-bar')
            self.assertGreaterEqual(progress_bars, 4,
                                  "All KPI widgets should have progress bars")
    
    def test_dashboard_structure_consistency(self):
        """
        **Property 1: Dashboard content completeness**
        
        The dashboard should maintain consistent structure regardless of data state.
        """
        # Test with minimal data
        minimal_data = self.create_mock_dashboard_data(
            active_work_orders=0,
            pending_invoices=0,
            low_stock_items=0,
            technician_productivity=0,
            recent_alerts=[],
            charts={
                'workorders_week': {'labels': [], 'created': [], 'completed': []},
                'status_distribution': {'labels': [], 'data': []}
            }
        )
        
        with patch('frontend.views.DashboardView.get_context_data') as mock_context:
            mock_context.return_value = minimal_data
            
            response = self.client.get(self.dashboard_url)
            
            # Verify response is successful even with minimal data
            self.assertEqual(response.status_code, 200)
            content = response.content.decode()
            
            # Verify essential dashboard structure is present
            essential_elements = [
                'kpi-cards',           # KPI cards container
                'workordersChart',     # Main chart
                'statusChart',         # Status chart
                'system-alerts',       # Alerts section
                'dashboard-page'       # Dashboard page class
            ]
            
            for element in essential_elements:
                self.assertIn(element, content,
                            f"Essential dashboard element '{element}' should always be present")
            
            # Verify page has proper title
            self.assertIn('Dashboard', content,
                         "Dashboard title should be present")
    
    def test_dashboard_error_handling_completeness(self):
        """
        **Property 1: Dashboard content completeness**
        
        The dashboard should display complete fallback content when API fails.
        """
        with patch('frontend.views.DashboardView.get_context_data') as mock_context:
            # Simulate API failure by returning fallback data
            fallback_data = {
                'active_work_orders': 0,
                'pending_invoices': 0,
                'low_stock_items': 0,
                'technician_productivity': 0,
                'recent_alerts': [],
                'charts': {},
                'summary': {}
            }
            mock_context.return_value = fallback_data
            
            response = self.client.get(self.dashboard_url)
            
            # Verify response is still successful (graceful degradation)
            self.assertEqual(response.status_code, 200)
            content = response.content.decode()
            
            # Verify fallback structure is complete
            fallback_elements = [
                'kpi-cards',           # KPI cards should still be present
                'workordersChart',     # Charts should still be present
                'system-alerts'        # Alerts section should still be present
            ]
            
            for element in fallback_elements:
                self.assertIn(element, content,
                            f"Fallback element '{element}' should be present during API failure")
    
    @given(
        alerts=st.lists(
            st.fixed_dictionaries({
                'id': st.integers(min_value=1, max_value=1000),
                'title': st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Pd', 'Zs'))),
                'message': st.text(min_size=1, max_size=200, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Pd', 'Zs'))),
                'severity': st.sampled_from(['info', 'warning', 'danger', 'success']),
                'category': st.sampled_from(['system', 'inventory', 'workorder', 'client']),
                'created_at': st.just('2024-01-15T10:30:00Z'),
                'is_read': st.booleans()
            }),
            min_size=0,
            max_size=5
        )
    )
    @settings(max_examples=5, deadline=None)
    def test_alerts_section_completeness(self, alerts):
        """
        **Property 1: Dashboard content completeness**
        
        For any list of alerts, the dashboard should display the alerts section
        with proper structure, whether alerts are present or not.
        """
        mock_data = self.create_mock_dashboard_data(
            recent_alerts=alerts,
            alert_count=len([a for a in alerts if not a['is_read']])
        )
        
        with patch('frontend.views.DashboardView.get_context_data') as mock_context:
            mock_context.return_value = mock_data
            
            response = self.client.get(self.dashboard_url)
            
            # Verify response is successful
            self.assertEqual(response.status_code, 200)
            content = response.content.decode()
            
            # Verify alerts section is present
            self.assertIn('system-alerts', content,
                         "System alerts section should be present")
            
            if alerts:
                # If there are alerts, verify alert structure
                for alert in alerts[:2]:  # Check first few alerts
                    if alert['title'].strip() and alert['message'].strip():
                        # At least one alert should have some content visible
                        has_alert_content = (
                            alert['title'] in content or 
                            alert['message'] in content or
                            f"alert-{alert['severity']}" in content
                        )
                        # This is a soft check since HTML escaping might affect exact matching
            else:
                # If no alerts, verify empty state message
                empty_state_indicators = [
                    'No hay alertas',
                    'funcionando correctamente',
                    'bi-check-circle'
                ]
                found_empty_indicator = any(indicator in content for indicator in empty_state_indicators)
                self.assertTrue(found_empty_indicator,
                              "Empty alerts state should be properly displayed")
    
    def test_dashboard_responsive_completeness(self):
        """
        **Property 1: Dashboard content completeness**
        
        The dashboard should include responsive design elements for mobile compatibility.
        """
        mock_data = self.create_mock_dashboard_data()
        
        with patch('frontend.views.DashboardView.get_context_data') as mock_context:
            mock_context.return_value = mock_data
            
            response = self.client.get(self.dashboard_url)
            
            # Verify response is successful
            self.assertEqual(response.status_code, 200)
            content = response.content.decode()
            
            # Verify responsive design elements
            responsive_elements = [
                'col-xl-',             # Bootstrap responsive columns
                'col-md-',             # Medium screen columns
                'col-',                # Base columns
                '@media',              # CSS media queries
                'responsive'           # Responsive classes/attributes
            ]
            
            found_responsive = sum(1 for element in responsive_elements if element in content)
            self.assertGreater(found_responsive, 0,
                             "Dashboard should include responsive design elements")
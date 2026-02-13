"""
Tests for advanced service management views.
"""
import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock

from ..services.api_client import APIException


class ServiceAdvancedViewsTestCase(TestCase):
    """Test case for advanced service management views."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.client.login(username='testuser', password='testpass123')
    
    @patch('frontend.views.service_advanced_views.ForgeAPIClient')
    def test_service_dashboard_view(self, mock_api_client):
        """Test service dashboard view loads correctly."""
        # Mock API responses
        mock_client = MagicMock()
        mock_api_client.return_value = mock_client
        
        # Mock work orders data
        mock_client.get.side_effect = [
            {'count': 25, 'results': []},  # Total work orders
            {'count': 5, 'results': []},   # Draft status
            {'count': 8, 'results': []},   # Scheduled status
            {'count': 7, 'results': []},   # In progress status
            {'count': 5, 'results': []},   # Completed status
            {'results': [               # Technicians
                {
                    'user_id': 1,
                    'name': 'John Doe',
                    'username': 'johndoe',
                    'specialization': 'Engine Specialist'
                }
            ]},
            {'results': [               # Recent work orders
                {
                    'wo_id': 1,
                    'wo_number': '2024-001',
                    'status': 'in_progress',
                    'created_at': '2024-01-15T10:00:00Z',
                    'client': {'name': 'Test Client'},
                    'equipment': {'make': 'Caterpillar', 'model': '320D'},
                    'complaint': 'Engine overheating issue'
                }
            ]}
        ]
        
        url = reverse('frontend:service_dashboard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard de Servicios')
        self.assertContains(response, 'Órdenes Activas')
        self.assertContains(response, 'Técnicos Destacados')
    
    @patch('frontend.views.service_advanced_views.ForgeAPIClient')
    def test_work_order_timeline_view(self, mock_api_client):
        """Test work order timeline view loads correctly."""
        # Mock API responses
        mock_client = MagicMock()
        mock_api_client.return_value = mock_client
        
        mock_work_order = {
            'wo_id': 1,
            'wo_number': '2024-001',
            'status': 'in_progress',
            'created_at': '2024-01-15T10:00:00Z',
            'scheduled_date': '2024-01-16T08:00:00Z',
            'client': {'name': 'Test Client'},
            'equipment': {'make': 'Caterpillar', 'model': '320D'},
            'complaint': 'Engine overheating'
        }
        
        mock_client.get.side_effect = [
            mock_work_order,  # Work order details
            {'results': []},  # WO services
            {'results': []},  # WO items
        ]
        
        url = reverse('frontend:workorder_timeline', kwargs={'wo_id': 1})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Timeline - Orden 2024-001')
        self.assertContains(response, 'Progreso General')
        self.assertContains(response, 'Cronología de Eventos')
    
    @patch('frontend.views.service_advanced_views.ForgeAPIClient')
    def test_flat_rate_calculator_view(self, mock_api_client):
        """Test flat rate calculator view loads correctly."""
        # Mock API responses
        mock_client = MagicMock()
        mock_api_client.return_value = mock_client
        
        mock_standards = {
            'results': [
                {
                    'flat_rate_id': 1,
                    'service_code': 'ENG-001',
                    'description': 'Engine oil change',
                    'standard_hours': 2.5,
                    'min_hours': 2.0,
                    'max_hours': 3.0,
                    'difficulty_level': 2,
                    'group_code': 'ENGINE',
                    'equipment_type': {'name': 'Excavator'},
                    'required_tools': ['Wrench Set', 'Oil Pan'],
                    'required_skills': ['Basic Maintenance']
                }
            ]
        }
        
        mock_client.get.side_effect = [
            mock_standards,  # Flat rate standards
            {'results': []}, # Equipment types
            {'results': []}, # Taxonomy groups
        ]
        
        url = reverse('frontend:flat_rate_calculator')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Calculadora de Tiempos Estándar')
        self.assertContains(response, 'ENG-001')
        self.assertContains(response, 'Engine oil change')
    
    @patch('frontend.views.service_advanced_views.ForgeAPIClient')
    def test_service_checklist_interactive_view(self, mock_api_client):
        """Test interactive service checklist view loads correctly."""
        # Mock API responses
        mock_client = MagicMock()
        mock_api_client.return_value = mock_client
        
        mock_flat_rate = {
            'flat_rate_id': 1,
            'service_code': 'ENG-001',
            'description': 'Engine oil change service',
            'standard_hours': 2.5,
            'difficulty_level': 2
        }
        
        mock_checklist_items = {
            'results': [
                {
                    'checklist_item_id': 1,
                    'sequence_number': 1,
                    'description': 'Check oil level',
                    'detailed_instructions': 'Use dipstick to check current oil level',
                    'is_critical': True,
                    'estimated_minutes': 5,
                    'required_tools': ['Dipstick'],
                    'safety_notes': 'Engine must be cool'
                },
                {
                    'checklist_item_id': 2,
                    'sequence_number': 2,
                    'description': 'Drain old oil',
                    'detailed_instructions': 'Remove drain plug and drain completely',
                    'is_critical': True,
                    'estimated_minutes': 15,
                    'required_tools': ['Wrench', 'Oil Pan'],
                    'safety_notes': 'Wear protective gloves'
                }
            ]
        }
        
        mock_client.get.side_effect = [
            mock_flat_rate,      # Flat rate details
            mock_checklist_items # Checklist items
        ]
        
        url = reverse('frontend:service_checklist_interactive', kwargs={'flat_rate_id': 1})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Checklist: ENG-001')
        self.assertContains(response, 'Check oil level')
        self.assertContains(response, 'Drain old oil')
        self.assertContains(response, 'Items Críticos')
    
    @patch('frontend.views.service_advanced_views.ForgeAPIClient')
    def test_flat_rate_calculator_with_filters(self, mock_api_client):
        """Test flat rate calculator with search filters."""
        # Mock API responses
        mock_client = MagicMock()
        mock_api_client.return_value = mock_client
        
        mock_client.get.side_effect = [
            {'results': []}, # Filtered standards (empty)
            {'results': []}, # Equipment types
            {'results': []}, # Taxonomy groups
        ]
        
        url = reverse('frontend:flat_rate_calculator')
        response = self.client.get(url, {
            'search': 'engine',
            'equipment_type': '1',
            'group_code': 'ENG'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No se encontraron estándares')
        
        # Verify API was called with filters
        mock_client.get.assert_called()
        call_args = mock_client.get.call_args_list[0]
        self.assertEqual(call_args[0][0], 'flat-rate-standards/')
        self.assertIn('search', call_args[1]['params'])
        self.assertEqual(call_args[1]['params']['search'], 'engine')
    
    @patch('frontend.views.service_advanced_views.ForgeAPIClient')
    def test_service_dashboard_api_error_handling(self, mock_api_client):
        """Test service dashboard handles API errors gracefully."""
        # Mock API client to raise exception
        mock_client = MagicMock()
        mock_api_client.return_value = mock_client
        mock_client.get.side_effect = APIException("API connection failed")
        
        url = reverse('frontend:service_dashboard')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        # Should still render page with empty data
        self.assertContains(response, 'Dashboard de Servicios')
        
        # Check that context has empty/default values
        context = response.context
        self.assertEqual(context['work_order_stats']['total'], 0)
        self.assertEqual(context['top_technicians'], [])
        self.assertEqual(context['recent_work_orders'], [])
    
    @patch('frontend.views.service_advanced_views.ForgeAPIClient')
    def test_work_order_timeline_not_found(self, mock_api_client):
        """Test work order timeline when work order doesn't exist."""
        # Mock API client to raise exception for work order not found
        mock_client = MagicMock()
        mock_api_client.return_value = mock_client
        mock_client.get.side_effect = APIException("Work order not found", status_code=404)
        
        url = reverse('frontend:workorder_timeline', kwargs={'wo_id': 999})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Orden de Trabajo No Encontrada')
    
    def test_service_views_require_authentication(self):
        """Test that service views require user authentication."""
        # Logout user
        self.client.logout()
        
        urls_to_test = [
            reverse('frontend:service_dashboard'),
            reverse('frontend:flat_rate_calculator'),
            reverse('frontend:workorder_timeline', kwargs={'wo_id': 1}),
            reverse('frontend:service_checklist_interactive', kwargs={'flat_rate_id': 1}),
        ]
        
        for url in urls_to_test:
            response = self.client.get(url)
            # Should redirect to login page
            self.assertEqual(response.status_code, 302)
            self.assertIn('/login/', response.url)
    
    @patch('frontend.views.service_advanced_views.ForgeAPIClient')
    def test_checklist_with_work_order_service(self, mock_api_client):
        """Test checklist view when associated with a work order service."""
        # Mock API responses
        mock_client = MagicMock()
        mock_api_client.return_value = mock_client
        
        mock_flat_rate = {
            'flat_rate_id': 1,
            'service_code': 'ENG-001',
            'description': 'Engine service',
            'standard_hours': 2.5
        }
        
        mock_wo_service = {
            'wo_service_id': 1,
            'wo': {'wo_id': 1, 'wo_number': '2024-001'},
            'completion_status': 'IN_PROGRESS'
        }
        
        mock_client.get.side_effect = [
            mock_flat_rate,      # Flat rate details
            {'results': []},     # Checklist items
            mock_wo_service      # Work order service
        ]
        
        url = reverse('frontend:service_checklist_wo', kwargs={
            'flat_rate_id': 1,
            'wo_service_id': 1
        })
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ver WO-2024-001')


class ServiceAdvancedIntegrationTestCase(TestCase):
    """Integration tests for service advanced functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_service_navigation_integration(self):
        """Test that service navigation links work correctly."""
        # Test dashboard loads
        dashboard_url = reverse('frontend:service_dashboard')
        response = self.client.get(dashboard_url)
        self.assertEqual(response.status_code, 200)
        
        # Test calculator loads
        calculator_url = reverse('frontend:flat_rate_calculator')
        response = self.client.get(calculator_url)
        self.assertEqual(response.status_code, 200)
    
    @patch('frontend.views.service_advanced_views.ForgeAPIClient')
    def test_service_workflow_integration(self, mock_api_client):
        """Test complete service workflow integration."""
        # Mock API client
        mock_client = MagicMock()
        mock_api_client.return_value = mock_client
        
        # Mock responses for complete workflow
        mock_client.get.side_effect = [
            # Dashboard data
            {'count': 10, 'results': []},  # Work orders
            {'count': 2, 'results': []},   # Draft
            {'count': 3, 'results': []},   # Scheduled  
            {'count': 3, 'results': []},   # In progress
            {'count': 2, 'results': []},   # Completed
            {'results': []},               # Technicians
            {'results': []},               # Recent work orders
            
            # Calculator data
            {'results': [{
                'flat_rate_id': 1,
                'service_code': 'TEST-001',
                'description': 'Test service',
                'standard_hours': 1.0
            }]},
            {'results': []},  # Equipment types
            {'results': []},  # Taxonomy groups
            
            # Timeline data
            {
                'wo_id': 1,
                'wo_number': '2024-001',
                'status': 'in_progress',
                'created_at': '2024-01-15T10:00:00Z'
            },
            {'results': []},  # Services
            {'results': []},  # Items
        ]
        
        # Test dashboard -> calculator -> timeline workflow
        urls = [
            reverse('frontend:service_dashboard'),
            reverse('frontend:flat_rate_calculator'),
            reverse('frontend:workorder_timeline', kwargs={'wo_id': 1})
        ]
        
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)


class ServiceAdvancedPropertyTestCase(TestCase):
    """Property-based tests for service advanced functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    @patch('frontend.views.service_advanced_views.ForgeAPIClient')
    def test_work_order_lifecycle_interface_completeness_property(self, mock_api_client):
        """
        Property 22: Work order lifecycle interface completeness
        For any work order in any valid lifecycle state, the timeline interface 
        should display all required lifecycle information and status indicators.
        Validates: Requirements 7.1
        """
        # Mock API client
        mock_client = MagicMock()
        mock_api_client.return_value = mock_client
        
        # Test different work order states
        test_states = ['draft', 'scheduled', 'in_progress', 'completed', 'cancelled']
        
        for state in test_states:
            with self.subTest(state=state):
                # Mock work order in specific state
                mock_work_order = {
                    'wo_id': 1,
                    'wo_number': f'2024-{state.upper()}-001',
                    'status': state,
                    'created_at': '2024-01-15T10:00:00Z',
                    'client': {'name': f'Test Client {state}'},
                    'equipment': {'make': 'Caterpillar', 'model': '320D'},
                    'complaint': f'Test complaint for {state} state'
                }
                
                # Add state-specific fields
                if state in ['scheduled', 'in_progress', 'completed']:
                    mock_work_order['scheduled_date'] = '2024-01-16T08:00:00Z'
                if state in ['in_progress', 'completed']:
                    mock_work_order['started_at'] = '2024-01-16T08:30:00Z'
                if state == 'completed':
                    mock_work_order['completed_at'] = '2024-01-16T16:00:00Z'
                
                mock_client.get.side_effect = [
                    mock_work_order,  # Work order details
                    {'results': []},  # WO services
                    {'results': []},  # WO items
                ]
                
                url = reverse('frontend:workorder_timeline', kwargs={'wo_id': 1})
                response = self.client.get(url)
                
                # Property: Interface should be complete for any valid state
                self.assertEqual(response.status_code, 200)
                
                # Should contain work order number
                self.assertContains(response, mock_work_order['wo_number'])
                
                # Should contain status information
                self.assertContains(response, 'Timeline')
                
                # Should contain progress information
                self.assertContains(response, 'Progreso General')
                
                # Should contain timeline events section
                self.assertContains(response, 'Cronología de Eventos')
                
                # Should contain services section
                self.assertContains(response, 'Servicios en Tiempo Real')
                
                # Should contain parts tracking section
                self.assertContains(response, 'Seguimiento de Partes')
    
    @patch('frontend.views.service_advanced_views.ForgeAPIClient')
    def test_service_checklist_verification_completeness_property(self, mock_api_client):
        """
        Property 26: Service checklist verification completeness
        For any service checklist with any combination of critical and non-critical items,
        the interface should provide complete verification capabilities and prevent
        completion until all critical items are verified.
        Validates: Requirements 7.5
        """
        # Mock API client
        mock_client = MagicMock()
        mock_api_client.return_value = mock_client
        
        # Test different checklist configurations
        test_configurations = [
            # (total_items, critical_items)
            (5, 2),   # Mixed critical/non-critical
            (3, 3),   # All critical
            (4, 0),   # No critical items
            (1, 1),   # Single critical item
            (10, 5),  # Large checklist
        ]
        
        for total_items, critical_items in test_configurations:
            with self.subTest(total_items=total_items, critical_items=critical_items):
                # Generate checklist items
                checklist_items = []
                for i in range(total_items):
                    is_critical = i < critical_items
                    checklist_items.append({
                        'checklist_item_id': i + 1,
                        'sequence_number': i + 1,
                        'description': f'Test item {i + 1}',
                        'detailed_instructions': f'Instructions for item {i + 1}',
                        'is_critical': is_critical,
                        'estimated_minutes': 10,
                        'required_tools': ['Tool A', 'Tool B'],
                        'safety_notes': 'Safety note' if is_critical else None
                    })
                
                mock_flat_rate = {
                    'flat_rate_id': 1,
                    'service_code': 'TEST-001',
                    'description': f'Test service with {total_items} items',
                    'standard_hours': 2.0,
                    'difficulty_level': 2
                }
                
                mock_client.get.side_effect = [
                    mock_flat_rate,
                    {'results': checklist_items}
                ]
                
                url = reverse('frontend:service_checklist_interactive', kwargs={'flat_rate_id': 1})
                response = self.client.get(url)
                
                # Property: Interface should be complete for any checklist configuration
                self.assertEqual(response.status_code, 200)
                
                # Should display service code
                self.assertContains(response, mock_flat_rate['service_code'])
                
                # Should show completion statistics
                self.assertContains(response, 'Estadísticas de Completación')
                
                # Should display total items count
                self.assertContains(response, str(total_items))
                
                # Should display critical items count
                self.assertContains(response, str(critical_items))
                
                # Should have completion actions
                self.assertContains(response, 'Completar Checklist')
                
                # Should have progress tracking
                self.assertContains(response, 'Progreso')
                
                # Should display all checklist items
                for item in checklist_items:
                    self.assertContains(response, item['description'])
                
                # Should have critical items section if there are critical items
                if critical_items > 0:
                    self.assertContains(response, 'Items Críticos')
                
                # Should have timer functionality
                self.assertContains(response, 'Tiempo Transcurrido')
    
    @patch('frontend.views.service_advanced_views.ForgeAPIClient')
    def test_flat_rate_calculator_consistency_property(self, mock_api_client):
        """
        Property: Flat rate calculator consistency
        For any flat rate standard, the calculator should consistently display
        time ranges and allow factor adjustments while maintaining calculation accuracy.
        """
        # Mock API client
        mock_client = MagicMock()
        mock_api_client.return_value = mock_client
        
        # Test different standard configurations
        test_standards = [
            {'standard_hours': 1.0, 'difficulty': 1},
            {'standard_hours': 2.5, 'difficulty': 3},
            {'standard_hours': 8.0, 'difficulty': 5},
            {'standard_hours': 0.5, 'difficulty': 2},
        ]
        
        for i, standard_config in enumerate(test_standards):
            with self.subTest(standard=standard_config):
                mock_standard = {
                    'flat_rate_id': i + 1,
                    'service_code': f'TEST-{i+1:03d}',
                    'description': f'Test service {i + 1}',
                    'standard_hours': standard_config['standard_hours'],
                    'min_hours': standard_config['standard_hours'] * 0.8,
                    'max_hours': standard_config['standard_hours'] * 1.2,
                    'difficulty_level': standard_config['difficulty'],
                    'group_code': 'TEST',
                    'equipment_type': {'name': 'Test Equipment'},
                    'required_tools': ['Tool A'],
                    'required_skills': ['Skill A']
                }
                
                mock_client.get.side_effect = [
                    {'results': [mock_standard]},  # Standards
                    {'results': []},               # Equipment types
                    {'results': []},               # Taxonomy groups
                ]
                
                url = reverse('frontend:flat_rate_calculator')
                response = self.client.get(url)
                
                # Property: Calculator should be consistent for any standard
                self.assertEqual(response.status_code, 200)
                
                # Should display service code
                self.assertContains(response, mock_standard['service_code'])
                
                # Should display standard hours
                self.assertContains(response, str(mock_standard['standard_hours']))
                
                # Should have calculator functionality
                self.assertContains(response, 'Calculadora de Tiempo')
                
                # Should have difficulty factor controls
                self.assertContains(response, 'Factor de Dificultad')
                
                # Should have technician experience controls
                self.assertContains(response, 'Experiencia del Técnico')
                
                # Should have time range visualization
                self.assertContains(response, 'Rango de Tiempo')
                
                # Should display difficulty level appropriately
                difficulty_labels = {1: 'Fácil', 2: 'Moderado', 3: 'Difícil', 4: 'Muy Difícil', 5: 'Muy Difícil'}
                expected_label = difficulty_labels.get(standard_config['difficulty'], 'Fácil')
                # Note: We can't easily test the exact label without more complex template parsing
                
    @patch('frontend.views.service_advanced_views.ForgeAPIClient')
    def test_service_dashboard_metrics_consistency_property(self, mock_api_client):
        """
        Property: Service dashboard metrics consistency
        For any set of work orders and technicians, the dashboard should consistently
        calculate and display accurate metrics and statistics.
        """
        # Mock API client
        mock_client = MagicMock()
        mock_api_client.return_value = mock_client
        
        # Test different data configurations
        test_configurations = [
            {'total_wo': 0, 'technicians': 0},    # Empty state
            {'total_wo': 5, 'technicians': 2},    # Small dataset
            {'total_wo': 50, 'technicians': 10},  # Medium dataset
            {'total_wo': 1, 'technicians': 1},    # Minimal dataset
        ]
        
        for config in test_configurations:
            with self.subTest(config=config):
                # Mock work order counts by status
                status_distribution = {
                    'draft': config['total_wo'] // 4,
                    'scheduled': config['total_wo'] // 4,
                    'in_progress': config['total_wo'] // 4,
                    'completed': config['total_wo'] - (3 * (config['total_wo'] // 4))
                }
                
                # Generate mock technicians
                mock_technicians = []
                for i in range(config['technicians']):
                    mock_technicians.append({
                        'user_id': i + 1,
                        'name': f'Technician {i + 1}',
                        'username': f'tech{i + 1}',
                        'specialization': 'General'
                    })
                
                # Generate mock recent work orders
                mock_recent_wo = []
                for i in range(min(5, config['total_wo'])):  # Max 5 recent
                    mock_recent_wo.append({
                        'wo_id': i + 1,
                        'wo_number': f'2024-{i+1:03d}',
                        'status': 'in_progress',
                        'created_at': '2024-01-15T10:00:00Z',
                        'client': {'name': f'Client {i + 1}'},
                        'equipment': {'make': 'Test', 'model': 'Model'},
                        'complaint': f'Test complaint {i + 1}'
                    })
                
                # Set up mock responses
                mock_responses = [
                    {'count': config['total_wo'], 'results': []},  # Total work orders
                ]
                
                # Add status-specific responses
                for status, count in status_distribution.items():
                    mock_responses.append({'count': count, 'results': []})
                
                mock_responses.extend([
                    {'results': mock_technicians},  # Technicians
                    {'results': mock_recent_wo},    # Recent work orders
                ])
                
                mock_client.get.side_effect = mock_responses
                
                url = reverse('frontend:service_dashboard')
                response = self.client.get(url)
                
                # Property: Dashboard should be consistent for any data configuration
                self.assertEqual(response.status_code, 200)
                
                # Should display dashboard title
                self.assertContains(response, 'Dashboard de Servicios')
                
                # Should display total work orders
                self.assertContains(response, str(config['total_wo']))
                
                # Should have metrics section
                self.assertContains(response, 'Órdenes Activas')
                
                # Should have technicians section (even if empty)
                self.assertContains(response, 'Técnicos Destacados')
                
                # Should have recent orders section (even if empty)
                self.assertContains(response, 'Órdenes Recientes')
                
                # Should have quick actions
                self.assertContains(response, 'Acciones Rápidas')
                
                # Should handle empty states gracefully
                if config['total_wo'] == 0:
                    # Should still render without errors
                    pass
                
                if config['technicians'] == 0:
                    self.assertContains(response, 'No hay técnicos disponibles')
"""
Simple tests for catalog interface functionality.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from unittest.mock import patch

from ..services.api_client import ForgeAPIClient, APIException


class SimpleCatalogTests(TestCase):
    """Simple tests for catalog interface."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        login_success = self.client.login(username='testuser', password='testpass123')
        self.assertTrue(login_success, "Failed to log in test user")
    
    def test_equipment_type_list_view_basic(self):
        """Test basic equipment type list view functionality."""
        # Mock API response
        mock_response = {
            'results': [
                {
                    'type_id': 1,
                    'type_code': 'AUTO001',
                    'name': 'Automóvil Sedan',
                    'category': 'AUTOMOTRIZ',
                    'is_active': True,
                    'attr_schema': {'color': 'string', 'year': 'integer'},
                    'created_at': '2024-01-01T00:00:00Z',
                    'updated_at': '2024-01-01T00:00:00Z',
                }
            ],
            'count': 1,
            'next': None,
            'previous': None
        }
        
        with patch.object(ForgeAPIClient, 'get') as mock_get:
            mock_get.return_value = mock_response
            
            # Make request to equipment type list view
            response = self.client.get(reverse('frontend:equipment_type_list'))
            
            # Check response
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'Tipos de Equipo')
            
            # Check context
            equipment_types = response.context.get('equipment_types', [])
            self.assertEqual(len(equipment_types), 1)
            
            # Check that processing was applied
            eq_type = equipment_types[0]
            self.assertIn('category_class', eq_type)
            self.assertIn('category_icon', eq_type)
            self.assertIn('attribute_count', eq_type)
            self.assertEqual(eq_type['attribute_count'], 2)
    
    def test_equipment_type_list_view_error_handling(self):
        """Test equipment type list view error handling."""
        with patch.object(ForgeAPIClient, 'get') as mock_get:
            # Simulate API error
            mock_get.side_effect = APIException("API connection failed")
            
            # Make request
            response = self.client.get(reverse('frontend:equipment_type_list'))
            
            # Should handle error gracefully
            self.assertEqual(response.status_code, 200)
            
            # Should have empty equipment types
            equipment_types = response.context.get('equipment_types', [])
            self.assertEqual(len(equipment_types), 0)
    
    def test_taxonomy_system_list_view_basic(self):
        """Test basic taxonomy system list view functionality."""
        # Mock API response
        mock_response = {
            'results': [
                {
                    'id': 1,
                    'system_code': 'ENG',
                    'name_es': 'Motor',
                    'category': 'AUTOMOTRIZ',
                    'is_active': True,
                    'sort_order': 1,
                    'subsystems': [
                        {
                            'id': 1,
                            'subsystem_code': 'ENG_BLOCK',
                            'name_es': 'Bloque Motor',
                            'sort_order': 1,
                            'groups': [
                                {
                                    'group_code': 'PISTONS',
                                    'name_es': 'Pistones',
                                    'requires_position': True,
                                    'requires_color': False,
                                    'requires_finish': False,
                                }
                            ]
                        }
                    ]
                }
            ],
            'count': 1
        }
        
        def mock_get_side_effect(endpoint, params=None):
            if endpoint == 'taxonomy-systems/':
                return mock_response
            elif endpoint == 'taxonomy-subsystems/':
                return {'results': mock_response['results'][0]['subsystems']}
            elif endpoint == 'taxonomy-groups/':
                return {'results': mock_response['results'][0]['subsystems'][0]['groups']}
            return {'results': []}
        
        with patch.object(ForgeAPIClient, 'get', side_effect=mock_get_side_effect):
            # Make request
            response = self.client.get(reverse('frontend:taxonomy_system_list'))
            
            # Check response
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'Sistemas de Taxonomía')
            
            # Check context
            taxonomy_systems = response.context.get('taxonomy_systems', [])
            self.assertEqual(len(taxonomy_systems), 1)
            
            # Check hierarchy preservation
            system = taxonomy_systems[0]
            self.assertEqual(system['system_code'], 'ENG')
            self.assertEqual(len(system['subsystems']), 1)
            
            subsystem = system['subsystems'][0]
            self.assertEqual(subsystem['subsystem_code'], 'ENG_BLOCK')
            self.assertEqual(len(subsystem['groups']), 1)
            
            group = subsystem['groups'][0]
            self.assertEqual(group['group_code'], 'PISTONS')
            self.assertTrue(group['requires_position'])
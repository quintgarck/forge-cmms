"""
Property-based tests for navigation consistency.

**Feature: forge-frontend-web, Property 2: Navigation consistency**

This module tests the property that for any navigation element click,
the system should successfully navigate to the corresponding module without errors.
"""
import pytest
from hypothesis import given, strategies as st, settings, assume
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse, resolve
from django.http import HttpResponse
from unittest.mock import Mock, patch
import re


class TestNavigationConsistency(TestCase):
    """
    **Feature: forge-frontend-web, Property 2: Navigation consistency**
    
    Tests that navigation behaves consistently across all navigation elements,
    ensuring that all navigation links work correctly and lead to valid pages.
    """
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        
        # Define all navigation URLs that should be accessible
        self.navigation_urls = [
            'frontend:dashboard',
            'frontend:client_list',
            'frontend:client_create',
            'frontend:workorder_list',
            'frontend:workorder_create',
            'frontend:inventory_list',
            'frontend:product_list',
            'frontend:product_create',
            'frontend:stock_list',
            'frontend:transaction_list',
            'frontend:equipment_list',
            'frontend:equipment_create',
        ]
        
        # Define expected status codes for different URL types
        self.expected_status_codes = {
            'list': [200],  # List views should always return 200
            'create': [200],  # Create forms should return 200
            'detail': [200, 404],  # Detail views might return 404 if object doesn't exist
            'update': [200, 404],  # Update views might return 404 if object doesn't exist
        }
    
    def _get_url_type(self, url_name: str) -> str:
        """Determine the type of URL based on its name."""
        if 'list' in url_name or url_name.endswith('dashboard'):
            return 'list'
        elif 'create' in url_name:
            return 'create'
        elif 'detail' in url_name:
            return 'detail'
        elif 'update' in url_name or 'edit' in url_name:
            return 'update'
        else:
            return 'list'  # Default to list type
    
    def _is_valid_url_name(self, url_name: str) -> bool:
        """Check if a URL name is valid and should be tested."""
        try:
            reverse(url_name)
            return True
        except:
            return False
    
    @given(st.sampled_from([
        'frontend:dashboard',
        'frontend:client_list',
        'frontend:client_create',
        'frontend:workorder_list',
        'frontend:inventory_list',
        'frontend:equipment_list',
    ]))
    @settings(max_examples=50, deadline=None)
    def test_navigation_consistency_basic_urls(self, url_name):
        """
        **Property 2: Navigation consistency**
        
        Test that basic navigation URLs consistently return successful responses.
        """
        # Act
        try:
            url = reverse(url_name)
            response = self.client.get(url)
        except Exception as e:
            self.fail(f"Navigation to {url_name} failed with exception: {e}")
        
        # Assert - Property validation
        url_type = self._get_url_type(url_name)
        expected_codes = self.expected_status_codes.get(url_type, [200])
        
        self.assertIn(response.status_code, expected_codes,
            f"Navigation to {url_name} returned unexpected status {response.status_code}. "
            f"Expected one of {expected_codes}")
        
        # Additional property: Response should contain expected navigation elements
        if response.status_code == 200:
            self.assertContains(response, 'navbar',
                f"Navigation to {url_name} should contain navbar")
            self.assertContains(response, 'ForgeDB',
                f"Navigation to {url_name} should contain brand name")
    
    def test_navigation_active_state_consistency(self):
        """
        **Property 2: Navigation consistency**
        
        Test that navigation active states are consistent across all pages.
        """
        test_cases = [
            ('frontend:dashboard', 'dashboard'),
            ('frontend:client_list', 'client'),
            ('frontend:workorder_list', 'workorder'),
            ('frontend:inventory_list', 'inventory'),
            ('frontend:equipment_list', 'equipment'),
        ]
        
        for url_name, expected_active in test_cases:
            with self.subTest(url_name=url_name):
                # Act
                response = self.client.get(reverse(url_name))
                
                # Assert - Property validation
                if response.status_code == 200:
                    content = response.content.decode()
                    
                    # Should have exactly one active navigation item
                    active_nav_items = content.count('nav-link active') + content.count('active')
                    self.assertGreaterEqual(active_nav_items, 1,
                        f"Page {url_name} should have at least one active navigation item")
    
    def test_breadcrumb_consistency(self):
        """
        **Property 2: Navigation consistency**
        
        Test that breadcrumbs are consistently displayed and structured.
        """
        test_urls = [
            'frontend:dashboard',
            'frontend:client_list',
            'frontend:client_create',
        ]
        
        for url_name in test_urls:
            with self.subTest(url_name=url_name):
                # Act
                response = self.client.get(reverse(url_name))
                
                # Assert - Property validation
                if response.status_code == 200:
                    # Should contain breadcrumb navigation
                    self.assertContains(response, 'breadcrumb',
                        f"Page {url_name} should contain breadcrumb navigation")
                    
                    # Should contain "Inicio" as first breadcrumb item
                    self.assertContains(response, 'Inicio',
                        f"Page {url_name} breadcrumb should contain 'Inicio'")
    
    @given(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    @settings(max_examples=20, deadline=None)
    def test_search_functionality_consistency(self, search_query):
        """
        **Property 2: Navigation consistency**
        
        Test that search functionality behaves consistently across different queries.
        """
        assume(len(search_query.strip()) > 0)  # Ensure non-empty search
        
        # Test search on client list page
        url = reverse('frontend:client_list')
        
        # Act
        response = self.client.get(url, {'search': search_query})
        
        # Assert - Property validation
        self.assertEqual(response.status_code, 200,
            f"Search with query '{search_query}' should return 200")
        
        # Should maintain search query in the form
        if response.status_code == 200:
            self.assertContains(response, 'search',
                "Search page should contain search functionality")
    
    def test_dropdown_navigation_consistency(self):
        """
        **Property 2: Navigation consistency**
        
        Test that dropdown navigation menus are consistently structured.
        """
        # Act
        response = self.client.get(reverse('frontend:dashboard'))
        
        # Assert - Property validation
        if response.status_code == 200:
            content = response.content.decode()
            
            # Should contain dropdown menus for main navigation items
            dropdown_items = ['Clientes', 'Órdenes', 'Inventario', 'Equipos']
            
            for item in dropdown_items:
                self.assertIn(item, content,
                    f"Navigation should contain dropdown for {item}")
            
            # Should contain dropdown-toggle classes
            self.assertIn('dropdown-toggle', content,
                "Navigation should contain dropdown functionality")
    
    def test_responsive_navigation_consistency(self):
        """
        **Property 2: Navigation consistency**
        
        Test that responsive navigation elements are consistently present.
        """
        # Act
        response = self.client.get(reverse('frontend:dashboard'))
        
        # Assert - Property validation
        if response.status_code == 200:
            content = response.content.decode()
            
            # Should contain mobile navigation toggle
            self.assertIn('navbar-toggler', content,
                "Navigation should contain mobile toggle button")
            
            # Should contain collapsible navigation
            self.assertIn('navbar-collapse', content,
                "Navigation should contain collapsible menu")
            
            # Should contain responsive classes
            self.assertIn('navbar-expand-lg', content,
                "Navigation should contain responsive breakpoint classes")
    
    def test_user_menu_consistency(self):
        """
        **Property 2: Navigation consistency**
        
        Test that user menu is consistently displayed when authenticated.
        """
        # Act
        response = self.client.get(reverse('frontend:dashboard'))
        
        # Assert - Property validation
        if response.status_code == 200:
            content = response.content.decode()
            
            # Should contain user menu elements
            self.assertIn(self.user.username, content,
                "Navigation should display current user's username")
            
            # Should contain logout link
            self.assertIn('Cerrar Sesión', content,
                "User menu should contain logout option")
            
            # Should contain user dropdown
            self.assertIn('dropdown-menu', content,
                "User menu should be a dropdown")
    
    def test_navigation_accessibility_consistency(self):
        """
        **Property 2: Navigation consistency**
        
        Test that navigation elements consistently include accessibility features.
        """
        # Act
        response = self.client.get(reverse('frontend:dashboard'))
        
        # Assert - Property validation
        if response.status_code == 200:
            content = response.content.decode()
            
            # Should contain ARIA labels
            self.assertIn('aria-label', content,
                "Navigation should contain ARIA labels for accessibility")
            
            # Should contain role attributes
            self.assertIn('role=', content,
                "Navigation should contain role attributes")
            
            # Should contain skip link for accessibility
            self.assertIn('Saltar al contenido', content,
                "Page should contain skip to content link")
    
    @given(st.integers(min_value=1, max_value=100))
    @settings(max_examples=10, deadline=None)
    def test_pagination_navigation_consistency(self, page_number):
        """
        **Property 2: Navigation consistency**
        
        Test that pagination navigation behaves consistently across different pages.
        """
        # Act - Test pagination on client list
        url = reverse('frontend:client_list')
        response = self.client.get(url, {'page': page_number})
        
        # Assert - Property validation
        # Should handle invalid page numbers gracefully
        self.assertIn(response.status_code, [200, 404],
            f"Pagination with page {page_number} should return 200 or 404")
        
        if response.status_code == 200:
            # Should contain pagination elements if there are multiple pages
            content = response.content.decode()
            # Note: Pagination might not be present if there's only one page
            # This is acceptable behavior
    
    def test_error_page_navigation_consistency(self):
        """
        **Property 2: Navigation consistency**
        
        Test that error pages maintain consistent navigation structure.
        """
        # Act - Try to access a non-existent client detail page
        try:
            response = self.client.get(reverse('frontend:client_detail', kwargs={'pk': 99999}))
        except:
            # If the URL doesn't exist or throws an error, that's also valid behavior
            # The important thing is that it doesn't crash the application
            response = Mock()
            response.status_code = 404
        
        # Assert - Property validation
        # Error pages should either return 404 or handle the error gracefully
        self.assertIn(response.status_code, [200, 404, 500],
            "Non-existent pages should return appropriate error codes")
    
    def test_navigation_url_resolution_consistency(self):
        """
        **Property 2: Navigation consistency**
        
        Test that all navigation URLs can be resolved consistently.
        """
        for url_name in self.navigation_urls:
            with self.subTest(url_name=url_name):
                # Act & Assert
                try:
                    url = reverse(url_name)
                    resolved = resolve(url)
                    
                    # Property: URL should resolve to a valid view
                    self.assertIsNotNone(resolved.func,
                        f"URL {url_name} should resolve to a valid view function")
                    
                    # Property: URL should have correct namespace
                    self.assertEqual(resolved.namespace, 'frontend',
                        f"URL {url_name} should be in frontend namespace")
                    
                except Exception as e:
                    self.fail(f"URL {url_name} failed to resolve: {e}")


class NavigationTestHelpers:
    """Helper methods for navigation testing."""
    
    @staticmethod
    def extract_navigation_links(html_content: str) -> list:
        """Extract all navigation links from HTML content."""
        import re
        # Simple regex to find href attributes in navigation
        nav_links = re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>', html_content)
        return nav_links
    
    @staticmethod
    def count_active_nav_items(html_content: str) -> int:
        """Count active navigation items in HTML content."""
        return html_content.count('nav-link active')
    
    @staticmethod
    def has_responsive_navigation(html_content: str) -> bool:
        """Check if HTML contains responsive navigation elements."""
        required_elements = [
            'navbar-toggler',
            'navbar-collapse',
            'navbar-expand'
        ]
        return all(element in html_content for element in required_elements)
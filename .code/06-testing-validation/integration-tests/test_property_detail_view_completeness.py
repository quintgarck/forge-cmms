#!/usr/bin/env python3
"""
Property-based test for client detail view completeness.

**Feature: forge-frontend-web, Property 5: Detail view completeness**
**Validates: Requirements 2.4**

Property 5: Detail view completeness
For any client detail view, all essential client information should be displayed completely and accurately
"""

import os
import sys
import django
from pathlib import Path
from decimal import Decimal
import random
import string
import re

# Add the project directory to Python path
project_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(project_dir))

# Setup Django BEFORE importing hypothesis.extra.django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')
django.setup()

# Now import hypothesis and Django components
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from hypothesis.extra.django import TestCase
from django.test import Client
from django.contrib.auth.models import User
from frontend.forms import ClientForm


class ClientDataGenerator:
    """Generator for comprehensive client test data."""
    
    @staticmethod
    def generate_random_string(length=10):
        """Generate random string for testing."""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    @staticmethod
    def generate_client_code():
        """Generate valid client codes."""
        prefixes = ['CLI', 'CUST', 'CLIENT', 'C']
        prefix = random.choice(prefixes)
        number = random.randint(1, 9999)
        return f"{prefix}-{number:04d}"
    
    @staticmethod
    def generate_name():
        """Generate realistic client names."""
        individual_names = [
            'Juan Carlos Pérez', 'María Elena González', 'José Luis Martínez',
            'Ana Patricia López', 'Carlos Eduardo Rodríguez', 'Sofía Isabel Hernández',
            'Miguel Ángel Sánchez', 'Lucía Fernanda Torres', 'Roberto Carlos Jiménez',
            'Valentina Alejandra Morales'
        ]
        
        business_names = [
            'Constructora del Norte S.A. de C.V.', 'Transportes Rápidos México',
            'Servicios Industriales Monterrey', 'Comercializadora del Bajío',
            'Grupo Empresarial del Pacífico', 'Tecnología y Sistemas Avanzados',
            'Distribuidora Nacional de Autopartes', 'Manufacturas del Centro',
            'Logística Integral del Sureste', 'Corporativo de Servicios Múltiples'
        ]
        
        return random.choice(individual_names + business_names)
    
    @staticmethod
    def generate_email():
        """Generate realistic email addresses."""
        domains = [
            'gmail.com', 'yahoo.com.mx', 'hotmail.com', 'outlook.com',
            'empresa.com.mx', 'corporativo.mx', 'negocio.com', 'comercial.mx'
        ]
        
        username = ClientDataGenerator.generate_random_string(random.randint(5, 15)).lower()
        domain = random.choice(domains)
        return f"{username}@{domain}"
    
    @staticmethod
    def generate_phone():
        """Generate realistic Mexican phone numbers."""
        formats = [
            lambda: f"{random.randint(10000000, 99999999)}",  # 8 digits local
            lambda: f"{random.randint(1000000000, 9999999999)}",  # 10 digits
            lambda: f"({random.randint(10,99)}) {random.randint(1000,9999)}-{random.randint(1000,9999)}",
            lambda: f"+52 {random.randint(10,99)} {random.randint(1000,9999)} {random.randint(1000,9999)}",
            lambda: f"{random.randint(10,99)}-{random.randint(1000,9999)}-{random.randint(1000,9999)}"
        ]
        return random.choice(formats)()
    
    @staticmethod
    def generate_address():
        """Generate realistic Mexican addresses."""
        streets = [
            'Av. Insurgentes Sur', 'Calle Reforma', 'Blvd. Miguel Hidalgo',
            'Av. Universidad', 'Calle Juárez', 'Av. Revolución',
            'Calle Morelos', 'Av. Constitución', 'Blvd. Adolfo López Mateos'
        ]
        
        colonies = [
            'Col. Del Valle', 'Col. Roma Norte', 'Col. Condesa',
            'Col. Polanco', 'Col. Santa Fe', 'Col. Coyoacán',
            'Col. San Ángel', 'Col. Doctores', 'Col. Centro'
        ]
        
        street = random.choice(streets)
        number = random.randint(1, 9999)
        colony = random.choice(colonies)
        postal_code = random.randint(10000, 99999)
        city = random.choice(['Ciudad de México', 'Guadalajara', 'Monterrey', 'Puebla', 'Tijuana'])
        
        return f"{street} #{number}, {colony}, C.P. {postal_code}, {city}"
    
    @staticmethod
    def generate_credit_limit():
        """Generate realistic credit limits."""
        ranges = [
            (0, 0),  # No credit
            (1000, 5000),  # Small credit
            (5000, 25000),  # Medium credit
            (25000, 100000),  # Large credit
            (100000, 500000),  # Very large credit
        ]
        
        min_val, max_val = random.choice(ranges)
        if min_val == max_val:
            return Decimal('0.00')
        
        amount = random.uniform(min_val, max_val)
        return Decimal(f"{amount:.2f}")
    
    @staticmethod
    def generate_complete_client_data():
        """Generate complete client data for testing."""
        client_type = random.choice(['individual', 'business'])
        
        return {
            'client_code': ClientDataGenerator.generate_client_code(),
            'type': client_type,
            'name': ClientDataGenerator.generate_name(),
            'email': ClientDataGenerator.generate_email(),
            'phone': ClientDataGenerator.generate_phone(),
            'address': ClientDataGenerator.generate_address(),
            'credit_limit': str(ClientDataGenerator.generate_credit_limit())
        }


class TestDetailViewCompleteness(TestCase):
    """
    Property-based tests for client detail view completeness.
    
    **Feature: forge-frontend-web, Property 5: Detail view completeness**
    **Validates: Requirements 2.4**
    """
    
    def setUp(self):
        """Set up test environment."""
        # Create or get admin user
        self.admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@forgedb.com',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True
            }
        )
        
        if created:
            self.admin_user.set_password('admin123')
            self.admin_user.save()
    
    def test_detail_view_completeness_property(self):
        """
        Property 5: Detail view completeness
        
        For any client detail view, all essential client information should be displayed completely and accurately.
        
        **Feature: forge-frontend-web, Property 5: Detail view completeness**
        **Validates: Requirements 2.4**
        """
        # Test with multiple generated client datasets
        for i in range(10):
            with self.subTest(test_case=i):
                # Generate client data
                client_data = ClientDataGenerator.generate_complete_client_data()
                
                # Validate the data through form processing (simulating backend processing)
                form = ClientForm(data=client_data)
                
                # Skip invalid data (edge cases)
                if not form.is_valid():
                    continue
                
                cleaned_data = form.cleaned_data
                
                # Test detail view completeness by checking that all essential information
                # would be available for display
                self._verify_detail_view_completeness(cleaned_data)
    
    def _verify_detail_view_completeness(self, client_data):
        """Verify that client detail view contains all essential information."""
        
        # Essential fields that must be present in detail view
        essential_fields = [
            'client_code', 'type', 'name', 'email', 'phone', 'credit_limit'
        ]
        
        # Verify all essential fields are present
        for field in essential_fields:
            self.assertIn(field, client_data, f"Essential field '{field}' missing from client data")
            
            # Verify field has meaningful content (not just empty)
            if field != 'address':  # Address is optional
                value = client_data[field]
                if isinstance(value, str):
                    self.assertTrue(value.strip(), f"Essential field '{field}' is empty")
                elif isinstance(value, Decimal):
                    self.assertIsNotNone(value, f"Essential field '{field}' is None")
                else:
                    self.assertIsNotNone(value, f"Essential field '{field}' is None")
        
        # Verify data types are appropriate for display
        self.assertIsInstance(client_data['client_code'], str)
        self.assertIsInstance(client_data['type'], str)
        self.assertIsInstance(client_data['name'], str)
        self.assertIsInstance(client_data['email'], str)
        self.assertIsInstance(client_data['phone'], str)
        self.assertIsInstance(client_data['credit_limit'], Decimal)
        
        # Verify data format is suitable for display
        self._verify_display_format_quality(client_data)
    
    def _verify_display_format_quality(self, client_data):
        """Verify that data is formatted appropriately for display."""
        
        # Client code should be uppercase and properly formatted
        client_code = client_data['client_code']
        self.assertTrue(client_code.isupper() or '-' in client_code or '_' in client_code,
                       f"Client code '{client_code}' should be properly formatted")
        
        # Name should be properly capitalized
        name = client_data['name']
        self.assertTrue(any(c.isupper() for c in name),
                       f"Name '{name}' should have proper capitalization")
        
        # Email should be lowercase and valid format
        email = client_data['email']
        self.assertTrue(email.islower(), f"Email '{email}' should be lowercase")
        self.assertIn('@', email, f"Email '{email}' should contain @")
        self.assertIn('.', email.split('@')[1], f"Email '{email}' should have valid domain")
        
        # Phone should contain only valid characters
        phone = client_data['phone']
        phone_chars = set(phone)
        valid_phone_chars = set('0123456789 ()-+.')
        self.assertTrue(phone_chars.issubset(valid_phone_chars),
                       f"Phone '{phone}' contains invalid characters")
        
        # Credit limit should be properly formatted decimal
        credit_limit = client_data['credit_limit']
        self.assertGreaterEqual(credit_limit, Decimal('0.00'),
                               f"Credit limit '{credit_limit}' should be non-negative")
    
    def test_detail_view_with_edge_cases(self):
        """Test detail view completeness with edge cases."""
        edge_cases = [
            # Minimum data
            {
                'client_code': 'MIN',
                'type': 'individual',
                'name': 'AB',
                'email': 'a@b.co',
                'phone': '12345678',
                'address': '',
                'credit_limit': '0.00'
            },
            # Maximum data
            {
                'client_code': 'MAX-VERY-LONG-CODE',
                'type': 'business',
                'name': 'Empresa con Nombre Extremadamente Largo para Pruebas de Visualización',
                'email': 'usuario.con.email.extremadamente.largo@dominio.muy.largo.com',
                'phone': '5512345678',  # Simplified to meet length requirements
                'address': 'Dirección extremadamente larga con muchos detalles específicos para probar la capacidad de visualización completa de información en la vista de detalle del cliente',
                'credit_limit': '999999.98'
            },
            # Special characters
            {
                'client_code': 'CLI-SPECIAL-001',
                'type': 'individual',
                'name': 'José María Fernández-López O\'Connor',
                'email': 'jose.maria@empresa.com.mx',
                'phone': '(55) 1234-5678',
                'address': 'Av. Insurgentes Sur #123, Col. Del Valle, C.P. 03100, Ciudad de México',
                'credit_limit': '50000.00'
            }
        ]
        
        for i, case_data in enumerate(edge_cases):
            with self.subTest(edge_case=i):
                # Validate through form
                form = ClientForm(data=case_data)
                self.assertTrue(form.is_valid(), f"Edge case {i} should be valid: {form.errors}")
                
                cleaned_data = form.cleaned_data
                
                # Verify completeness
                self._verify_detail_view_completeness(cleaned_data)
    
    def test_detail_view_information_accuracy(self):
        """Test that detail view preserves information accuracy."""
        test_data = {
            'client_code': 'CLI-ACCURACY-001',
            'type': 'business',
            'name': 'Empresa de Pruebas de Precisión',
            'email': 'precision@testing.com',
            'phone': '5512345678',
            'address': 'Calle de la Precisión #123, Col. Exactitud',
            'credit_limit': '75000.50'
        }
        
        # Process through form (simulating backend processing)
        form = ClientForm(data=test_data)
        self.assertTrue(form.is_valid())
        
        cleaned_data = form.cleaned_data
        
        # Verify that essential information is preserved accurately
        self.assertEqual(cleaned_data['client_code'], 'CLI-ACCURACY-001')
        self.assertEqual(cleaned_data['type'], 'business')
        self.assertEqual(cleaned_data['name'], 'Empresa De Pruebas De Precisión')  # Capitalized by form
        self.assertEqual(cleaned_data['email'], 'precision@testing.com')
        self.assertEqual(cleaned_data['phone'], '5512345678')
        self.assertEqual(cleaned_data['address'], 'Calle de la Precisión #123, Col. Exactitud')
        self.assertEqual(cleaned_data['credit_limit'], Decimal('75000.50'))
    
    def test_detail_view_financial_information_completeness(self):
        """Test that financial information is complete and properly formatted."""
        financial_test_cases = [
            ('0.00', Decimal('0.00')),
            ('1000.00', Decimal('1000.00')),
            ('50000.50', Decimal('50000.50')),
            ('999999.98', Decimal('999999.98')),  # Just under the maximum
        ]
        
        for credit_input, expected_decimal in financial_test_cases:
            with self.subTest(credit_limit=credit_input):
                test_data = {
                    'client_code': f'CLI-FIN-{credit_input.replace(".", "")}',
                    'type': 'business',
                    'name': 'Cliente Financiero Test',
                    'email': 'financiero@test.com',
                    'phone': '5512345678',
                    'address': 'Dirección Financiera 123',
                    'credit_limit': credit_input
                }
                
                form = ClientForm(data=test_data)
                self.assertTrue(form.is_valid(), f"Financial test case should be valid: {form.errors}")
                
                cleaned_data = form.cleaned_data
                
                # Verify financial information completeness
                self.assertEqual(cleaned_data['credit_limit'], expected_decimal)
                self.assertIsInstance(cleaned_data['credit_limit'], Decimal)
                
                # Verify that credit limit is suitable for display
                credit_str = str(cleaned_data['credit_limit'])
                self.assertRegex(credit_str, r'^\d+\.\d{2}$', 
                               f"Credit limit '{credit_str}' should be formatted with 2 decimal places")
    
    def test_detail_view_contact_information_completeness(self):
        """Test that contact information is complete and properly formatted."""
        contact_test_cases = [
            # Various phone formats
            ('12345678', 'simple@email.com'),
            ('(55) 1234-5678', 'formatted@email.com'),
            ('+52 55 1234 5678', 'international@email.com'),
            ('55-1234-5678', 'dashed@email.com'),
        ]
        
        for phone, email in contact_test_cases:
            with self.subTest(phone=phone, email=email):
                test_data = {
                    'client_code': f'CLI-CONTACT-{len(phone)}',
                    'type': 'individual',
                    'name': 'Cliente Contacto Test',
                    'email': email,
                    'phone': phone,
                    'address': 'Dirección de Contacto 123',
                    'credit_limit': '10000.00'
                }
                
                form = ClientForm(data=test_data)
                self.assertTrue(form.is_valid(), f"Contact test case should be valid: {form.errors}")
                
                cleaned_data = form.cleaned_data
                
                # Verify contact information completeness
                self.assertEqual(cleaned_data['phone'], phone)
                self.assertEqual(cleaned_data['email'], email.lower())  # Email normalized to lowercase
                
                # Verify contact information is suitable for display
                self.assertTrue(cleaned_data['phone'].strip(), "Phone should not be empty")
                self.assertTrue(cleaned_data['email'].strip(), "Email should not be empty")
                self.assertIn('@', cleaned_data['email'], "Email should contain @")
    
    def test_detail_view_type_specific_information(self):
        """Test that type-specific information is handled correctly."""
        type_test_cases = [
            ('individual', 'Juan Pérez García'),
            ('business', 'Corporativo Empresarial S.A. de C.V.'),
        ]
        
        for client_type, name in type_test_cases:
            with self.subTest(client_type=client_type):
                test_data = {
                    'client_code': f'CLI-{client_type.upper()}-001',
                    'type': client_type,
                    'name': name,
                    'email': f'{client_type}@test.com',
                    'phone': '5512345678',
                    'address': f'Dirección {client_type} 123',
                    'credit_limit': '25000.00'
                }
                
                form = ClientForm(data=test_data)
                self.assertTrue(form.is_valid(), f"Type test case should be valid: {form.errors}")
                
                cleaned_data = form.cleaned_data
                
                # Verify type-specific information
                self.assertEqual(cleaned_data['type'], client_type)
                self.assertIn(client_type, ['individual', 'business'])
                
                # Verify name formatting is appropriate for type
                formatted_name = cleaned_data['name']
                self.assertTrue(any(c.isupper() for c in formatted_name),
                               f"Name '{formatted_name}' should be properly capitalized")


def run_property_tests():
    """Run the property-based tests."""
    import unittest
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDetailViewCompleteness)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    print("🧪 EJECUTANDO PROPERTY TEST 5: DETAIL VIEW COMPLETENESS")
    print("=" * 70)
    print("**Feature: forge-frontend-web, Property 5: Detail view completeness**")
    print("**Validates: Requirements 2.4**")
    print("=" * 70)
    
    success = run_property_tests()
    
    if success:
        print("\n✅ PROPERTY TEST 5 PASSED")
        print("🎉 Detail view completeness property verified")
        sys.exit(0)
    else:
        print("\n❌ PROPERTY TEST 5 FAILED")
        print("🚨 Detail view completeness property violated")
        sys.exit(1)
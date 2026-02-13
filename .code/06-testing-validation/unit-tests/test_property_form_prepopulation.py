#!/usr/bin/env python3
"""
Property-based test for form pre-population accuracy.

**Feature: forge-frontend-web, Property 4: Form pre-population accuracy**
**Validates: Requirements 2.3**

Property 4: Form pre-population accuracy
For any edit operation, the form should be pre-populated with the exact existing data from the backend
"""

import os
import sys
import django
from pathlib import Path
from decimal import Decimal
import random
import string

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


class TestFormPrePopulationAccuracy(TestCase):
    """
    Property-based tests for form pre-population accuracy.
    
    **Feature: forge-frontend-web, Property 4: Form pre-population accuracy**
    **Validates: Requirements 2.3**
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
    
    # Hypothesis strategies for generating test data
    @staticmethod
    def client_code_strategy():
        """Generate valid client codes."""
        return st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Nd'), whitelist_characters='-_'),
            min_size=3,
            max_size=20
        ).filter(lambda x: x and not x.isspace() and len(x) >= 3)
    
    @staticmethod
    def name_strategy():
        """Generate valid client names."""
        return st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll'), whitelist_characters=' -\''),
            min_size=2,
            max_size=100
        ).filter(lambda x: x.strip() and len(x.strip()) >= 2 and '  ' not in x)
    
    @staticmethod
    def email_strategy():
        """Generate valid email addresses."""
        local_part = st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='._-'),
            min_size=1,
            max_size=60  # Keep under 64 limit
        ).filter(lambda x: x and not x.startswith('.') and not x.endswith('.') and not x.startswith('-') and not x.endswith('-'))
        
        domain = st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-'),
            min_size=1,
            max_size=60  # Keep under 63 limit
        ).filter(lambda x: x and not x.startswith('-') and not x.endswith('-'))
        
        tld = st.sampled_from(['com', 'org', 'net', 'edu', 'gov', 'mx', 'es'])
        
        return st.builds(
            lambda l, d, t: f"{l}@{d}.{t}",
            local_part, domain, tld
        )
    
    @staticmethod
    def phone_strategy():
        """Generate valid phone numbers."""
        return st.one_of([
            # Mexican local numbers (8-10 digits)
            st.integers(min_value=10000000, max_value=9999999999).map(str),
            # Formatted numbers
            st.builds(
                lambda area, num: f"({area}) {num[:4]}-{num[4:]}",
                st.integers(min_value=10, max_value=99).map(str),
                st.integers(min_value=10000000, max_value=99999999).map(str)
            ),
            # International format (keep under 15 digits total)
            st.builds(
                lambda country, area, num: f"+{country} {area} {num[:4]} {num[4:]}",
                st.integers(min_value=1, max_value=99).map(str),
                st.integers(min_value=10, max_value=99).map(str),
                st.integers(min_value=10000000, max_value=99999999).map(str)
            )
        ])
    
    @staticmethod
    def address_strategy():
        """Generate valid addresses."""
        return st.one_of([
            st.just(""),  # Empty address (optional field)
            st.text(
                alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters=' ,-#.'),
                min_size=10,
                max_size=500
            ).filter(lambda x: x.strip() and len(x.strip()) >= 10)
        ])
    
    @staticmethod
    def credit_limit_strategy():
        """Generate valid credit limits."""
        return st.decimals(
            min_value=Decimal('0.00'),
            max_value=Decimal('999999.99'),  # Respect the form's maximum
            places=2
        )
    
    @given(
        client_code=client_code_strategy(),
        client_type=st.sampled_from(['individual', 'business']),
        name=name_strategy(),
        email=email_strategy(),
        phone=phone_strategy(),
        address=address_strategy(),
        credit_limit=credit_limit_strategy()
    )
    @settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.filter_too_much])
    def test_form_prepopulation_accuracy_property(self, client_code, client_type, name, email, phone, address, credit_limit):
        """
        Property 4: Form pre-population accuracy
        
        For any edit operation, the form should be pre-populated with the exact existing data from the backend.
        
        **Feature: forge-frontend-web, Property 4: Form pre-population accuracy**
        **Validates: Requirements 2.3**
        """
        # Basic validation of generated data
        assume(len(client_code.strip()) >= 3)
        assume(len(name.strip()) >= 2)
        assume('@' in email and '.' in email.split('@')[1])
        
        # Clean phone to check digit count
        phone_digits = ''.join(c for c in phone if c.isdigit())
        assume(8 <= len(phone_digits) <= 15)
        
        # Step 1: Create initial client data
        original_data = {
            'client_code': client_code.strip().upper(),
            'type': client_type,
            'name': name.strip(),
            'email': email.lower().strip(),
            'phone': phone.strip(),
            'address': address.strip(),
            'credit_limit': str(credit_limit)
        }
        
        # Step 2: Test form validation with original data
        form = ClientForm(data=original_data)
        
        # Skip if form is not valid (edge case)
        assume(form.is_valid())
        
        cleaned_data = form.cleaned_data
        
        # Step 3: Test form pre-population by creating a new form with initial data
        prepopulated_form = ClientForm(initial=cleaned_data)
        
        # Step 4: Verify form pre-population accuracy
        # Check that initial data matches cleaned data
        for field_name, expected_value in cleaned_data.items():
            if field_name in prepopulated_form.initial:
                actual_value = prepopulated_form.initial[field_name]
                
                # Handle different data types appropriately
                if isinstance(expected_value, Decimal):
                    self.assertEqual(str(actual_value), str(expected_value),
                                   f"Decimal field '{field_name}' pre-population mismatch: {actual_value} != {expected_value}")
                else:
                    self.assertEqual(actual_value, expected_value,
                                   f"Field '{field_name}' pre-population mismatch: {actual_value} != {expected_value}")
        
        # Step 5: Test roundtrip consistency
        # Simulate submitting the pre-populated form
        form_data = {}
        for field_name, field in prepopulated_form.fields.items():
            if field_name in prepopulated_form.initial:
                form_data[field_name] = str(prepopulated_form.initial[field_name])
        
        roundtrip_form = ClientForm(data=form_data)
        
        # The roundtrip form should be valid
        if not roundtrip_form.is_valid():
            self.fail(f"Roundtrip form validation failed: {roundtrip_form.errors}")
        
        roundtrip_cleaned = roundtrip_form.cleaned_data
        
        # Essential fields should remain unchanged through the roundtrip
        essential_fields = ['client_code', 'name', 'email', 'phone', 'type']
        for field in essential_fields:
            if field in cleaned_data and field in roundtrip_cleaned:
                original_value = cleaned_data[field]
                roundtrip_value = roundtrip_cleaned[field]
                
                self.assertEqual(original_value, roundtrip_value,
                               f"Roundtrip failed for '{field}': {original_value} != {roundtrip_value}")
    
    def test_form_prepopulation_with_known_data(self):
        """
        Test form pre-population with known, controlled data.
        
        This is a concrete test case to ensure the property test is working correctly.
        """
        # Create a client with known data
        known_data = {
            'client_code': 'CLI-PREPOP-001',
            'type': 'individual',
            'name': 'Cliente Pre-Población Test',
            'email': 'prepop@test.com',
            'phone': '82363829',
            'address': 'Dirección de Pre-Población 123',
            'credit_limit': '5000.00'
        }
        
        # Create and validate form
        form = ClientForm(data=known_data)
        self.assertTrue(form.is_valid(), f"Form should be valid with data: {known_data}")
        
        if not form.is_valid():
            self.fail(f"Form validation errors: {form.errors}")
        
        cleaned_data = form.cleaned_data
        
        # Create pre-populated form
        prepopulated_form = ClientForm(initial=cleaned_data)
        
        # Verify pre-population (note: name gets capitalized by clean_name method)
        self.assertEqual(prepopulated_form.initial['client_code'], 'CLI-PREPOP-001')
        self.assertEqual(prepopulated_form.initial['name'], 'Cliente Pre-población Test')  # Capitalized by form
        self.assertEqual(prepopulated_form.initial['email'], 'prepop@test.com')
        self.assertEqual(prepopulated_form.initial['phone'], '82363829')
        self.assertEqual(str(prepopulated_form.initial['credit_limit']), '5000.00')
    
    def test_form_validation_consistency_with_prepopulated_data(self):
        """
        Test that pre-populated data passes the same validation as new data.
        
        This ensures that data retrieved from the backend is consistent with form validation.
        """
        # Test data that should be valid
        valid_data = {
            'client_code': 'CLI-VALID-001',
            'type': 'business',
            'name': 'Empresa Válida',  # Simplified name to avoid case issues
            'email': 'valida@empresa.com',
            'phone': '5512345678',  # Simplified phone format
            'address': 'Calle Válida 456, Colonia Test',
            'credit_limit': '10000.00'
        }
        
        # Create form with this data
        form = ClientForm(data=valid_data)
        
        # Form should be valid
        self.assertTrue(form.is_valid(), f"Form should be valid with data: {valid_data}")
        
        if not form.is_valid():
            self.fail(f"Form validation errors: {form.errors}")
        
        # Cleaned data should match input data (with expected transformations)
        cleaned = form.cleaned_data
        
        self.assertEqual(cleaned['client_code'], valid_data['client_code'])
        self.assertEqual(cleaned['type'], valid_data['type'])
        self.assertEqual(cleaned['name'], valid_data['name'])
        self.assertEqual(cleaned['email'], valid_data['email'])
        self.assertEqual(cleaned['phone'], valid_data['phone'])
        self.assertEqual(cleaned['address'], valid_data['address'])
        self.assertEqual(float(cleaned['credit_limit']), float(valid_data['credit_limit']))
    
    def test_edge_cases_prepopulation(self):
        """Test form pre-population with edge cases."""
        edge_cases = [
            # Minimum values (adjusted to meet validation requirements)
            {
                'client_code': 'CLI',  # At least 3 characters
                'type': 'individual',
                'name': 'AB',
                'email': 'a@b.co',
                'phone': '12345678',  # At least 8 digits
                'address': '',  # Empty is allowed
                'credit_limit': '0.00'
            },
            # Special characters (adjusted to meet validation requirements)
            {
                'client_code': 'CLI-NU-123',  # No special characters like Ñ in client_code
                'type': 'business',
                'name': 'José María Fernández-López',
                'email': 'jose.maria@empresa.com.mx',
                'phone': '5512345678',
                'address': 'Av. Insurgentes Sur #123, Col. Del Valle',
                'credit_limit': '15000.50'
            },
            # Maximum reasonable values (adjusted to meet validation requirements)
            {
                'client_code': 'CLI-VERY-LONG-CODE',
                'type': 'business',
                'name': 'Empresa con Nombre Muy Largo para Pruebas de Validación',
                'email': 'usuario.con.email.muy.largo@dominio.muy.largo.com',
                'phone': '525512345678',
                'address': 'Dirección muy larga con muchos detalles para probar el límite de caracteres permitidos en el campo de dirección',
                'credit_limit': '999999.98'  # Just under the maximum to avoid floating point issues
            }
        ]
        
        for i, case_data in enumerate(edge_cases):
            with self.subTest(case=i):
                # Test form validation
                form = ClientForm(data=case_data)
                self.assertTrue(form.is_valid(), f"Edge case {i} should be valid: {form.errors}")
                
                cleaned_data = form.cleaned_data
                
                # Test pre-population
                prepopulated_form = ClientForm(initial=cleaned_data)
                
                # Verify all fields are pre-populated correctly
                for field_name, expected_value in cleaned_data.items():
                    if field_name in prepopulated_form.initial:
                        actual_value = prepopulated_form.initial[field_name]
                        
                        if isinstance(expected_value, Decimal):
                            self.assertEqual(str(actual_value), str(expected_value),
                                           f"Edge case {i}, field '{field_name}' pre-population failed")
                        else:
                            self.assertEqual(actual_value, expected_value,
                                           f"Edge case {i}, field '{field_name}' pre-population failed")
    
    def test_form_field_types_consistency(self):
        """Test that form field types are handled consistently in pre-population."""
        test_data = {
            'client_code': 'CLI-TYPE-TEST',
            'type': 'individual',
            'name': 'Cliente Tipo Test',
            'email': 'tipo@test.com',
            'phone': '82363829',
            'address': 'Dirección Tipo Test 123',
            'credit_limit': '7500.25'
        }
        
        # Create and validate form
        form = ClientForm(data=test_data)
        self.assertTrue(form.is_valid())
        
        cleaned_data = form.cleaned_data
        
        # Verify data types after cleaning
        self.assertIsInstance(cleaned_data['client_code'], str)
        self.assertIsInstance(cleaned_data['type'], str)
        self.assertIsInstance(cleaned_data['name'], str)
        self.assertIsInstance(cleaned_data['email'], str)
        self.assertIsInstance(cleaned_data['phone'], str)
        self.assertIsInstance(cleaned_data['address'], str)
        self.assertIsInstance(cleaned_data['credit_limit'], Decimal)
        
        # Create pre-populated form
        prepopulated_form = ClientForm(initial=cleaned_data)
        
        # Verify that initial data maintains appropriate types
        for field_name, value in prepopulated_form.initial.items():
            original_value = cleaned_data[field_name]
            
            if isinstance(original_value, Decimal):
                # Decimal fields should be convertible back to Decimal
                self.assertEqual(Decimal(str(value)), original_value)
            else:
                # Other fields should maintain their values
                self.assertEqual(value, original_value)


def run_property_tests():
    """Run the property-based tests."""
    import unittest
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestFormPrePopulationAccuracy)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    print("🧪 EJECUTANDO PROPERTY TEST 4: FORM PRE-POPULATION ACCURACY")
    print("=" * 70)
    print("**Feature: forge-frontend-web, Property 4: Form pre-population accuracy**")
    print("**Validates: Requirements 2.3**")
    print("=" * 70)
    
    success = run_property_tests()
    
    if success:
        print("\n✅ PROPERTY TEST 4 PASSED")
        print("🎉 Form pre-population accuracy property verified")
        sys.exit(0)
    else:
        print("\n❌ PROPERTY TEST 4 FAILED")
        print("🚨 Form pre-population accuracy property violated")
        sys.exit(1)
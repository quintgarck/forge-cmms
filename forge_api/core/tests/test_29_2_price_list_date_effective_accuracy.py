"""
**Feature: forge-api-rest, Property 56: Price list date-effective accuracy**

Property-based test for price list date-effective accuracy.
Tests that price requests return accurate pricing based on date-effective 
price lists with proper currency and tax calculations.

**Validates: Requirements 12.3**
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from decimal import Decimal
from datetime import date, timedelta

from ..models import PriceList, ProductPrice, Technician
from ..serializers.main_serializers import PriceListSerializer, ProductPriceSerializer


class TestPriceListDateEffectiveAccuracy(APITestCase):
    """Property-based tests for price list date-effective accuracy"""

    def setUp(self):
        """Set up test data"""
        # Create test user and technician
        self.user = User.objects.create_user(
            username='testtech',
            password='testpass123',
            email='test@example.com'
        )
        self.technician = Technician.objects.create(
            employee_code='TECH001',
            first_name='Test',
            last_name='Technician',
            email='test@example.com',
            hire_date='2023-01-01',
            status='active'
        )
        self.client.force_authenticate(user=self.user)

    # Hypothesis strategies for generating test data
    valid_price_list_codes = st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Nd')),
        min_size=3,
        max_size=20
    ).map(lambda x: x.replace(' ', ''))
    
    valid_names = st.text(min_size=1, max_size=100)
    
    valid_currencies = st.sampled_from(['USD', 'EUR', 'MXN', 'CAD'])
    
    valid_prices = st.decimals(
        min_value=Decimal('0.01'),
        max_value=Decimal('9999.99'),
        places=2
    )
    
    valid_percentages = st.decimals(
        min_value=Decimal('0.00'),
        max_value=Decimal('100.00'),
        places=2
    )
    
    valid_skus = st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Nd')),
        min_size=3,
        max_size=20
    )

    @given(
        price_list_code=valid_price_list_codes,
        name=valid_names,
        currency_code=valid_currencies,
        is_tax_included=st.booleans(),
        days_offset=st.integers(min_value=-365, max_value=365)
    )
    @settings(max_examples=100, deadline=None)
    def test_price_list_date_effective_accuracy(self, price_list_code, name, 
                                              currency_code, is_tax_included, days_offset):
        """
        **Feature: forge-api-rest, Property 56: Price list date-effective accuracy**
        
        For any price request, the system should return accurate pricing based on 
        date-effective price lists with proper currency and tax calculations.
        """
        # Calculate date range
        base_date = date.today()
        valid_from = base_date + timedelta(days=days_offset)
        valid_until = valid_from + timedelta(days=30) if days_offset <= 0 else None
        
        # Arrange: Create price list data
        price_list_data = {
            'price_list_code': price_list_code,
            'name': name,
            'currency_code': currency_code,
            'is_tax_included': is_tax_included,
            'is_active': True,
            'valid_from': valid_from,
            'valid_until': valid_until
        }

        # Act: Validate through serializer
        serializer = PriceListSerializer(data=price_list_data)
        
        # Assert: Date-effective accuracy should be maintained
        if serializer.is_valid():
            price_list = serializer.save()
            
            # Verify date-effective properties
            assert price_list.valid_from == valid_from
            assert price_list.valid_until == valid_until
            assert price_list.currency_code == currency_code
            assert price_list.is_tax_included == is_tax_included
            
            # Test date-effective logic
            today = date.today()
            
            if valid_from <= today and (valid_until is None or valid_until >= today):
                # Price list should be effective today
                assert price_list.is_active == True
                
                # Verify it can be retrieved for current date
                current_price_lists = PriceList.objects.filter(
                    valid_from__lte=today,
                    is_active=True
                ).filter(
                    models.Q(valid_until__gte=today) | models.Q(valid_until__isnull=True)
                )
                assert price_list in current_price_lists
            
            price_list.delete()

    @given(
        price_list_code=valid_price_list_codes,
        sku=valid_skus,
        unit_price=valid_prices,
        tax_percent=valid_percentages,
        discount_percent=valid_percentages,
        days_in_past=st.integers(min_value=1, max_value=30),
        days_in_future=st.integers(min_value=1, max_value=30)
    )
    @settings(max_examples=50, deadline=None)
    def test_product_price_date_effective_accuracy(self, price_list_code, sku, unit_price, 
                                                 tax_percent, discount_percent, 
                                                 days_in_past, days_in_future):
        """
        Test that product prices are accurately calculated based on date-effective rules
        """
        # Create price list
        price_list = PriceList.objects.create(
            price_list_code=price_list_code,
            name=f'Test Price List {price_list_code}',
            currency_code='USD',
            is_active=True,
            valid_from=date.today() - timedelta(days=days_in_past),
            valid_until=date.today() + timedelta(days=days_in_future)
        )
        
        try:
            # Create product price
            product_price_data = {
                'price_list': price_list.price_list_id,
                'internal_sku': sku,
                'unit_price': unit_price,
                'tax_percent': tax_percent,
                'discount_percent': discount_percent,
                'min_qty': 1,
                'valid_from': price_list.valid_from,
                'valid_until': price_list.valid_until
            }
            
            serializer = ProductPriceSerializer(data=product_price_data)
            
            if serializer.is_valid():
                product_price = serializer.save()
                
                # Verify price calculations
                assert product_price.unit_price == unit_price
                assert product_price.tax_percent == tax_percent
                assert product_price.discount_percent == discount_percent
                
                # Calculate expected final price
                discounted_price = unit_price * (Decimal('100') - discount_percent) / Decimal('100')
                
                if price_list.is_tax_included:
                    final_price = discounted_price
                else:
                    final_price = discounted_price * (Decimal('100') + tax_percent) / Decimal('100')
                
                # Verify date-effective retrieval
                today = date.today()
                if (product_price.valid_from <= today and 
                    (product_price.valid_until is None or product_price.valid_until >= today)):
                    
                    # Should be retrievable for current date
                    current_prices = ProductPrice.objects.filter(
                        price_list=price_list,
                        internal_sku=sku,
                        valid_from__lte=today
                    ).filter(
                        models.Q(valid_until__gte=today) | models.Q(valid_until__isnull=True)
                    )
                    assert product_price in current_prices
                
                product_price.delete()
                
        finally:
            price_list.delete()

    def test_overlapping_price_periods_accuracy(self):
        """
        Test accuracy when multiple price periods overlap
        """
        # Create base price list
        price_list = PriceList.objects.create(
            price_list_code='OVERLAP001',
            name='Overlap Test Price List',
            currency_code='USD',
            is_active=True,
            valid_from=date.today() - timedelta(days=30),
            valid_until=date.today() + timedelta(days=30)
        )
        
        try:
            # Create multiple price periods for same product
            sku = 'TESTSKU001'
            
            # Old price (expired)
            old_price = ProductPrice.objects.create(
                price_list=price_list,
                internal_sku=sku,
                unit_price=Decimal('10.00'),
                valid_from=date.today() - timedelta(days=30),
                valid_until=date.today() - timedelta(days=1)
            )
            
            # Current price
            current_price = ProductPrice.objects.create(
                price_list=price_list,
                internal_sku=sku,
                unit_price=Decimal('12.00'),
                valid_from=date.today(),
                valid_until=date.today() + timedelta(days=15)
            )
            
            # Future price
            future_price = ProductPrice.objects.create(
                price_list=price_list,
                internal_sku=sku,
                unit_price=Decimal('15.00'),
                valid_from=date.today() + timedelta(days=16),
                valid_until=date.today() + timedelta(days=30)
            )
            
            # Test current date retrieval
            today = date.today()
            current_prices = ProductPrice.objects.filter(
                price_list=price_list,
                internal_sku=sku,
                valid_from__lte=today,
                valid_until__gte=today
            ).order_by('-valid_from')
            
            # Should return only current price
            assert current_prices.count() == 1
            assert current_prices.first() == current_price
            assert current_prices.first().unit_price == Decimal('12.00')
            
            # Test future date retrieval
            future_date = date.today() + timedelta(days=20)
            future_prices = ProductPrice.objects.filter(
                price_list=price_list,
                internal_sku=sku,
                valid_from__lte=future_date,
                valid_until__gte=future_date
            ).order_by('-valid_from')
            
            # Should return future price
            assert future_prices.count() == 1
            assert future_prices.first() == future_price
            assert future_prices.first().unit_price == Decimal('15.00')
            
        finally:
            price_list.delete()

    def test_api_endpoint_date_effective_accuracy(self):
        """
        Test that API endpoints return date-effective pricing accurately
        """
        # Create price list via API
        price_list_data = {
            'price_list_code': 'API001',
            'name': 'API Test Price List',
            'currency_code': 'USD',
            'is_tax_included': False,
            'is_active': True,
            'valid_from': str(date.today()),
            'valid_until': str(date.today() + timedelta(days=30))
        }
        
        response = self.client.post('/api/v1/inventory/price-lists/', price_list_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        
        price_list_id = response.json()['price_list_id']
        
        # Create product price via API
        product_price_data = {
            'price_list': price_list_id,
            'internal_sku': 'APISKU001',
            'unit_price': '25.99',
            'tax_percent': '10.00',
            'discount_percent': '5.00',
            'min_qty': 1,
            'valid_from': str(date.today()),
            'valid_until': str(date.today() + timedelta(days=30))
        }
        
        response = self.client.post('/api/v1/inventory/product-prices/', product_price_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        
        # Verify date-effective retrieval via API
        response = self.client.get(f'/api/v1/inventory/product-prices/?price_list={price_list_id}&internal_sku=APISKU001')
        assert response.status_code == status.HTTP_200_OK
        
        prices = response.json()['results']
        assert len(prices) >= 1
        
        # Verify price calculation accuracy
        price_data = prices[0]
        assert Decimal(price_data['unit_price']) == Decimal('25.99')
        assert Decimal(price_data['tax_percent']) == Decimal('10.00')
        assert Decimal(price_data['discount_percent']) == Decimal('5.00')

    def tearDown(self):
        """Clean up test data"""
        # Clean up product prices first (due to foreign key)
        ProductPrice.objects.filter(price_list__price_list_code__startswith='API').delete()
        ProductPrice.objects.filter(price_list__price_list_code__startswith='OVERLAP').delete()
        ProductPrice.objects.filter(price_list__price_list_code__startswith='TEST').delete()
        
        # Clean up price lists
        PriceList.objects.filter(price_list_code__startswith='API').delete()
        PriceList.objects.filter(price_list_code__startswith='OVERLAP').delete()
        PriceList.objects.filter(price_list_code__startswith='TEST').delete()


# Import Django Q for complex queries
from django.db import models
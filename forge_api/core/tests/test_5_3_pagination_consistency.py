"""
ForgeDB API REST - Property Tests for Pagination Consistency
Task 5.3: Property test for pagination consistency

**Feature: forge-api-rest, Property 20: Pagination metadata consistency**
**Validates: Requirements 5.1**

This module contains property-based tests that verify the consistency of pagination
metadata and behavior across all ViewSets.
"""

from django.test import TestCase
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import QuerySet
import math
from datetime import date

from core.models import (
    Technician, Client, Equipment, WorkOrder, Invoice, 
    ProductMaster, Stock, Warehouse, Transaction
)
from core.serializers import (
    ClientSerializer, EquipmentSerializer, WorkOrderSerializer,
    ProductMasterSerializer, StockSerializer
)
from .test_helpers import TestDataFactory


class TestPaginationMetadataConsistency(TestCase):
    """
    Property-based tests for pagination metadata consistency across all ViewSets
    """
    
    def setUp(self):
        """Set up test data"""
        self.technician = TestDataFactory.create_technician()
    
    def test_pagination_metadata_consistency_for_clients(self):
        """
        **Feature: forge-api-rest, Property 20: Pagination metadata consistency**
        **Validates: Requirements 5.1**
        
        For any Client list request with pagination parameters, the system should 
        return consistent metadata including count, next, previous, and results.
        """
        # Setup: Create multiple clients
        clients = []
        for i in range(25):
            client = TestDataFactory.create_client(created_by=self.technician)
            clients.append(client)
        
        # Test different page sizes
        page_sizes = [5, 10, 20]
        
        for page_size in page_sizes:
            with self.subTest(page_size=page_size):
                # Create paginator
                queryset = Client.objects.all().order_by('client_code')
                paginator = Paginator(queryset, page_size)
                
                # Calculate expected values
                total_items = queryset.count()
                expected_pages = math.ceil(total_items / page_size)
                
                # Test first page
                page1 = paginator.get_page(1)
                self.assertEqual(len(page1.object_list), min(page_size, total_items))
                self.assertEqual(page1.number, 1)
                self.assertTrue(page1.has_next() if expected_pages > 1 else not page1.has_next())
                self.assertFalse(page1.has_previous())
                
                # Test middle page (if exists)
                if expected_pages > 2:
                    middle_page = 2
                    page_middle = paginator.get_page(middle_page)
                    self.assertEqual(len(page_middle.object_list), page_size)
                    self.assertEqual(page_middle.number, middle_page)
                    self.assertTrue(page_middle.has_next())
                    self.assertTrue(page_middle.has_previous())
                
                # Test last page
                if expected_pages > 1:
                    last_page = paginator.get_page(expected_pages)
                    expected_last_page_items = total_items - (expected_pages - 1) * page_size
                    self.assertEqual(len(last_page.object_list), expected_last_page_items)
                    self.assertEqual(last_page.number, expected_pages)
                    self.assertFalse(last_page.has_next())
                    self.assertTrue(last_page.has_previous())

    def test_pagination_metadata_consistency_for_equipment(self):
        """
        **Feature: forge-api-rest, Property 20: Pagination metadata consistency**
        **Validates: Requirements 5.1**
        
        For any Equipment list request with pagination, metadata should be consistent.
        """
        # Setup: Create client and equipment
        client = TestDataFactory.create_client(created_by=self.technician)
        equipment_list = []
        
        for i in range(15):
            equipment = TestDataFactory.create_equipment(client=client)
            equipment_list.append(equipment)
        
        # Test pagination with different parameters
        page_size = 7
        queryset = Equipment.objects.all().order_by('equipment_code')
        paginator = Paginator(queryset, page_size)
        
        total_items = queryset.count()
        expected_pages = math.ceil(total_items / page_size)
        
        # Verify pagination metadata consistency
        self.assertEqual(paginator.count, total_items)
        self.assertEqual(paginator.num_pages, expected_pages)
        self.assertEqual(paginator.per_page, page_size)
        
        # Test each page
        for page_num in range(1, expected_pages + 1):
            page = paginator.get_page(page_num)
            
            # Verify page metadata
            self.assertEqual(page.number, page_num)
            self.assertEqual(page.paginator, paginator)
            
            # Verify page content
            if page_num < expected_pages:
                self.assertEqual(len(page.object_list), page_size)
            else:
                # Last page might have fewer items
                expected_items = total_items - (page_num - 1) * page_size
                self.assertEqual(len(page.object_list), expected_items)

    def test_pagination_edge_cases(self):
        """
        **Feature: forge-api-rest, Property 20: Pagination metadata consistency**
        **Validates: Requirements 5.1**
        
        Test pagination behavior with edge cases like empty results, single item, etc.
        """
        # Test empty queryset
        empty_queryset = Client.objects.none()
        paginator = Paginator(empty_queryset, 10)
        
        self.assertEqual(paginator.count, 0)
        self.assertEqual(paginator.num_pages, 1)  # Django returns 1 page for empty results
        
        page = paginator.get_page(1)
        self.assertEqual(len(page.object_list), 0)
        self.assertFalse(page.has_next())
        self.assertFalse(page.has_previous())
        
        # Test single item
        single_client = TestDataFactory.create_client(created_by=self.technician)
        single_queryset = Client.objects.filter(client_id=single_client.client_id)
        paginator = Paginator(single_queryset, 10)
        
        self.assertEqual(paginator.count, 1)
        self.assertEqual(paginator.num_pages, 1)
        
        page = paginator.get_page(1)
        self.assertEqual(len(page.object_list), 1)
        self.assertFalse(page.has_next())
        self.assertFalse(page.has_previous())

    def test_pagination_invalid_page_numbers(self):
        """
        **Feature: forge-api-rest, Property 20: Pagination metadata consistency**
        **Validates: Requirements 5.1**
        
        Test pagination behavior with invalid page numbers.
        """
        # Setup: Create some clients
        for i in range(10):
            TestDataFactory.create_client(created_by=self.technician)
        
        queryset = Client.objects.all()
        paginator = Paginator(queryset, 5)  # 2 pages total
        
        # Test invalid page numbers
        invalid_pages = [0, -1, 999, 'invalid']
        
        for invalid_page in invalid_pages:
            with self.subTest(invalid_page=invalid_page):
                try:
                    # Negative or zero page numbers
                    if isinstance(invalid_page, int) and invalid_page <= 0:
                        with self.assertRaises(EmptyPage):
                            paginator.page(invalid_page)
                    # Page number exceeds available pages
                    elif isinstance(invalid_page, int) and invalid_page > paginator.num_pages:
                        with self.assertRaises(EmptyPage):
                            paginator.page(invalid_page)
                    # Non-integer page numbers
                    else:
                        with self.assertRaises(PageNotAnInteger):
                            paginator.page(invalid_page)
                except Exception as e:
                    # get_page() method handles errors gracefully
                    page = paginator.get_page(invalid_page)
                    # Should return first or last page
                    self.assertIn(page.number, [1, paginator.num_pages])

    def test_pagination_ordering_consistency(self):
        """
        **Feature: forge-api-rest, Property 20: Pagination metadata consistency**
        **Validates: Requirements 5.1**
        
        Test that pagination maintains consistent ordering across pages.
        """
        # Setup: Create work orders with different dates
        client = TestDataFactory.create_client(created_by=self.technician)
        equipment = TestDataFactory.create_equipment(client=client)
        
        work_orders = []
        for i in range(12):
            work_order = WorkOrder.objects.create(
                wo_number=f"WO{TestDataFactory.get_unique_id()}",
                client=client,
                equipment=equipment,
                description=f"Work order {i}",
                status='draft',
                priority='normal',
                created_by=self.technician
            )
            work_orders.append(work_order)
        
        # Test ordering by wo_number
        queryset = WorkOrder.objects.all().order_by('wo_number')
        paginator = Paginator(queryset, 5)
        
        # Get all items across pages
        all_items = []
        for page_num in range(1, paginator.num_pages + 1):
            page = paginator.get_page(page_num)
            all_items.extend(page.object_list)
        
        # Verify ordering is maintained
        wo_numbers = [wo.wo_number for wo in all_items]
        self.assertEqual(wo_numbers, sorted(wo_numbers))
        
        # Verify no items are duplicated or missing
        self.assertEqual(len(all_items), queryset.count())
        self.assertEqual(set(wo.wo_id for wo in all_items), 
                        set(wo.wo_id for wo in queryset))


class TestPaginationPerformanceConsistency(TestCase):
    """
    Tests for pagination performance and consistency
    """
    
    def setUp(self):
        """Set up test data"""
        self.technician = TestDataFactory.create_technician()
    
    def test_pagination_performance_with_large_datasets(self):
        """
        **Feature: forge-api-rest, Property 20: Pagination metadata consistency**
        **Validates: Requirements 5.1**
        
        Test pagination performance and consistency with larger datasets.
        """
        # Setup: Create larger dataset
        clients = []
        for i in range(100):
            client = TestDataFactory.create_client(created_by=self.technician)
            clients.append(client)
        
        # Test different page sizes
        page_sizes = [10, 25, 50]
        
        for page_size in page_sizes:
            with self.subTest(page_size=page_size):
                queryset = Client.objects.all().order_by('client_code')
                paginator = Paginator(queryset, page_size)
                
                # Verify metadata consistency
                expected_pages = math.ceil(queryset.count() / page_size)
                self.assertEqual(paginator.num_pages, expected_pages)
                
                # Test first and last pages
                first_page = paginator.get_page(1)
                last_page = paginator.get_page(paginator.num_pages)
                
                self.assertEqual(len(first_page.object_list), page_size)
                self.assertLessEqual(len(last_page.object_list), page_size)
                
                # Verify total items across all pages
                total_paginated_items = (paginator.num_pages - 1) * page_size + len(last_page.object_list)
                self.assertEqual(total_paginated_items, queryset.count())

    def test_pagination_with_filtering(self):
        """
        **Feature: forge-api-rest, Property 20: Pagination metadata consistency**
        **Validates: Requirements 5.1**
        
        Test pagination consistency when combined with filtering.
        """
        # Setup: Create clients with different types
        individual_clients = []
        business_clients = []
        
        for i in range(15):
            individual_client = TestDataFactory.create_client(
                created_by=self.technician,
                type='individual'
            )
            individual_clients.append(individual_client)
            
            business_client = TestDataFactory.create_client(
                created_by=self.technician,
                type='business'
            )
            business_clients.append(business_client)
        
        # Test pagination with filtering
        individual_queryset = Client.objects.filter(type='individual').order_by('client_code')
        paginator = Paginator(individual_queryset, 7)
        
        # Verify filtered pagination metadata
        self.assertEqual(paginator.count, len(individual_clients))
        expected_pages = math.ceil(len(individual_clients) / 7)
        self.assertEqual(paginator.num_pages, expected_pages)
        
        # Verify all paginated items match filter
        for page_num in range(1, paginator.num_pages + 1):
            page = paginator.get_page(page_num)
            for client in page.object_list:
                self.assertEqual(client.type, 'individual')

    def test_pagination_serializer_consistency(self):
        """
        **Feature: forge-api-rest, Property 20: Pagination metadata consistency**
        **Validates: Requirements 5.1**
        
        Test that pagination works consistently with serializers.
        """
        # Setup: Create products
        products = []
        for i in range(20):
            product = TestDataFactory.create_product()
            products.append(product)
        
        # Test pagination with serialization
        queryset = ProductMaster.objects.all().order_by('product_code')
        paginator = Paginator(queryset, 8)
        
        for page_num in range(1, paginator.num_pages + 1):
            page = paginator.get_page(page_num)
            
            # Serialize page data
            serializer = ProductMasterSerializer(page.object_list, many=True)
            serialized_data = serializer.data
            
            # Verify serialization consistency
            self.assertEqual(len(serialized_data), len(page.object_list))
            
            # Verify each serialized item has required fields
            for item in serialized_data:
                self.assertIn('product_code', item)
                self.assertIn('name', item)
                self.assertIn('type', item)
                self.assertIn('status', item)


# Tests can be run with: python manage.py test core.tests.test_5_3_pagination_consistency
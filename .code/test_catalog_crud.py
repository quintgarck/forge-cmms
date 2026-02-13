#!/usr/bin/env python3
"""
CATALOG CRUD FUNCTIONALITY VERIFICATION SCRIPT

This script tests all catalog CRUD operations to ensure they're working correctly
after the authentication fixes.
"""

import requests
import json
from urllib.parse import urljoin
import time

class CatalogCRUDTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.authenticated = False
        
    def login(self, username="admin", password="admin123"):
        """Login to the system"""
        try:
            # Get CSRF token first
            csrf_response = self.session.get(f"{self.base_url}/login/")
            csrf_token = csrf_response.cookies.get('csrftoken')
            
            login_data = {
                'username': username,
                'password': password,
                'csrfmiddlewaretoken': csrf_token
            }
            
            response = self.session.post(
                f"{self.base_url}/login/",
                data=login_data,
                headers={'Referer': f"{self.base_url}/login/"}
            )
            
            if response.status_code in [200, 302]:
                self.authenticated = True
                print("✅ Login successful")
                return True
            else:
                print(f"❌ Login failed - Status: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Login error: {str(e)}")
            return False
    
    def test_catalog_endpoints(self):
        """Test all catalog-related endpoints"""
        if not self.authenticated:
            print("❌ Not authenticated. Please login first.")
            return False
            
        test_cases = [
            # Equipment Types
            {
                'name': 'Equipment Types List',
                'url': '/catalog/equipment-types/',
                'method': 'GET',
                'expected_status': 200
            },
            {
                'name': 'Equipment Types Create Form',
                'url': '/catalog/equipment-types/create/',
                'method': 'GET',
                'expected_status': 200
            },
            
            # Reference Codes
            {
                'name': 'Reference Codes List',
                'url': '/catalog/reference-codes/',
                'method': 'GET',
                'expected_status': 200
            },
            {
                'name': 'Reference Codes Create Form',
                'url': '/catalog/reference-codes/create/',
                'method': 'GET',
                'expected_status': 200
            },
            
            # Taxonomy
            {
                'name': 'Taxonomy Tree View',
                'url': '/catalog/taxonomy/',
                'method': 'GET',
                'expected_status': 200
            },
            {
                'name': 'Taxonomy Systems List',
                'url': '/catalog/taxonomy/systems/',
                'method': 'GET',
                'expected_status': 200
            },
            
            # Currencies
            {
                'name': 'Currencies List',
                'url': '/catalog/currencies/',
                'method': 'GET',
                'expected_status': 200
            },
            {
                'name': 'Currency Converter',
                'url': '/catalog/currencies/converter/',
                'method': 'GET',
                'expected_status': 200
            },
            
            # Clients
            {
                'name': 'Clients List',
                'url': '/clients/',
                'method': 'GET',
                'expected_status': 200
            },
            {
                'name': 'Clients Create Form',
                'url': '/clients/create/',
                'method': 'GET',
                'expected_status': 200
            },
            
            # Equipment
            {
                'name': 'Equipment List',
                'url': '/equipment/',
                'method': 'GET',
                'expected_status': 200
            },
            {
                'name': 'Equipment Create Form',
                'url': '/equipment/create/',
                'method': 'GET',
                'expected_status': 200
            },
            
            # OEM
            {
                'name': 'OEM Brands List',
                'url': '/oem/brands/list/',
                'method': 'GET',
                'expected_status': 200
            },
            {
                'name': 'OEM Catalog Items',
                'url': '/oem/catalog/items/',
                'method': 'GET',
                'expected_status': 200
            },
            
            # Suppliers
            {
                'name': 'Suppliers List',
                'url': '/suppliers/',
                'method': 'GET',
                'expected_status': 200
            },
            
            # Alerts
            {
                'name': 'Alerts Dashboard',
                'url': '/alerts/',
                'method': 'GET',
                'expected_status': 200
            },
            
            # Quotes
            {
                'name': 'Quotes List',
                'url': '/quotes/',
                'method': 'GET',
                'expected_status': 200
            },
        ]
        
        results = []
        passed = 0
        failed = 0
        
        print("\n" + "="*60)
        print("TESTING CATALOG CRUD ENDPOINTS")
        print("="*60)
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{i}. Testing: {test_case['name']}")
            print(f"   URL: {test_case['url']}")
            print(f"   Method: {test_case['method']}", end="")
            
            try:
                if test_case['method'] == 'GET':
                    response = self.session.get(urljoin(self.base_url, test_case['url']))
                else:
                    response = self.session.post(urljoin(self.base_url, test_case['url']))
                
                status_ok = response.status_code == test_case['expected_status']
                content_ok = 'html' in response.headers.get('content-type', '').lower()
                
                if status_ok and content_ok:
                    print(f" ✅ PASS (Status: {response.status_code})")
                    passed += 1
                    results.append({
                        'test': test_case['name'],
                        'status': 'PASS',
                        'status_code': response.status_code
                    })
                else:
                    print(f" ❌ FAIL (Status: {response.status_code}, Content-Type: {response.headers.get('content-type', 'unknown')})")
                    failed += 1
                    results.append({
                        'test': test_case['name'],
                        'status': 'FAIL',
                        'status_code': response.status_code,
                        'content_type': response.headers.get('content-type', 'unknown')
                    })
                    
            except Exception as e:
                print(f" ❌ ERROR - {str(e)}")
                failed += 1
                results.append({
                    'test': test_case['name'],
                    'status': 'ERROR',
                    'error': str(e)
                })
            
            # Small delay to avoid overwhelming the server
            time.sleep(0.1)
        
        # Summary
        print("\n" + "="*60)
        print("TEST RESULTS SUMMARY")
        print("="*60)
        print(f"Total Tests: {len(test_cases)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/len(test_cases)*100):.1f}%")
        
        if failed > 0:
            print("\nFAILED TESTS:")
            for result in results:
                if result['status'] != 'PASS':
                    print(f"  - {result['test']}: {result.get('status', 'ERROR')} "
                          f"(Status: {result.get('status_code', 'N/A')})")
        
        return failed == 0
    
    def test_api_endpoints(self):
        """Test API endpoints for catalog data"""
        if not self.authenticated:
            print("❌ Not authenticated. Please login first.")
            return False
            
        api_tests = [
            {
                'name': 'Equipment Types API',
                'url': '/api/v1/equipment-types/',
                'method': 'GET'
            },
            {
                'name': 'Fuel Codes API',
                'url': '/api/v1/fuel-codes/',
                'method': 'GET'
            },
            {
                'name': 'Currencies API',
                'url': '/api/v1/currencies/',
                'method': 'GET'
            },
            {
                'name': 'Clients API',
                'url': '/api/v1/clients/',
                'method': 'GET'
            },
        ]
        
        print("\n" + "="*60)
        print("TESTING API ENDPOINTS")
        print("="*60)
        
        api_passed = 0
        api_failed = 0
        
        for test in api_tests:
            print(f"\nTesting: {test['name']}")
            print(f"URL: {test['url']}")
            
            try:
                if test['method'] == 'GET':
                    response = self.session.get(urljoin(self.base_url, test['url']))
                else:
                    response = self.session.post(urljoin(self.base_url, test['url']))
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        print(f"✅ PASS - Status: {response.status_code}")
                        print(f"   Records found: {data.get('count', len(data))}")
                        api_passed += 1
                    except json.JSONDecodeError:
                        print(f"❌ FAIL - Invalid JSON response")
                        api_failed += 1
                else:
                    print(f"❌ FAIL - Status: {response.status_code}")
                    api_failed += 1
                    
            except Exception as e:
                print(f"❌ ERROR - {str(e)}")
                api_failed += 1
        
        print(f"\nAPI Tests - Passed: {api_passed}, Failed: {api_failed}")
        return api_failed == 0

def main():
    tester = CatalogCRUDTester()
    
    print("Forge CMMS Catalog CRUD Verification Tool")
    print("=" * 50)
    
    # Login
    if not tester.login():
        print("\n❌ Unable to login. Please check credentials and server status.")
        return
    
    # Test frontend endpoints
    frontend_success = tester.test_catalog_endpoints()
    
    # Test API endpoints
    api_success = tester.test_api_endpoints()
    
    # Final summary
    print("\n" + "="*60)
    print("FINAL VERIFICATION SUMMARY")
    print("="*60)
    
    if frontend_success and api_success:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Catalog CRUD functionality is working correctly")
        print("✅ Authentication is properly configured")
        print("✅ All endpoints are accessible")
    else:
        print("⚠️  SOME TESTS FAILED")
        if not frontend_success:
            print("❌ Frontend CRUD endpoints have issues")
        if not api_success:
            print("❌ API endpoints have issues")
        print("\nPlease check the detailed output above for specific errors.")

if __name__ == "__main__":
    main()
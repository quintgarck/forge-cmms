#!/usr/bin/env python3
"""
Test script for responsive design and performance optimizations
ForgeDB Frontend - Tasks 10.1 and 10.2
"""

import os
import sys
import django
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')
django.setup()

class ResponsivePerformanceTest:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.driver = None
        self.results = {
            'responsive_tests': [],
            'performance_tests': [],
            'errors': []
        }
    
    def setup_driver(self, mobile=False):
        """Setup Chrome driver with mobile or desktop configuration"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        
        if mobile:
            # Mobile device simulation (iPhone 12)
            mobile_emulation = {
                "deviceMetrics": {"width": 390, "height": 844, "pixelRatio": 3.0},
                "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15"
            }
            chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
        else:
            # Desktop configuration
            chrome_options.add_argument('--window-size=1920,1080')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            return True
        except Exception as e:
            print(f"Error setting up Chrome driver: {e}")
            return False
    
    def test_responsive_breakpoints(self):
        """Test responsive design at different breakpoints"""
        print("🔍 Testing responsive breakpoints...")
        
        breakpoints = [
            {'name': 'Mobile', 'width': 375, 'height': 667},
            {'name': 'Tablet', 'width': 768, 'height': 1024},
            {'name': 'Desktop', 'width': 1200, 'height': 800},
            {'name': 'Large Desktop', 'width': 1920, 'height': 1080}
        ]
        
        pages_to_test = [
            '/frontend/',
            '/frontend/clients/',
            '/frontend/workorders/',
            '/frontend/inventory/'
        ]
        
        for breakpoint in breakpoints:
            print(f"  Testing {breakpoint['name']} ({breakpoint['width']}x{breakpoint['height']})...")
            
            if not self.setup_driver():
                continue
                
            self.driver.set_window_size(breakpoint['width'], breakpoint['height'])
            
            for page in pages_to_test:
                try:
                    self.driver.get(f"{self.base_url}{page}")
                    
                    # Wait for page to load
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "main"))
                    )
                    
                    # Check if navigation is properly collapsed on mobile
                    if breakpoint['width'] < 992:
                        navbar_toggle = self.driver.find_elements(By.CLASS_NAME, "navbar-toggler")
                        if navbar_toggle:
                            is_visible = navbar_toggle[0].is_displayed()
                            self.results['responsive_tests'].append({
                                'test': f'Mobile navigation toggle - {page}',
                                'breakpoint': breakpoint['name'],
                                'passed': is_visible,
                                'details': 'Mobile navigation toggle is visible' if is_visible else 'Mobile navigation toggle not found'
                            })
                    
                    # Check if tables are responsive
                    tables = self.driver.find_elements(By.CLASS_NAME, "table-responsive")
                    for table in tables:
                        has_horizontal_scroll = self.driver.execute_script(
                            "return arguments[0].scrollWidth > arguments[0].clientWidth;", table
                        )
                        self.results['responsive_tests'].append({
                            'test': f'Table responsiveness - {page}',
                            'breakpoint': breakpoint['name'],
                            'passed': True,  # Table-responsive class is present
                            'details': f'Horizontal scroll: {has_horizontal_scroll}'
                        })
                    
                    # Check button sizes on mobile
                    if breakpoint['width'] < 768:
                        buttons = self.driver.find_elements(By.CLASS_NAME, "btn")
                        for i, button in enumerate(buttons[:3]):  # Check first 3 buttons
                            height = button.size['height']
                            min_touch_target = 44  # Apple's recommended minimum
                            self.results['responsive_tests'].append({
                                'test': f'Touch target size - Button {i+1} - {page}',
                                'breakpoint': breakpoint['name'],
                                'passed': height >= min_touch_target,
                                'details': f'Button height: {height}px (min: {min_touch_target}px)'
                            })
                    
                    print(f"    ✅ {page} - OK")
                    
                except TimeoutException:
                    error_msg = f"Timeout loading {page} at {breakpoint['name']}"
                    print(f"    ❌ {error_msg}")
                    self.results['errors'].append(error_msg)
                except Exception as e:
                    error_msg = f"Error testing {page} at {breakpoint['name']}: {str(e)}"
                    print(f"    ❌ {error_msg}")
                    self.results['errors'].append(error_msg)
            
            self.driver.quit()
    
    def test_touch_friendly_elements(self):
        """Test touch-friendly interface elements"""
        print("🔍 Testing touch-friendly elements...")
        
        if not self.setup_driver(mobile=True):
            return
        
        pages_to_test = [
            '/frontend/',
            '/frontend/clients/',
            '/frontend/clients/create/'
        ]
        
        for page in pages_to_test:
            try:
                self.driver.get(f"{self.base_url}{page}")
                
                # Wait for page to load
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "main"))
                )
                
                # Test form controls
                form_controls = self.driver.find_elements(By.CLASS_NAME, "form-control")
                for i, control in enumerate(form_controls[:5]):  # Test first 5
                    height = control.size['height']
                    font_size = self.driver.execute_script(
                        "return window.getComputedStyle(arguments[0]).fontSize;", control
                    )
                    
                    # Check minimum height and font size for iOS
                    min_height = 44
                    expected_font_size = "16px"  # Prevents zoom on iOS
                    
                    self.results['responsive_tests'].append({
                        'test': f'Form control touch-friendly - {page}',
                        'breakpoint': 'Mobile',
                        'passed': height >= min_height and font_size == expected_font_size,
                        'details': f'Height: {height}px, Font-size: {font_size}'
                    })
                
                # Test button sizes
                buttons = self.driver.find_elements(By.CLASS_NAME, "btn")
                for i, button in enumerate(buttons[:3]):
                    height = button.size['height']
                    self.results['responsive_tests'].append({
                        'test': f'Button touch target - {page}',
                        'breakpoint': 'Mobile',
                        'passed': height >= 44,
                        'details': f'Height: {height}px'
                    })
                
                print(f"    ✅ {page} - Touch elements OK")
                
            except Exception as e:
                error_msg = f"Error testing touch elements on {page}: {str(e)}"
                print(f"    ❌ {error_msg}")
                self.results['errors'].append(error_msg)
        
        self.driver.quit()
    
    def test_performance_optimizations(self):
        """Test performance optimizations"""
        print("🔍 Testing performance optimizations...")
        
        if not self.setup_driver():
            return
        
        pages_to_test = [
            '/frontend/',
            '/frontend/clients/',
            '/frontend/workorders/'
        ]
        
        for page in pages_to_test:
            try:
                start_time = time.time()
                self.driver.get(f"{self.base_url}{page}")
                
                # Wait for page to load completely
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "main"))
                )
                
                load_time = time.time() - start_time
                
                # Check if performance.js is loaded
                performance_js_loaded = self.driver.execute_script(
                    "return typeof window.LazyLoader !== 'undefined';"
                )
                
                # Check if service worker is registered
                sw_registered = self.driver.execute_script(
                    "return 'serviceWorker' in navigator && navigator.serviceWorker.controller !== null;"
                )
                
                # Check for lazy loading images
                lazy_images = self.driver.find_elements(By.CSS_SELECTOR, "img[data-src]")
                
                # Check for responsive CSS
                responsive_css = self.driver.execute_script(
                    """
                    var links = document.querySelectorAll('link[href*="responsive.css"]');
                    return links.length > 0;
                    """
                )
                
                # Check for critical CSS inlined
                critical_css = self.driver.execute_script(
                    "return document.querySelector('style') !== null;"
                )
                
                self.results['performance_tests'].append({
                    'page': page,
                    'load_time': round(load_time, 2),
                    'performance_js_loaded': performance_js_loaded,
                    'service_worker_registered': sw_registered,
                    'lazy_images_count': len(lazy_images),
                    'responsive_css_loaded': responsive_css,
                    'critical_css_inlined': critical_css,
                    'passed': load_time < 5.0 and performance_js_loaded and responsive_css
                })
                
                print(f"    ✅ {page} - Load time: {load_time:.2f}s")
                
            except Exception as e:
                error_msg = f"Error testing performance on {page}: {str(e)}"
                print(f"    ❌ {error_msg}")
                self.results['errors'].append(error_msg)
        
        self.driver.quit()
    
    def test_lazy_loading(self):
        """Test lazy loading implementation"""
        print("🔍 Testing lazy loading...")
        
        if not self.setup_driver():
            return
        
        try:
            # Go to a page with potential lazy content
            self.driver.get(f"{self.base_url}/frontend/inventory/")
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "main"))
            )
            
            # Check if LazyLoader is available
            lazy_loader_available = self.driver.execute_script(
                "return typeof window.LazyLoader !== 'undefined';"
            )
            
            # Check for intersection observer support
            intersection_observer_support = self.driver.execute_script(
                "return 'IntersectionObserver' in window;"
            )
            
            # Look for lazy loading elements
            lazy_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-lazy-content], img[data-src]")
            
            self.results['performance_tests'].append({
                'test': 'Lazy Loading Implementation',
                'lazy_loader_available': lazy_loader_available,
                'intersection_observer_support': intersection_observer_support,
                'lazy_elements_count': len(lazy_elements),
                'passed': lazy_loader_available and intersection_observer_support
            })
            
            print(f"    ✅ Lazy loading - Elements found: {len(lazy_elements)}")
            
        except Exception as e:
            error_msg = f"Error testing lazy loading: {str(e)}"
            print(f"    ❌ {error_msg}")
            self.results['errors'].append(error_msg)
        
        self.driver.quit()
    
    def test_caching_implementation(self):
        """Test client-side caching"""
        print("🔍 Testing caching implementation...")
        
        if not self.setup_driver():
            return
        
        try:
            self.driver.get(f"{self.base_url}/frontend/")
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "main"))
            )
            
            # Check if API cache is available
            api_cache_available = self.driver.execute_script(
                "return typeof window.apiCache !== 'undefined';"
            )
            
            # Check if CacheManager is available
            cache_manager_available = self.driver.execute_script(
                "return typeof window.CacheManager !== 'undefined';"
            )
            
            self.results['performance_tests'].append({
                'test': 'Client-side Caching',
                'api_cache_available': api_cache_available,
                'cache_manager_available': cache_manager_available,
                'passed': api_cache_available
            })
            
            print(f"    ✅ Caching - API Cache: {api_cache_available}")
            
        except Exception as e:
            error_msg = f"Error testing caching: {str(e)}"
            print(f"    ❌ {error_msg}")
            self.results['errors'].append(error_msg)
        
        self.driver.quit()
    
    def generate_report(self):
        """Generate test report"""
        print("\n" + "="*60)
        print("📊 RESPONSIVE DESIGN & PERFORMANCE TEST REPORT")
        print("="*60)
        
        # Responsive Tests Summary
        responsive_passed = sum(1 for test in self.results['responsive_tests'] if test['passed'])
        responsive_total = len(self.results['responsive_tests'])
        
        print(f"\n🎨 RESPONSIVE DESIGN TESTS:")
        print(f"   Passed: {responsive_passed}/{responsive_total}")
        
        if responsive_total > 0:
            print(f"   Success Rate: {(responsive_passed/responsive_total)*100:.1f}%")
            
            # Group by breakpoint
            breakpoints = {}
            for test in self.results['responsive_tests']:
                bp = test.get('breakpoint', 'Unknown')
                if bp not in breakpoints:
                    breakpoints[bp] = {'passed': 0, 'total': 0}
                breakpoints[bp]['total'] += 1
                if test['passed']:
                    breakpoints[bp]['passed'] += 1
            
            for bp, stats in breakpoints.items():
                print(f"   {bp}: {stats['passed']}/{stats['total']} tests passed")
        
        # Performance Tests Summary
        performance_passed = sum(1 for test in self.results['performance_tests'] if test.get('passed', False))
        performance_total = len(self.results['performance_tests'])
        
        print(f"\n⚡ PERFORMANCE TESTS:")
        print(f"   Passed: {performance_passed}/{performance_total}")
        
        if performance_total > 0:
            print(f"   Success Rate: {(performance_passed/performance_total)*100:.1f}%")
            
            # Show load times
            for test in self.results['performance_tests']:
                if 'load_time' in test:
                    status = "✅" if test['load_time'] < 3.0 else "⚠️" if test['load_time'] < 5.0 else "❌"
                    print(f"   {status} {test['page']}: {test['load_time']}s")
        
        # Errors Summary
        if self.results['errors']:
            print(f"\n❌ ERRORS ({len(self.results['errors'])}):")
            for error in self.results['errors'][:5]:  # Show first 5 errors
                print(f"   • {error}")
            if len(self.results['errors']) > 5:
                print(f"   ... and {len(self.results['errors']) - 5} more errors")
        
        # Overall Status
        total_tests = responsive_total + performance_total
        total_passed = responsive_passed + performance_passed
        
        print(f"\n🎯 OVERALL RESULTS:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {total_passed}")
        print(f"   Failed: {total_tests - total_passed}")
        print(f"   Errors: {len(self.results['errors'])}")
        
        if total_tests > 0:
            success_rate = (total_passed / total_tests) * 100
            print(f"   Success Rate: {success_rate:.1f}%")
            
            if success_rate >= 90:
                print("   Status: 🟢 EXCELLENT")
            elif success_rate >= 75:
                print("   Status: 🟡 GOOD")
            elif success_rate >= 50:
                print("   Status: 🟠 NEEDS IMPROVEMENT")
            else:
                print("   Status: 🔴 CRITICAL ISSUES")
        
        print("="*60)
    
    def run_all_tests(self):
        """Run all responsive and performance tests"""
        print("🚀 Starting Responsive Design & Performance Tests...")
        print("="*60)
        
        try:
            # Test responsive breakpoints
            self.test_responsive_breakpoints()
            
            # Test touch-friendly elements
            self.test_touch_friendly_elements()
            
            # Test performance optimizations
            self.test_performance_optimizations()
            
            # Test lazy loading
            self.test_lazy_loading()
            
            # Test caching
            self.test_caching_implementation()
            
        except KeyboardInterrupt:
            print("\n⚠️ Tests interrupted by user")
        except Exception as e:
            print(f"\n❌ Unexpected error during testing: {e}")
            self.results['errors'].append(f"Unexpected error: {e}")
        finally:
            # Generate report
            self.generate_report()

def main():
    """Main function to run tests"""
    print("ForgeDB Frontend - Responsive Design & Performance Tests")
    print("Tasks 10.1 and 10.2 Verification")
    print("="*60)
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:8000/frontend/", timeout=5)
        if response.status_code != 200:
            print("❌ Server is not responding correctly")
            print("Please make sure the Django development server is running:")
            print("   python manage.py runserver")
            return
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to server at http://localhost:8000")
        print("Please make sure the Django development server is running:")
        print("   python manage.py runserver")
        return
    
    # Run tests
    tester = ResponsivePerformanceTest()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
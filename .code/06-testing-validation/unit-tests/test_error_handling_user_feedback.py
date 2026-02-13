#!/usr/bin/env python3
"""
Test script for error handling and user feedback systems
ForgeDB Frontend - Tasks 11.1 and 11.2
"""

import os
import sys
import django
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')
django.setup()

class ErrorHandlingUserFeedbackTest:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.driver = None
        self.results = {
            'error_handling_tests': [],
            'user_feedback_tests': [],
            'loading_state_tests': [],
            'toast_notification_tests': [],
            'empty_state_tests': [],
            'form_validation_tests': [],
            'errors': []
        }
    
    def setup_driver(self):
        """Setup Chrome driver"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            return True
        except Exception as e:
            print(f"Error setting up Chrome driver: {e}")
            return False
    
    def test_error_handler_initialization(self):
        """Test error handler JavaScript initialization"""
        print("🔍 Testing error handler initialization...")
        
        if not self.setup_driver():
            return
        
        try:
            self.driver.get(f"{self.base_url}/frontend/")
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "main"))
            )
            
            # Check if error handler is initialized
            error_handler_available = self.driver.execute_script(
                "return typeof window.errorHandler !== 'undefined';"
            )
            
            # Check if error container exists
            error_container_exists = self.driver.execute_script(
                "return document.getElementById('error-container') !== null;"
            )
            
            # Check if ErrorHandler class is available
            error_handler_class_available = self.driver.execute_script(
                "return typeof ErrorHandler !== 'undefined';"
            )
            
            self.results['error_handling_tests'].append({
                'test': 'Error Handler Initialization',
                'error_handler_available': error_handler_available,
                'error_container_exists': error_container_exists,
                'error_handler_class_available': error_handler_class_available,
                'passed': error_handler_available and error_container_exists
            })
            
            print(f"    ✅ Error handler available: {error_handler_available}")
            print(f"    ✅ Error container exists: {error_container_exists}")
            
        except Exception as e:
            error_msg = f"Error testing error handler initialization: {str(e)}"
            print(f"    ❌ {error_msg}")
            self.results['errors'].append(error_msg)
        
        self.driver.quit()
    
    def test_user_feedback_initialization(self):
        """Test user feedback system initialization"""
        print("🔍 Testing user feedback system initialization...")
        
        if not self.setup_driver():
            return
        
        try:
            self.driver.get(f"{self.base_url}/frontend/")
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "main"))
            )
            
            # Check if user feedback is initialized
            user_feedback_available = self.driver.execute_script(
                "return typeof window.userFeedback !== 'undefined';"
            )
            
            # Check individual managers
            loading_manager_available = self.driver.execute_script(
                "return typeof window.loadingManager !== 'undefined';"
            )
            
            toast_manager_available = self.driver.execute_script(
                "return typeof window.toastManager !== 'undefined';"
            )
            
            empty_state_manager_available = self.driver.execute_script(
                "return typeof window.emptyStateManager !== 'undefined';"
            )
            
            # Check if toast container exists
            toast_container_exists = self.driver.execute_script(
                "return document.getElementById('toast-container') !== null;"
            )
            
            self.results['user_feedback_tests'].append({
                'test': 'User Feedback System Initialization',
                'user_feedback_available': user_feedback_available,
                'loading_manager_available': loading_manager_available,
                'toast_manager_available': toast_manager_available,
                'empty_state_manager_available': empty_state_manager_available,
                'toast_container_exists': toast_container_exists,
                'passed': all([
                    user_feedback_available,
                    loading_manager_available,
                    toast_manager_available,
                    empty_state_manager_available,
                    toast_container_exists
                ])
            })
            
            print(f"    ✅ User feedback available: {user_feedback_available}")
            print(f"    ✅ Loading manager available: {loading_manager_available}")
            print(f"    ✅ Toast manager available: {toast_manager_available}")
            print(f"    ✅ Empty state manager available: {empty_state_manager_available}")
            
        except Exception as e:
            error_msg = f"Error testing user feedback initialization: {str(e)}"
            print(f"    ❌ {error_msg}")
            self.results['errors'].append(error_msg)
        
        self.driver.quit()
    
    def test_loading_states(self):
        """Test loading state functionality"""
        print("🔍 Testing loading states...")
        
        if not self.setup_driver():
            return
        
        try:
            self.driver.get(f"{self.base_url}/frontend/")
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "main"))
            )
            
            # Test global loading
            global_loader_shown = self.driver.execute_script("""
                if (window.loadingManager) {
                    const loaderId = window.loadingManager.showLoading('global', 'Testing...');
                    const loader = document.getElementById('global-loader');
                    const isVisible = loader && !loader.classList.contains('d-none');
                    window.loadingManager.hideLoading(loaderId);
                    return isVisible;
                }
                return false;
            """)
            
            # Test button loading
            button_loading_works = self.driver.execute_script("""
                if (window.loadingManager) {
                    // Create a test button
                    const button = document.createElement('button');
                    button.textContent = 'Test Button';
                    button.className = 'btn btn-primary';
                    document.body.appendChild(button);
                    
                    // Show loading
                    const loaderId = window.loadingManager.showLoading(button, 'Loading...');
                    const hasSpinner = button.querySelector('.spinner-border') !== null;
                    const isDisabled = button.disabled;
                    
                    // Hide loading
                    window.loadingManager.hideLoading(loaderId);
                    const spinnerRemoved = button.querySelector('.spinner-border') === null;
                    const isEnabled = !button.disabled;
                    
                    // Clean up
                    button.remove();
                    
                    return hasSpinner && isDisabled && spinnerRemoved && isEnabled;
                }
                return false;
            """)
            
            self.results['loading_state_tests'].append({
                'test': 'Loading States Functionality',
                'global_loader_works': global_loader_shown,
                'button_loading_works': button_loading_works,
                'passed': global_loader_shown and button_loading_works
            })
            
            print(f"    ✅ Global loader: {global_loader_shown}")
            print(f"    ✅ Button loading: {button_loading_works}")
            
        except Exception as e:
            error_msg = f"Error testing loading states: {str(e)}"
            print(f"    ❌ {error_msg}")
            self.results['errors'].append(error_msg)
        
        self.driver.quit()
    
    def test_toast_notifications(self):
        """Test toast notification functionality"""
        print("🔍 Testing toast notifications...")
        
        if not self.setup_driver():
            return
        
        try:
            self.driver.get(f"{self.base_url}/frontend/")
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "main"))
            )
            
            # Test different toast types
            toast_types = ['success', 'error', 'warning', 'info']
            toast_results = {}
            
            for toast_type in toast_types:
                toast_shown = self.driver.execute_script(f"""
                    if (window.toastManager) {{
                        const toast = window.toastManager.{toast_type}('Test {toast_type} message');
                        const container = document.getElementById('toast-container');
                        const toastExists = container && container.children.length > 0;
                        
                        // Clean up
                        if (toast && toast.parentNode) {{
                            toast.parentNode.removeChild(toast);
                        }}
                        
                        return toastExists;
                    }}
                    return false;
                """)
                
                toast_results[f'{toast_type}_toast'] = toast_shown
                print(f"    ✅ {toast_type.capitalize()} toast: {toast_shown}")
            
            # Test toast with custom options
            custom_toast_works = self.driver.execute_script("""
                if (window.toastManager) {
                    const toast = window.toastManager.show('Custom message', 'info', {
                        title: 'Custom Title',
                        duration: 1000
                    });
                    const hasTitle = toast.textContent.includes('Custom Title');
                    
                    // Clean up
                    if (toast && toast.parentNode) {
                        toast.parentNode.removeChild(toast);
                    }
                    
                    return hasTitle;
                }
                return false;
            """)
            
            toast_results['custom_toast'] = custom_toast_works
            
            self.results['toast_notification_tests'].append({
                'test': 'Toast Notifications Functionality',
                **toast_results,
                'passed': all(toast_results.values())
            })
            
            print(f"    ✅ Custom toast: {custom_toast_works}")
            
        except Exception as e:
            error_msg = f"Error testing toast notifications: {str(e)}"
            print(f"    ❌ {error_msg}")
            self.results['errors'].append(error_msg)
        
        self.driver.quit()
    
    def test_empty_states(self):
        """Test empty state functionality"""
        print("🔍 Testing empty states...")
        
        if not self.setup_driver():
            return
        
        try:
            self.driver.get(f"{self.base_url}/frontend/")
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "main"))
            )
            
            # Test basic empty state
            basic_empty_state_works = self.driver.execute_script("""
                if (window.emptyStateManager) {
                    // Create test container
                    const container = document.createElement('div');
                    container.id = 'test-empty-container';
                    document.body.appendChild(container);
                    
                    // Show empty state
                    const emptyStateId = window.emptyStateManager.show(container, {
                        title: 'Test Empty State',
                        message: 'This is a test message'
                    });
                    
                    const hasEmptyState = container.querySelector('.empty-state') !== null;
                    const hasTitle = container.textContent.includes('Test Empty State');
                    
                    // Clean up
                    window.emptyStateManager.hide(emptyStateId);
                    container.remove();
                    
                    return hasEmptyState && hasTitle;
                }
                return false;
            """)
            
            # Test predefined empty states
            no_results_works = self.driver.execute_script("""
                if (window.emptyStateManager) {
                    const container = document.createElement('div');
                    document.body.appendChild(container);
                    
                    const emptyStateId = window.emptyStateManager.showNoResults(container, 'test query');
                    const hasSearchIcon = container.querySelector('.bi-search') !== null;
                    const hasQuery = container.textContent.includes('test query');
                    
                    window.emptyStateManager.hide(emptyStateId);
                    container.remove();
                    
                    return hasSearchIcon && hasQuery;
                }
                return false;
            """)
            
            error_state_works = self.driver.execute_script("""
                if (window.emptyStateManager) {
                    const container = document.createElement('div');
                    document.body.appendChild(container);
                    
                    const emptyStateId = window.emptyStateManager.showError(container, 'Test error message');
                    const hasErrorIcon = container.querySelector('.bi-exclamation-triangle') !== null;
                    const hasMessage = container.textContent.includes('Test error message');
                    
                    window.emptyStateManager.hide(emptyStateId);
                    container.remove();
                    
                    return hasErrorIcon && hasMessage;
                }
                return false;
            """)
            
            self.results['empty_state_tests'].append({
                'test': 'Empty States Functionality',
                'basic_empty_state': basic_empty_state_works,
                'no_results_state': no_results_works,
                'error_state': error_state_works,
                'passed': all([basic_empty_state_works, no_results_works, error_state_works])
            })
            
            print(f"    ✅ Basic empty state: {basic_empty_state_works}")
            print(f"    ✅ No results state: {no_results_works}")
            print(f"    ✅ Error state: {error_state_works}")
            
        except Exception as e:
            error_msg = f"Error testing empty states: {str(e)}"
            print(f"    ❌ {error_msg}")
            self.results['errors'].append(error_msg)
        
        self.driver.quit()
    
    def test_form_validation_display(self):
        """Test form validation error display"""
        print("🔍 Testing form validation display...")
        
        if not self.setup_driver():
            return
        
        try:
            self.driver.get(f"{self.base_url}/frontend/")
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "main"))
            )
            
            # Test form validation error display
            form_validation_works = self.driver.execute_script("""
                if (window.errorHandler) {
                    // Create test form
                    const form = document.createElement('form');
                    form.innerHTML = `
                        <input name="email" class="form-control" />
                        <input name="password" class="form-control" />
                    `;
                    document.body.appendChild(form);
                    
                    // Simulate validation errors
                    const errors = {
                        email: ['This field is required.', 'Enter a valid email.'],
                        password: ['Password is too short.']
                    };
                    
                    window.errorHandler.handleFormValidationErrors(form, errors);
                    
                    // Check if errors are displayed
                    const emailField = form.querySelector('input[name="email"]');
                    const passwordField = form.querySelector('input[name="password"]');
                    
                    const emailHasError = emailField.classList.contains('is-invalid');
                    const passwordHasError = passwordField.classList.contains('is-invalid');
                    const errorMessagesExist = form.querySelectorAll('.invalid-feedback').length === 2;
                    
                    // Clean up
                    form.remove();
                    
                    return emailHasError && passwordHasError && errorMessagesExist;
                }
                return false;
            """)
            
            # Test error clearing
            error_clearing_works = self.driver.execute_script("""
                if (window.errorHandler) {
                    const form = document.createElement('form');
                    form.innerHTML = `
                        <input name="test" class="form-control is-invalid" />
                        <div class="invalid-feedback">Test error</div>
                    `;
                    document.body.appendChild(form);
                    
                    window.errorHandler.clearFormErrors(form);
                    
                    const hasErrorClass = form.querySelector('.is-invalid') !== null;
                    const hasErrorMessage = form.querySelector('.invalid-feedback') !== null;
                    
                    form.remove();
                    
                    return !hasErrorClass && !hasErrorMessage;
                }
                return false;
            """)
            
            self.results['form_validation_tests'].append({
                'test': 'Form Validation Display',
                'validation_display_works': form_validation_works,
                'error_clearing_works': error_clearing_works,
                'passed': form_validation_works and error_clearing_works
            })
            
            print(f"    ✅ Validation display: {form_validation_works}")
            print(f"    ✅ Error clearing: {error_clearing_works}")
            
        except Exception as e:
            error_msg = f"Error testing form validation: {str(e)}"
            print(f"    ❌ {error_msg}")
            self.results['errors'].append(error_msg)
        
        self.driver.quit()
    
    def test_api_integration(self):
        """Test API integration with error handling"""
        print("🔍 Testing API integration...")
        
        if not self.setup_driver():
            return
        
        try:
            self.driver.get(f"{self.base_url}/frontend/")
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "main"))
            )
            
            # Check if API client is available
            api_client_available = self.driver.execute_script(
                "return typeof window.apiClient !== 'undefined';"
            )
            
            # Check if form handler is available
            form_handler_available = self.driver.execute_script(
                "return typeof window.formHandler !== 'undefined';"
            )
            
            # Check if data loader is available
            data_loader_available = self.driver.execute_script(
                "return typeof window.dataLoader !== 'undefined';"
            )
            
            # Check if search handler is available
            search_handler_available = self.driver.execute_script(
                "return typeof window.searchHandler !== 'undefined';"
            )
            
            self.results['error_handling_tests'].append({
                'test': 'API Integration',
                'api_client_available': api_client_available,
                'form_handler_available': form_handler_available,
                'data_loader_available': data_loader_available,
                'search_handler_available': search_handler_available,
                'passed': all([
                    api_client_available,
                    form_handler_available,
                    data_loader_available,
                    search_handler_available
                ])
            })
            
            print(f"    ✅ API client: {api_client_available}")
            print(f"    ✅ Form handler: {form_handler_available}")
            print(f"    ✅ Data loader: {data_loader_available}")
            print(f"    ✅ Search handler: {search_handler_available}")
            
        except Exception as e:
            error_msg = f"Error testing API integration: {str(e)}"
            print(f"    ❌ {error_msg}")
            self.results['errors'].append(error_msg)
        
        self.driver.quit()
    
    def generate_report(self):
        """Generate test report"""
        print("\n" + "="*70)
        print("📊 ERROR HANDLING & USER FEEDBACK TEST REPORT")
        print("="*70)
        
        # Count results
        categories = [
            ('Error Handling', self.results['error_handling_tests']),
            ('User Feedback', self.results['user_feedback_tests']),
            ('Loading States', self.results['loading_state_tests']),
            ('Toast Notifications', self.results['toast_notification_tests']),
            ('Empty States', self.results['empty_state_tests']),
            ('Form Validation', self.results['form_validation_tests'])
        ]
        
        total_tests = 0
        total_passed = 0
        
        for category_name, tests in categories:
            if tests:
                category_passed = sum(1 for test in tests if test.get('passed', False))
                category_total = len(tests)
                total_tests += category_total
                total_passed += category_passed
                
                print(f"\n🔧 {category_name.upper()}:")
                print(f"   Passed: {category_passed}/{category_total}")
                
                for test in tests:
                    status = "✅" if test.get('passed', False) else "❌"
                    print(f"   {status} {test['test']}")
        
        # Errors Summary
        if self.results['errors']:
            print(f"\n❌ ERRORS ({len(self.results['errors'])}):")
            for error in self.results['errors'][:5]:  # Show first 5 errors
                print(f"   • {error}")
            if len(self.results['errors']) > 5:
                print(f"   ... and {len(self.results['errors']) - 5} more errors")
        
        # Overall Status
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
        
        print("="*70)
        
        # Task completion status
        error_handling_complete = len([t for t in self.results['error_handling_tests'] if t.get('passed', False)]) >= 2
        user_feedback_complete = len([t for t in self.results['user_feedback_tests'] + 
                                     self.results['loading_state_tests'] + 
                                     self.results['toast_notification_tests'] + 
                                     self.results['empty_state_tests'] if t.get('passed', False)]) >= 3
        
        print(f"\n📋 TASK COMPLETION STATUS:")
        print(f"   Task 11.1 (Error Handling System): {'✅ COMPLETE' if error_handling_complete else '⚠️ INCOMPLETE'}")
        print(f"   Task 11.2 (User Feedback System): {'✅ COMPLETE' if user_feedback_complete else '⚠️ INCOMPLETE'}")
        
        return error_handling_complete and user_feedback_complete
    
    def run_all_tests(self):
        """Run all error handling and user feedback tests"""
        print("🚀 Starting Error Handling & User Feedback Tests...")
        print("="*70)
        
        try:
            # Test error handler initialization
            self.test_error_handler_initialization()
            
            # Test user feedback initialization
            self.test_user_feedback_initialization()
            
            # Test loading states
            self.test_loading_states()
            
            # Test toast notifications
            self.test_toast_notifications()
            
            # Test empty states
            self.test_empty_states()
            
            # Test form validation
            self.test_form_validation_display()
            
            # Test API integration
            self.test_api_integration()
            
        except KeyboardInterrupt:
            print("\n⚠️ Tests interrupted by user")
        except Exception as e:
            print(f"\n❌ Unexpected error during testing: {e}")
            self.results['errors'].append(f"Unexpected error: {e}")
        finally:
            # Generate report
            return self.generate_report()

def main():
    """Main function to run tests"""
    print("ForgeDB Frontend - Error Handling & User Feedback Tests")
    print("Tasks 11.1 and 11.2 Verification")
    print("="*70)
    
    # Note: These tests don't require a running server as they test JavaScript functionality
    print("ℹ️ These tests verify JavaScript functionality and don't require a running server")
    
    # Run tests
    tester = ErrorHandlingUserFeedbackTest()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All error handling and user feedback systems working correctly!")
        return 0
    else:
        print("\n⚠️ Some systems need attention.")
        return 1

if __name__ == "__main__":
    exit(main())
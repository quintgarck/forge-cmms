#!/usr/bin/env python3
"""
Verification script for error handling and user feedback systems
ForgeDB Frontend - Tasks 11.1 and 11.2
"""

import os
import re
from pathlib import Path

class ErrorHandlingUserFeedbackVerifier:
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.results = {
            'error_handling_features': [],
            'user_feedback_features': [],
            'files_checked': [],
            'issues': []
        }
    
    def check_error_handler_js(self):
        """Check error handler JavaScript implementation"""
        print("🔍 Checking error handler JavaScript...")
        
        error_handler_path = self.base_path / 'static/frontend/js/error-handler.js'
        
        if not error_handler_path.exists():
            self.results['issues'].append("error-handler.js file not found")
            return
        
        with open(error_handler_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for error handler features
        error_handler_features = [
            (r'class ErrorHandler', 'ErrorHandler class'),
            (r'ERROR_TYPES\s*=', 'Error types constants'),
            (r'ERROR_SEVERITY\s*=', 'Error severity levels'),
            (r'handleError\s*\(', 'Error handling method'),
            (r'handleApiError\s*\(', 'API error handling'),
            (r'handleFormValidationErrors\s*\(', 'Form validation error handling'),
            (r'displayError\s*\(', 'Error display method'),
            (r'displayFieldError\s*\(', 'Field error display'),
            (r'clearFormErrors\s*\(', 'Error clearing method'),
            (r'attemptRecovery\s*\(', 'Error recovery mechanism'),
            (r'showSuccess\s*\(', 'Success message display'),
            (r'addEventListener.*error', 'Global error listeners'),
            (r'addEventListener.*unhandledrejection', 'Unhandled promise rejection handler'),
            (r'retryError\s*\(', 'Error retry functionality')
        ]
        
        for pattern, description in error_handler_features:
            if re.search(pattern, content, re.IGNORECASE):
                self.results['error_handling_features'].append(f"✅ {description}")
            else:
                self.results['issues'].append(f"❌ {description} missing")
        
        self.results['files_checked'].append('error-handler.js')
        print("    ✅ Error handler JavaScript checked")
    
    def check_user_feedback_js(self):
        """Check user feedback JavaScript implementation"""
        print("🔍 Checking user feedback JavaScript...")
        
        user_feedback_path = self.base_path / 'static/frontend/js/user-feedback.js'
        
        if not user_feedback_path.exists():
            self.results['issues'].append("user-feedback.js file not found")
            return
        
        with open(user_feedback_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for user feedback features
        user_feedback_features = [
            (r'class LoadingStateManager', 'Loading state manager'),
            (r'class ToastManager', 'Toast notification manager'),
            (r'class EmptyStateManager', 'Empty state manager'),
            (r'class ProgressIndicator', 'Progress indicator'),
            (r'class UserFeedback', 'Main user feedback class'),
            (r'showLoading\s*\(', 'Show loading method'),
            (r'hideLoading\s*\(', 'Hide loading method'),
            (r'showGlobalLoading\s*\(', 'Global loading display'),
            (r'showFormLoading\s*\(', 'Form loading states'),
            (r'createToast\s*\(', 'Toast creation method'),
            (r'success\s*\(.*options', 'Success toast method'),
            (r'error\s*\(.*options', 'Error toast method'),
            (r'warning\s*\(.*options', 'Warning toast method'),
            (r'info\s*\(.*options', 'Info toast method'),
            (r'createEmptyState\s*\(', 'Empty state creation'),
            (r'showNoResults\s*\(', 'No results empty state'),
            (r'showNoData\s*\(', 'No data empty state'),
            (r'showError\s*\(', 'Error empty state'),
            (r'showOffline\s*\(', 'Offline empty state'),
            (r'handleAsyncOperation\s*\(', 'Async operation handler'),
            (r'handleFormSubmission\s*\(', 'Form submission handler'),
            (r'handleDataLoad\s*\(', 'Data loading handler')
        ]
        
        for pattern, description in user_feedback_features:
            if re.search(pattern, content, re.IGNORECASE):
                self.results['user_feedback_features'].append(f"✅ {description}")
            else:
                self.results['issues'].append(f"❌ {description} missing")
        
        self.results['files_checked'].append('user-feedback.js')
        print("    ✅ User feedback JavaScript checked")
    
    def check_api_integration_js(self):
        """Check API integration JavaScript"""
        print("🔍 Checking API integration JavaScript...")
        
        api_integration_path = self.base_path / 'static/frontend/js/api-integration.js'
        
        if not api_integration_path.exists():
            self.results['issues'].append("api-integration.js file not found")
            return
        
        with open(api_integration_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for API integration features
        api_integration_features = [
            (r'class EnhancedAPIClient', 'Enhanced API client'),
            (r'class FormHandler', 'Form handler'),
            (r'class DataLoader', 'Data loader'),
            (r'class SearchHandler', 'Search handler'),
            (r'setupDefaultInterceptors\s*\(', 'Request/response interceptors'),
            (r'handleFormSubmit\s*\(', 'Form submission handling'),
            (r'displayFormErrors\s*\(', 'Form error display'),
            (r'loadElementData\s*\(', 'Element data loading'),
            (r'renderTemplate\s*\(', 'Template rendering'),
            (r'handleSearchInput\s*\(', 'Search input handling'),
            (r'performSearch\s*\(', 'Search execution'),
            (r'window\.apiClient', 'Global API client'),
            (r'window\.formHandler', 'Global form handler'),
            (r'window\.dataLoader', 'Global data loader'),
            (r'window\.searchHandler', 'Global search handler')
        ]
        
        for pattern, description in api_integration_features:
            if re.search(pattern, content, re.IGNORECASE):
                self.results['user_feedback_features'].append(f"✅ {description}")
            else:
                self.results['issues'].append(f"❌ {description} missing")
        
        self.results['files_checked'].append('api-integration.js')
        print("    ✅ API integration JavaScript checked")
    
    def check_user_feedback_css(self):
        """Check user feedback CSS styles"""
        print("🔍 Checking user feedback CSS...")
        
        user_feedback_css_path = self.base_path / 'static/frontend/css/user-feedback.css'
        
        if not user_feedback_css_path.exists():
            self.results['issues'].append("user-feedback.css file not found")
            return
        
        with open(user_feedback_css_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for CSS features
        css_features = [
            (r'\.global-loader', 'Global loader styles'),
            (r'\.error-container', 'Error container styles'),
            (r'\.toast-container', 'Toast container styles'),
            (r'\.loading-overlay', 'Loading overlay styles'),
            (r'\.empty-state', 'Empty state styles'),
            (r'\.progress-container', 'Progress indicator styles'),
            (r'\.invalid-feedback', 'Form validation styles'),
            (r'@keyframes.*slideIn', 'Slide in animations'),
            (r'@keyframes.*fadeIn', 'Fade in animations'),
            (r'@keyframes.*skeleton-loading', 'Skeleton loading animation'),
            (r'@media.*prefers-reduced-motion', 'Reduced motion support'),
            (r'@media.*prefers-contrast', 'High contrast support'),
            (r'@media.*max-width.*575', 'Mobile responsive styles'),
            (r'\.skeleton-loader', 'Skeleton loading styles'),
            (r'\.notification-badge', 'Notification badge styles'),
            (r'\.status-indicator', 'Status indicator styles')
        ]
        
        for pattern, description in css_features:
            if re.search(pattern, content, re.IGNORECASE):
                self.results['user_feedback_features'].append(f"✅ {description}")
            else:
                self.results['issues'].append(f"⚠️ {description} not found")
        
        self.results['files_checked'].append('user-feedback.css')
        print("    ✅ User feedback CSS checked")
    
    def check_base_template_integration(self):
        """Check base template integration"""
        print("🔍 Checking base template integration...")
        
        base_template_path = self.base_path / 'templates/frontend/base/base.html'
        
        if not base_template_path.exists():
            self.results['issues'].append("Base template not found")
            return
        
        with open(base_template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for template integration
        template_features = [
            (r'user-feedback\.css', 'User feedback CSS included'),
            (r'error-handler\.js', 'Error handler JS included'),
            (r'user-feedback\.js', 'User feedback JS included'),
            (r'api-integration\.js', 'API integration JS included'),
            (r'defer.*error-handler', 'Error handler deferred loading'),
            (r'defer.*user-feedback', 'User feedback deferred loading'),
            (r'defer.*api-integration', 'API integration deferred loading')
        ]
        
        for pattern, description in template_features:
            if re.search(pattern, content, re.IGNORECASE):
                self.results['user_feedback_features'].append(f"✅ Template: {description}")
            else:
                self.results['issues'].append(f"❌ Template: {description} missing")
        
        self.results['files_checked'].append('base.html')
        print("    ✅ Base template integration checked")
    
    def check_error_recovery_mechanisms(self):
        """Check error recovery mechanisms"""
        print("🔍 Checking error recovery mechanisms...")
        
        error_handler_path = self.base_path / 'static/frontend/js/error-handler.js'
        
        if not error_handler_path.exists():
            return
        
        with open(error_handler_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for recovery mechanisms
        recovery_features = [
            (r'handleAuthenticationRecovery\s*\(', 'Authentication recovery'),
            (r'handleNetworkRecovery\s*\(', 'Network recovery'),
            (r'scheduleRetry\s*\(', 'Retry scheduling'),
            (r'calculateRetryDelay\s*\(', 'Retry delay calculation'),
            (r'RETRY_STRATEGIES', 'Retry strategies'),
            (r'EXPONENTIAL_BACKOFF', 'Exponential backoff strategy'),
            (r'refreshToken', 'Token refresh mechanism'),
            (r'queueOfflineRequests', 'Offline request queuing'),
            (r'retryFailedRequests', 'Failed request retry')
        ]
        
        for pattern, description in recovery_features:
            if re.search(pattern, content, re.IGNORECASE):
                self.results['error_handling_features'].append(f"✅ Recovery: {description}")
            else:
                self.results['issues'].append(f"⚠️ Recovery: {description} not found")
        
        print("    ✅ Error recovery mechanisms checked")
    
    def check_accessibility_features(self):
        """Check accessibility features"""
        print("🔍 Checking accessibility features...")
        
        css_path = self.base_path / 'static/frontend/css/user-feedback.css'
        
        if not css_path.exists():
            return
        
        with open(css_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for accessibility features
        accessibility_features = [
            (r'aria-label', 'ARIA labels'),
            (r'role=', 'ARIA roles'),
            (r'visually-hidden', 'Screen reader text'),
            (r'focus.*outline', 'Focus indicators'),
            (r'prefers-reduced-motion', 'Reduced motion support'),
            (r'prefers-contrast', 'High contrast support'),
            (r'prefers-color-scheme', 'Dark mode support')
        ]
        
        for pattern, description in accessibility_features:
            if re.search(pattern, content, re.IGNORECASE):
                self.results['user_feedback_features'].append(f"✅ A11y: {description}")
        
        print("    ✅ Accessibility features checked")
    
    def generate_report(self):
        """Generate verification report"""
        print("\n" + "="*70)
        print("📊 ERROR HANDLING & USER FEEDBACK VERIFICATION REPORT")
        print("="*70)
        
        # Files checked
        print(f"\n📁 FILES CHECKED ({len(self.results['files_checked'])}):")
        for file in self.results['files_checked']:
            print(f"   ✅ {file}")
        
        # Error handling features
        print(f"\n🚨 ERROR HANDLING FEATURES ({len(self.results['error_handling_features'])}):")
        for feature in self.results['error_handling_features']:
            print(f"   {feature}")
        
        # User feedback features
        print(f"\n💬 USER FEEDBACK FEATURES ({len(self.results['user_feedback_features'])}):")
        for feature in self.results['user_feedback_features']:
            print(f"   {feature}")
        
        # Issues
        if self.results['issues']:
            print(f"\n⚠️ ISSUES FOUND ({len(self.results['issues'])}):")
            for issue in self.results['issues']:
                print(f"   {issue}")
        else:
            print(f"\n✅ NO CRITICAL ISSUES FOUND")
        
        # Summary
        total_features = len(self.results['error_handling_features']) + len(self.results['user_feedback_features'])
        total_issues = len(self.results['issues'])
        
        print(f"\n🎯 SUMMARY:")
        print(f"   Features Implemented: {total_features}")
        print(f"   Issues Found: {total_issues}")
        print(f"   Files Verified: {len(self.results['files_checked'])}")
        
        # Categorize issues
        critical_issues = len([i for i in self.results['issues'] if '❌' in i])
        warning_issues = len([i for i in self.results['issues'] if '⚠️' in i])
        
        print(f"   Critical Issues: {critical_issues}")
        print(f"   Warning Issues: {warning_issues}")
        
        if critical_issues == 0:
            if warning_issues <= 3:
                print(f"   Status: 🟢 EXCELLENT - All critical features implemented")
            else:
                print(f"   Status: 🟡 GOOD - Minor issues found")
        elif critical_issues <= 3:
            print(f"   Status: 🟠 NEEDS IMPROVEMENT - Some critical issues found")
        else:
            print(f"   Status: 🔴 CRITICAL - Many issues found")
        
        print("="*70)
        
        # Task completion status
        error_handling_complete = len([f for f in self.results['error_handling_features'] if '✅' in f]) >= 10
        user_feedback_complete = len([f for f in self.results['user_feedback_features'] if '✅' in f]) >= 20
        
        print(f"\n📋 TASK COMPLETION STATUS:")
        print(f"   Task 11.1 (Error Handling System): {'✅ COMPLETE' if error_handling_complete else '⚠️ INCOMPLETE'}")
        print(f"   Task 11.2 (User Feedback System): {'✅ COMPLETE' if user_feedback_complete else '⚠️ INCOMPLETE'}")
        
        return error_handling_complete and user_feedback_complete and critical_issues == 0
    
    def run_verification(self):
        """Run all verification checks"""
        print("🚀 Starting Error Handling & User Feedback Verification...")
        print("="*70)
        
        try:
            # Check all components
            self.check_error_handler_js()
            self.check_user_feedback_js()
            self.check_api_integration_js()
            self.check_user_feedback_css()
            self.check_base_template_integration()
            self.check_error_recovery_mechanisms()
            self.check_accessibility_features()
            
        except Exception as e:
            print(f"\n❌ Unexpected error during verification: {e}")
            self.results['issues'].append(f"Verification error: {e}")
        
        # Generate report
        return self.generate_report()

def main():
    """Main function"""
    print("ForgeDB Frontend - Error Handling & User Feedback Verification")
    print("Tasks 11.1 and 11.2 Implementation Check")
    print("="*70)
    
    verifier = ErrorHandlingUserFeedbackVerifier()
    success = verifier.run_verification()
    
    if success:
        print("\n🎉 All error handling and user feedback systems successfully implemented!")
        return 0
    else:
        print("\n⚠️ Some systems need attention.")
        return 1

if __name__ == "__main__":
    exit(main())
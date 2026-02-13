#!/usr/bin/env python3
"""
Verification script for responsive design and performance optimizations
ForgeDB Frontend - Tasks 10.1 and 10.2
"""

import os
import re
from pathlib import Path

class ResponsivePerformanceVerifier:
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.results = {
            'responsive_features': [],
            'performance_features': [],
            'files_checked': [],
            'issues': []
        }
    
    def check_responsive_css(self):
        """Check responsive CSS implementation"""
        print("🔍 Checking responsive CSS implementation...")
        
        responsive_css_path = self.base_path / 'static/frontend/css/responsive.css'
        
        if not responsive_css_path.exists():
            self.results['issues'].append("responsive.css file not found")
            return
        
        with open(responsive_css_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for responsive breakpoints
        breakpoints = [
            r'@media.*max-width:\s*575\.98px',  # Mobile
            r'@media.*min-width:\s*576px.*max-width:\s*767\.98px',  # Small tablets
            r'@media.*min-width:\s*768px.*max-width:\s*991\.98px',  # Tablets
            r'@media.*min-width:\s*992px.*max-width:\s*1199\.98px',  # Desktop
            r'@media.*min-width:\s*1200px'  # Large desktop
        ]
        
        breakpoint_names = ['Mobile', 'Small Tablet', 'Tablet', 'Desktop', 'Large Desktop']
        
        for i, pattern in enumerate(breakpoints):
            if re.search(pattern, content, re.IGNORECASE):
                self.results['responsive_features'].append(f"✅ {breakpoint_names[i]} breakpoint implemented")
            else:
                self.results['issues'].append(f"❌ {breakpoint_names[i]} breakpoint missing")
        
        # Check for touch-friendly elements
        touch_features = [
            (r'min-height:\s*44px', 'Touch target minimum height (44px)'),
            (r'font-size:\s*16px.*iOS', 'iOS zoom prevention (16px font)'),
            (r'touch-friendly', 'Touch-friendly interface elements'),
            (r'btn-group-mobile', 'Mobile button group optimization'),
            (r'table-stack', 'Mobile table stacking')
        ]
        
        for pattern, description in touch_features:
            if re.search(pattern, content, re.IGNORECASE):
                self.results['responsive_features'].append(f"✅ {description}")
            else:
                self.results['issues'].append(f"⚠️ {description} not found")
        
        # Check for mobile navigation patterns
        mobile_nav_features = [
            (r'navbar-collapse', 'Collapsible navigation'),
            (r'navbar-toggler', 'Mobile menu toggle'),
            (r'dropdown-menu.*mobile', 'Mobile dropdown optimization')
        ]
        
        for pattern, description in mobile_nav_features:
            if re.search(pattern, content, re.IGNORECASE):
                self.results['responsive_features'].append(f"✅ {description}")
        
        self.results['files_checked'].append('responsive.css')
        print("    ✅ Responsive CSS checked")
    
    def check_performance_js(self):
        """Check performance JavaScript implementation"""
        print("🔍 Checking performance JavaScript implementation...")
        
        performance_js_path = self.base_path / 'static/frontend/js/performance.js'
        
        if not performance_js_path.exists():
            self.results['issues'].append("performance.js file not found")
            return
        
        with open(performance_js_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for lazy loading implementation
        lazy_loading_features = [
            (r'class LazyLoader', 'LazyLoader class'),
            (r'IntersectionObserver', 'Intersection Observer API'),
            (r'data-src', 'Lazy image loading'),
            (r'data-lazy-content', 'Lazy content loading')
        ]
        
        for pattern, description in lazy_loading_features:
            if re.search(pattern, content, re.IGNORECASE):
                self.results['performance_features'].append(f"✅ {description}")
            else:
                self.results['issues'].append(f"❌ {description} missing")
        
        # Check for caching implementation
        caching_features = [
            (r'class CacheManager', 'Cache Manager class'),
            (r'class APICache', 'API Cache class'),
            (r'fetchWithCache', 'Cached fetch implementation'),
            (r'maxAge.*minutes', 'Cache expiration')
        ]
        
        for pattern, description in caching_features:
            if re.search(pattern, content, re.IGNORECASE):
                self.results['performance_features'].append(f"✅ {description}")
            else:
                self.results['issues'].append(f"❌ {description} missing")
        
        # Check for image optimization
        image_optimization_features = [
            (r'class ImageOptimizer', 'Image Optimizer class'),
            (r'webpSupported', 'WebP support detection'),
            (r'loading.*lazy', 'Native lazy loading'),
            (r'decoding.*async', 'Async image decoding')
        ]
        
        for pattern, description in image_optimization_features:
            if re.search(pattern, content, re.IGNORECASE):
                self.results['performance_features'].append(f"✅ {description}")
            else:
                self.results['issues'].append(f"❌ {description} missing")
        
        # Check for performance monitoring
        monitoring_features = [
            (r'class PerformanceMonitor', 'Performance Monitor class'),
            (r'PerformanceObserver', 'Performance Observer API'),
            (r'first-contentful-paint', 'First Contentful Paint tracking'),
            (r'largest-contentful-paint', 'Largest Contentful Paint tracking')
        ]
        
        for pattern, description in monitoring_features:
            if re.search(pattern, content, re.IGNORECASE):
                self.results['performance_features'].append(f"✅ {description}")
            else:
                self.results['issues'].append(f"❌ {description} missing")
        
        # Check for utility functions
        utility_features = [
            (r'function debounce', 'Debounce utility'),
            (r'function throttle', 'Throttle utility'),
            (r'initializeResponsiveTables', 'Responsive table initialization'),
            (r'initializeMobileOptimizations', 'Mobile optimizations')
        ]
        
        for pattern, description in utility_features:
            if re.search(pattern, content, re.IGNORECASE):
                self.results['performance_features'].append(f"✅ {description}")
        
        self.results['files_checked'].append('performance.js')
        print("    ✅ Performance JavaScript checked")
    
    def check_service_worker(self):
        """Check service worker implementation"""
        print("🔍 Checking service worker implementation...")
        
        sw_path = self.base_path / 'static/frontend/js/sw.js'
        
        if not sw_path.exists():
            self.results['issues'].append("Service worker file not found")
            return
        
        with open(sw_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for service worker features
        sw_features = [
            (r'CACHE_NAME', 'Cache naming'),
            (r'STATIC_CACHE', 'Static asset caching'),
            (r'DYNAMIC_CACHE', 'Dynamic content caching'),
            (r'addEventListener.*install', 'Install event handler'),
            (r'addEventListener.*activate', 'Activate event handler'),
            (r'addEventListener.*fetch', 'Fetch event handler'),
            (r'caches\.open', 'Cache API usage'),
            (r'cache\.addAll', 'Bulk cache addition')
        ]
        
        for pattern, description in sw_features:
            if re.search(pattern, content, re.IGNORECASE):
                self.results['performance_features'].append(f"✅ Service Worker: {description}")
            else:
                self.results['issues'].append(f"❌ Service Worker: {description} missing")
        
        self.results['files_checked'].append('sw.js')
        print("    ✅ Service Worker checked")
    
    def check_base_template(self):
        """Check base template optimizations"""
        print("🔍 Checking base template optimizations...")
        
        base_template_path = self.base_path / 'templates/frontend/base/base.html'
        
        if not base_template_path.exists():
            self.results['issues'].append("Base template not found")
            return
        
        with open(base_template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for performance optimizations in template
        template_features = [
            (r'rel="preconnect"', 'DNS preconnect'),
            (r'rel="dns-prefetch"', 'DNS prefetch'),
            (r'rel="preload"', 'Resource preloading'),
            (r'rel="prefetch"', 'Resource prefetching'),
            (r'media="print".*onload', 'Async CSS loading'),
            (r'loading="lazy"', 'Native lazy loading'),
            (r'async.*defer', 'Async/defer script loading'),
            (r'serviceWorker\.register', 'Service worker registration'),
            (r'critical.*css', 'Critical CSS inlining'),
            (r'viewport.*width=device-width', 'Responsive viewport')
        ]
        
        for pattern, description in template_features:
            if re.search(pattern, content, re.IGNORECASE):
                self.results['performance_features'].append(f"✅ Template: {description}")
            else:
                self.results['issues'].append(f"⚠️ Template: {description} not found")
        
        # Check for responsive features in template
        responsive_template_features = [
            (r'navbar-toggler', 'Mobile navigation toggle'),
            (r'collapse.*navbar', 'Collapsible navigation'),
            (r'dropdown-menu', 'Dropdown menus'),
            (r'table-responsive', 'Responsive tables'),
            (r'modal.*responsive', 'Responsive modals')
        ]
        
        for pattern, description in responsive_template_features:
            if re.search(pattern, content, re.IGNORECASE):
                self.results['responsive_features'].append(f"✅ Template: {description}")
        
        self.results['files_checked'].append('base.html')
        print("    ✅ Base template checked")
    
    def check_performance_css(self):
        """Check performance-specific CSS"""
        print("🔍 Checking performance CSS optimizations...")
        
        perf_css_path = self.base_path / 'static/frontend/css/performance-optimizations.css'
        
        if not perf_css_path.exists():
            self.results['issues'].append("performance-optimizations.css file not found")
            return
        
        with open(perf_css_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for performance CSS features
        perf_css_features = [
            (r'contain:\s*layout', 'CSS containment for layout'),
            (r'will-change:', 'Will-change optimization'),
            (r'transform:\s*translateZ\(0\)', 'GPU acceleration'),
            (r'font-display:\s*swap', 'Font loading optimization'),
            (r'content-visibility:\s*auto', 'Content visibility optimization'),
            (r'@media.*prefers-reduced-motion', 'Reduced motion support'),
            (r'@media.*prefers-contrast', 'High contrast support'),
            (r'skeleton-loading', 'Skeleton loading animation'),
            (r'background-size:\s*200%', 'Optimized loading animation')
        ]
        
        for pattern, description in perf_css_features:
            if re.search(pattern, content, re.IGNORECASE):
                self.results['performance_features'].append(f"✅ CSS: {description}")
            else:
                self.results['issues'].append(f"⚠️ CSS: {description} not found")
        
        self.results['files_checked'].append('performance-optimizations.css')
        print("    ✅ Performance CSS checked")
    
    def check_manifest(self):
        """Check PWA manifest"""
        print("🔍 Checking PWA manifest...")
        
        manifest_path = self.base_path / 'static/frontend/manifest.json'
        
        if not manifest_path.exists():
            self.results['issues'].append("PWA manifest not found")
            return
        
        try:
            import json
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            # Check required manifest fields
            required_fields = ['name', 'short_name', 'start_url', 'display', 'theme_color', 'background_color']
            
            for field in required_fields:
                if field in manifest:
                    self.results['performance_features'].append(f"✅ PWA: {field} defined")
                else:
                    self.results['issues'].append(f"❌ PWA: {field} missing from manifest")
            
            # Check for icons
            if 'icons' in manifest and len(manifest['icons']) > 0:
                self.results['performance_features'].append(f"✅ PWA: {len(manifest['icons'])} icons defined")
            else:
                self.results['issues'].append("❌ PWA: No icons defined")
            
        except json.JSONDecodeError:
            self.results['issues'].append("❌ PWA: Invalid JSON in manifest")
        
        self.results['files_checked'].append('manifest.json')
        print("    ✅ PWA manifest checked")
    
    def generate_report(self):
        """Generate verification report"""
        print("\n" + "="*70)
        print("📊 RESPONSIVE DESIGN & PERFORMANCE VERIFICATION REPORT")
        print("="*70)
        
        # Files checked
        print(f"\n📁 FILES CHECKED ({len(self.results['files_checked'])}):")
        for file in self.results['files_checked']:
            print(f"   ✅ {file}")
        
        # Responsive features
        print(f"\n🎨 RESPONSIVE DESIGN FEATURES ({len(self.results['responsive_features'])}):")
        for feature in self.results['responsive_features']:
            print(f"   {feature}")
        
        # Performance features
        print(f"\n⚡ PERFORMANCE FEATURES ({len(self.results['performance_features'])}):")
        for feature in self.results['performance_features']:
            print(f"   {feature}")
        
        # Issues
        if self.results['issues']:
            print(f"\n⚠️ ISSUES FOUND ({len(self.results['issues'])}):")
            for issue in self.results['issues']:
                print(f"   {issue}")
        else:
            print(f"\n✅ NO ISSUES FOUND")
        
        # Summary
        total_features = len(self.results['responsive_features']) + len(self.results['performance_features'])
        total_issues = len(self.results['issues'])
        
        print(f"\n🎯 SUMMARY:")
        print(f"   Features Implemented: {total_features}")
        print(f"   Issues Found: {total_issues}")
        print(f"   Files Verified: {len(self.results['files_checked'])}")
        
        if total_issues == 0:
            print(f"   Status: 🟢 EXCELLENT - All optimizations implemented")
        elif total_issues <= 3:
            print(f"   Status: 🟡 GOOD - Minor issues found")
        elif total_issues <= 6:
            print(f"   Status: 🟠 NEEDS IMPROVEMENT - Several issues found")
        else:
            print(f"   Status: 🔴 CRITICAL - Many issues found")
        
        print("="*70)
        
        # Task completion status
        responsive_complete = len([f for f in self.results['responsive_features'] if '✅' in f]) >= 8
        performance_complete = len([f for f in self.results['performance_features'] if '✅' in f]) >= 15
        
        print(f"\n📋 TASK COMPLETION STATUS:")
        print(f"   Task 10.1 (Responsive Breakpoints): {'✅ COMPLETE' if responsive_complete else '⚠️ INCOMPLETE'}")
        print(f"   Task 10.2 (Performance Optimization): {'✅ COMPLETE' if performance_complete else '⚠️ INCOMPLETE'}")
        
        return responsive_complete and performance_complete
    
    def run_verification(self):
        """Run all verification checks"""
        print("🚀 Starting Responsive Design & Performance Verification...")
        print("="*70)
        
        try:
            # Check all components
            self.check_responsive_css()
            self.check_performance_js()
            self.check_service_worker()
            self.check_base_template()
            self.check_performance_css()
            self.check_manifest()
            
        except Exception as e:
            print(f"\n❌ Unexpected error during verification: {e}")
            self.results['issues'].append(f"Verification error: {e}")
        
        # Generate report
        return self.generate_report()

def main():
    """Main function"""
    print("ForgeDB Frontend - Responsive Design & Performance Verification")
    print("Tasks 10.1 and 10.2 Implementation Check")
    print("="*70)
    
    verifier = ResponsivePerformanceVerifier()
    success = verifier.run_verification()
    
    if success:
        print("\n🎉 All optimizations successfully implemented!")
        return 0
    else:
        print("\n⚠️ Some optimizations need attention.")
        return 1

if __name__ == "__main__":
    exit(main())
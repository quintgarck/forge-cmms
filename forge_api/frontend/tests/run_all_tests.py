"""
Script to run all frontend tests and generate a checkpoint report.

This script runs all frontend tests and generates a comprehensive report
on test coverage and status.
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')
django.setup()

from django.test.utils import get_runner
from django.conf import settings
import subprocess


def run_tests():
    """Run all frontend tests and return results."""
    print("=" * 80)
    print("FORGEDB FRONTEND - TEST CHECKPOINT")
    print("=" * 80)
    print()
    
    test_modules = [
        'frontend.tests.test_unit_views',
        'frontend.tests.test_integration_e2e',
        'frontend.tests.test_services_basic',
        'frontend.tests.test_dashboard_integration',
        'frontend.tests.test_property_dashboard_completeness',
        'frontend.tests.test_property_form_validation',
        'frontend.tests.test_property_navigation_consistency',
    ]
    
    print("Running frontend tests...")
    print("-" * 80)
    
    # Run tests using Django test runner
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, keepdb=False)
    
    failures = test_runner.run_tests(test_modules)
    
    print()
    print("=" * 80)
    print("TEST RESULTS SUMMARY")
    print("=" * 80)
    
    if failures:
        print(f"❌ {failures} test(s) failed")
        return False
    else:
        print("✅ All tests passed!")
        return True


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)


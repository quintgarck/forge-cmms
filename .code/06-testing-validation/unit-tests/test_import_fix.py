#!/usr/bin/env python
"""
Test script to verify that the import issues have been resolved.
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')
django.setup()

def test_imports():
    """Test that all the problematic imports now work."""
    print("Testing import fixes...")
    
    try:
        # Test the main problematic import
        from frontend.views import ClientCreateView
        print("✓ ClientCreateView imported successfully")
        
        # Test other client views
        from frontend.views import ClientListView, ClientDetailView, ClientUpdateView, ClientDeleteView
        print("✓ All client views imported successfully")
        
        # Test that the views are actually classes
        assert hasattr(ClientCreateView, 'get_context_data'), "ClientCreateView should have get_context_data method"
        assert hasattr(ClientCreateView, 'post'), "ClientCreateView should have post method"
        print("✓ ClientCreateView has expected methods")
        
        # Test that we can instantiate the view
        view = ClientCreateView()
        print("✓ ClientCreateView can be instantiated")
        
        print("\n🎉 All import tests passed! The module import error has been fixed.")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_form_imports():
    """Test that form imports work correctly."""
    print("\nTesting form imports...")
    
    try:
        # Test direct import from main forms module
        from frontend.forms import ClientForm
        print("✓ ClientForm imported successfully from frontend.forms")
        
        # Test that the form is actually a form class
        assert hasattr(ClientForm, 'is_valid'), "ClientForm should have is_valid method"
        print("✓ ClientForm has expected methods")
        
        # Test that we can instantiate the form
        form = ClientForm()
        print("✓ ClientForm can be instantiated")
        
        return True
        
    except ImportError as e:
        print(f"❌ Form import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected form error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("IMPORT FIX VERIFICATION TEST")
    print("=" * 60)
    
    success = True
    
    # Test view imports
    if not test_imports():
        success = False
    
    # Test form imports
    if not test_form_imports():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 ALL TESTS PASSED - Import issues have been resolved!")
        print("The ModuleNotFoundError for frontend.views.client_views should be fixed.")
    else:
        print("❌ SOME TESTS FAILED - Import issues still exist.")
    print("=" * 60)
    
    sys.exit(0 if success else 1)
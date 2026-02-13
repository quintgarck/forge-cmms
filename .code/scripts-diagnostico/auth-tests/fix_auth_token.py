#!/usr/bin/env python
"""
Quick fix for authentication token issues.
This script helps resolve JWT token and session problems.
"""
import os
import sys
import django

# Setup Django environment first
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.utils import timezone
from datetime import datetime, timedelta

def fix_authentication_issues():
    """Fix common authentication issues."""
    print("🔧 Fixing Authentication Issues")
    print("=" * 50)
    
    # Step 1: Clear expired sessions
    print("\n1. Clearing expired sessions...")
    expired_sessions = Session.objects.filter(expire_date__lt=timezone.now())
    expired_count = expired_sessions.count()
    expired_sessions.delete()
    print(f"   ✅ Cleared {expired_count} expired sessions")
    
    # Step 2: Ensure demo user exists and is active
    print("\n2. Checking demo user...")
    try:
        user = User.objects.get(username='demo')
        if not user.is_active:
            user.is_active = True
            user.save()
            print("   ✅ Activated demo user")
        else:
            print("   ✅ Demo user is active")
    except User.DoesNotExist:
        user = User.objects.create_user(
            username='demo',
            password='demo123',
            email='demo@example.com',
            is_active=True
        )
        print("   ✅ Created new demo user")
    
    # Step 3: Create admin user if needed
    print("\n3. Checking admin user...")
    try:
        admin = User.objects.get(username='admin')
        if not admin.is_active:
            admin.is_active = True
            admin.save()
            print("   ✅ Activated admin user")
        else:
            print("   ✅ Admin user is active")
    except User.DoesNotExist:
        admin = User.objects.create_superuser(
            username='admin',
            password='admin123',
            email='admin@example.com'
        )
        print("   ✅ Created new admin user")
    
    # Step 4: Create test user if needed
    print("\n4. Checking test user...")
    try:
        test_user = User.objects.get(username='testuser')
        if not test_user.is_active:
            test_user.is_active = True
            test_user.save()
            print("   ✅ Activated test user")
        else:
            print("   ✅ Test user is active")
    except User.DoesNotExist:
        test_user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='testuser@example.com',
            is_active=True
        )
        print("   ✅ Created new test user")
    
    return True

def create_debug_auth_view():
    """Create a simple debug view for authentication."""
    print("\n5. Creating debug authentication info...")
    
    debug_info = {
        'users': [],
        'sessions': Session.objects.count(),
        'active_sessions': Session.objects.filter(expire_date__gt=timezone.now()).count()
    }
    
    for user in User.objects.all():
        debug_info['users'].append({
            'username': user.username,
            'email': user.email,
            'is_active': user.is_active,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'last_login': user.last_login.isoformat() if user.last_login else None,
            'date_joined': user.date_joined.isoformat()
        })
    
    print(f"   ✅ Found {len(debug_info['users'])} users")
    print(f"   ✅ {debug_info['active_sessions']} active sessions out of {debug_info['sessions']} total")
    
    return debug_info

def main():
    """Run authentication fixes."""
    print("🔐 ForgeDB Authentication Fix Tool")
    print("Fixing authentication and session issues...")
    
    try:
        fix_authentication_issues()
        debug_info = create_debug_auth_view()
        
        print("\n" + "=" * 50)
        print("🎯 Authentication Fix Completed!")
        print("\n✅ Available Users:")
        for user_info in debug_info['users']:
            status = "🟢" if user_info['is_active'] else "🔴"
            role = "👑" if user_info['is_superuser'] else "👤"
            print(f"   {status} {role} {user_info['username']} ({user_info['email']})")
        
        print("\n🔑 Login Credentials:")
        print("   • Admin: admin / admin123")
        print("   • Demo: demo / demo123") 
        print("   • Test: testuser / testpass123")
        
        print("\n💡 Next Steps:")
        print("   1. Go to http://localhost:8000/login/")
        print("   2. Login with any of the above credentials")
        print("   3. Try creating a client again")
        print("   4. If issues persist, check the server logs")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Fix failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
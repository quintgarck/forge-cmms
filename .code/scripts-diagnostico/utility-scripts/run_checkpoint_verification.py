#!/usr/bin/env python
"""
ForgeDB API REST - Checkpoint Verification Script
Task 6: Checkpoint - Ensure all tests pass

This script provides a quick verification of system health and test status.
Run this script to verify that all tests are passing and the system is healthy.
"""
import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner
from django.core.management import execute_from_command_line


def run_checkpoint_verification():
    """Run checkpoint verification and provide summary report"""
    print("=" * 80)
    print("🔍 ForgeDB API REST - Checkpoint Verification")
    print("=" * 80)
    
    # Set up Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')
    django.setup()
    
    print("\n📋 Running comprehensive test suite...")
    
    # Run all tests
    result = os.system('python manage.py test --verbosity=1')
    
    print("\n" + "=" * 80)
    if result == 0:
        print("✅ CHECKPOINT VERIFICATION PASSED")
        print("🎉 All tests are passing - System is healthy!")
        print("🚀 Ready for production deployment")
    else:
        print("❌ CHECKPOINT VERIFICATION FAILED")
        print("⚠️  Some tests are failing - System needs attention")
        print("🔧 Please review test failures and fix issues")
    
    print("=" * 80)
    
    # System health check
    print("\n🏥 System Health Check:")
    try:
        # Check database connectivity
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        print("✅ Database connectivity: OK")
    except Exception as e:
        print(f"❌ Database connectivity: ERROR - {str(e)}")
        result = 1
    
    try:
        # Check model integrity
        from core.models import Technician, Client, Equipment
        tech_count = Technician.objects.count()
        client_count = Client.objects.count()
        equipment_count = Equipment.objects.count()
        print(f"✅ Model integrity: OK (Technicians: {tech_count}, Clients: {client_count}, Equipment: {equipment_count})")
    except Exception as e:
        print(f"❌ Model integrity: ERROR - {str(e)}")
        result = 1
    
    try:
        # Check serializer imports
        from core.serializers import (
            TechnicianSerializer, ClientSerializer, EquipmentSerializer,
            WorkOrderSerializer, InvoiceSerializer
        )
        print("✅ Serializer imports: OK")
    except Exception as e:
        print(f"❌ Serializer imports: ERROR - {str(e)}")
        result = 1
    
    # Final status
    print("\n" + "=" * 80)
    if result == 0:
        print("🎯 FINAL STATUS: SYSTEM HEALTHY")
        print("✅ All checkpoints passed")
        print("🚀 Ready for next development phase")
    else:
        print("⚠️  FINAL STATUS: SYSTEM NEEDS ATTENTION")
        print("❌ Some checkpoints failed")
        print("🔧 Please address issues before proceeding")
    print("=" * 80)
    
    return result == 0


if __name__ == "__main__":
    success = run_checkpoint_verification()
    sys.exit(0 if success else 1)
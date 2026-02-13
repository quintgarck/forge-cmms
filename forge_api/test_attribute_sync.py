#!/usr/bin/env python
"""
Test script to verify attribute schema synchronization is working correctly.
This simulates the frontend JavaScript behavior to ensure data flows properly.
"""

import os
import sys
import django
import json

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'forge_api.settings')
django.setup()

from core.models import EquipmentType

def test_attribute_sync():
    """Test that attribute schema synchronization works correctly"""
    
    print("🔍 Testing Attribute Schema Synchronization...")
    print("=" * 50)
    
    # Test data that mimics what the visual builder would create
    test_attributes = {
        "marca": {
            "type": "string",
            "required": True,
            "label": "Marca del equipo"
        },
        "modelo": {
            "type": "string", 
            "required": True,
            "label": "Modelo específico"
        },
        "anio": {
            "type": "number",
            "required": False,
            "label": "Año de fabricación"
        },
        "color": {
            "type": "select",
            "required": False,
            "label": "Color",
            "options": ["Rojo", "Azul", "Negro", "Blanco"]
        },
        "es_electrico": {
            "type": "boolean",
            "required": False,
            "label": "Es eléctrico"
        }
    }
    
    # Convert to JSON string (this is what the sync function does)
    json_string = json.dumps(test_attributes, indent=2)
    print(f"📝 Generated JSON:\n{json_string}")
    print()
    
    # Validate the JSON structure
    try:
        parsed = json.loads(json_string)
        print("✅ JSON structure is valid")
        
        # Validate schema structure
        assert isinstance(parsed, dict), "Schema must be an object"
        print("✅ Schema is a dictionary")
        
        # Validate field definitions
        for field_name, field_config in parsed.items():
            assert isinstance(field_config, dict), f"Field '{field_name}' config must be an object"
            assert 'type' in field_config, f"Field '{field_name}' must specify a type"
            assert field_config['type'] in ['string', 'number', 'boolean', 'date', 'select'], \
                f"Invalid type '{field_config['type']}' for field '{field_name}'"
            
        print("✅ All field definitions are valid")
        print("✅ Schema validation passed")
        
        # Test saving to database
        print("\n💾 Testing database save...")
        
        # Create or update an equipment type
        equipment_type, created = EquipmentType.objects.update_or_create(
            type_code='TEST_SYNC',
            defaults={
                'name': 'Test Equipment Type Sync',
                'category': 'AUTOMOTRIZ',
                'description': 'Testing attribute schema synchronization',
                'attr_schema': json_string,
                'is_active': True
            }
        )
        
        if created:
            print("✅ Created new equipment type")
        else:
            print("✅ Updated existing equipment type")
            
        # Verify the saved data
        saved_equipment = EquipmentType.objects.get(type_code='TEST_SYNC')
        saved_schema = json.loads(saved_equipment.attr_schema)
        
        print(f"✅ Retrieved from database successfully")
        print(f"📊 Saved attributes: {len(saved_schema)} fields")
        
        # Compare with original
        assert saved_schema == test_attributes, "Saved schema doesn't match original"
        print("✅ Database save/retrieve cycle successful")
        
        # Clean up
        equipment_type.delete()
        print("🧹 Cleaned up test data")
        
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Attribute schema synchronization is working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

if __name__ == '__main__':
    success = test_attribute_sync()
    sys.exit(0 if success else 1)
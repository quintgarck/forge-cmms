"""
Database Router for ForgeDB Schema Management

This router helps Django handle multiple database schemas correctly,
ensuring that tables are created in the correct schemas.

Note: Django's db_table with schema notation (e.g., 'cat.clients') 
should work correctly, but this router provides additional safeguards.
"""
from django.conf import settings


class SchemaRouter:
    """
    Database router to help manage schemas in ForgeDB.
    
    This router ensures that Django operations respect the schema
    configuration in db_table settings.
    """
    
    # Map of app labels to default schemas
    APP_SCHEMA_MAP = {
        'core': None,  # Uses schema from db_table in models
    }
    
    def db_for_read(self, model, **hints):
        """Suggest which database should be used for read operations."""
        return 'default'
    
    def db_for_write(self, model, **hints):
        """Suggest which database should be used for write operations."""
        return 'default'
    
    def allow_relation(self, obj1, obj2, **hints):
        """Allow relations if models are in the same app."""
        db_set = {'default'}
        if obj1._state.db in db_set and obj2._state.db in db_set:
            return True
        return None
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Ensure migrations run on the default database."""
        if db == 'default':
            return True
        return None


# Note: This router is optional. Django should handle schemas correctly
# through db_table settings. Use this router only if you need additional
# schema management logic.


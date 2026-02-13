from django.apps import AppConfig


class CoreConfig(AppConfig):
    """
    Configuration for the Core app.
    
    This app contains the main models, views, and business logic
    for the ForgeDB API REST system.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'ForgeDB Core'
    
    def ready(self):
        """
        Perform initialization tasks when the app is ready.
        """
        # Import signal handlers
        try:
            import core.signals  # noqa
        except ImportError:
            pass
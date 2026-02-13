from django.apps import AppConfig


class FrontendConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'frontend'
    verbose_name = 'ForgeDB Frontend'
    
    def ready(self):
        """Initialize frontend app when Django starts."""
        pass
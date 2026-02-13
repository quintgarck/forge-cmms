"""
Mixins for frontend views.
"""
import logging
from django.contrib import messages
from .services.api_client import ForgeAPIClient, APIException

logger = logging.getLogger(__name__)


class APIClientMixin:
    """Mixin to provide API client functionality to views."""
    
    @property
    def api_client(self):
        """Get an API client instance configured for the current request."""
        return ForgeAPIClient(request=self.request)
    
    def get_api_client(self):
        """Get an API client instance configured for the current request."""
        return ForgeAPIClient(request=self.request)
    
    def _get_page_number(self):
        """Get the current page number from request parameters."""
        try:
            return int(self.request.GET.get('page', 1))
        except (ValueError, TypeError):
            return 1
    
    def _get_page_range(self, current_page, total_pages, window=5):
        """Generate a smart page range for pagination."""
        if total_pages <= window:
            return list(range(1, total_pages + 1))
        
        half_window = window // 2
        start = max(1, current_page - half_window)
        end = min(total_pages, current_page + half_window)
        
        if end - start < window - 1:
            if start == 1:
                end = min(total_pages, start + window - 1)
            else:
                start = max(1, end - window + 1)
        
        return list(range(start, end + 1))
    
    def handle_api_error(self, error: APIException, default_message: str = "Error en la operación"):
        """Handle API errors and display appropriate messages."""
        if error.status_code == 401:
            # Authentication errors - clear session and show message
            messages.error(self.request, "Sesión expirada. Por favor, inicie sesión nuevamente.")
            # Don't redirect here - let the view handle it after showing the message
        elif error.status_code == 400 and error.response_data:
            # Validation errors
            error_messages = []
            for field, errors in error.response_data.items():
                if isinstance(errors, list):
                    error_messages.extend(errors)
                else:
                    error_messages.append(str(errors))

            if error_messages:
                for msg in error_messages:
                    messages.error(self.request, msg)
            else:
                messages.error(self.request, error.message)
        else:
            messages.error(self.request, error.message or default_message)
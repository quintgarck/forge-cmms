"""
View mixins for ForgeDB frontend.
"""
from django.contrib import messages
import logging

from .services import ForgeAPIClient
from .services.api_client import APIException


logger = logging.getLogger(__name__)


class APIClientMixin:
    """Mixin to provide API client functionality to views."""
    
    def get_api_client(self):
        """Get an API client instance for this request."""
        return ForgeAPIClient(request=self.request)
    
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

"""
Authentication-related frontend views for ForgeDB.
"""
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.generic import TemplateView
from django.views import View
import logging

from .services import AuthenticationService


logger = logging.getLogger(__name__)


class LoginView(TemplateView):
    """User login view."""
    template_name = 'frontend/auth/login.html'
    
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('frontend:dashboard')
        return render(request, self.template_name)
    
    def post(self, request, *args, **kwargs):
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        auth_service = AuthenticationService(request)
        
        try:
            success, message, user_data = auth_service.login(username, password)
            
            if success:
                messages.success(request, message)
                return redirect('frontend:dashboard')
            else:
                messages.error(request, message)
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            messages.error(request, 'Error durante el login. Por favor, intente de nuevo.')
        
        return render(request, self.template_name)


class LogoutView(View):
    """User logout view."""
    
    def get(self, request, *args, **kwargs):
        auth_service = AuthenticationService(request)
        
        if auth_service.logout():
            messages.info(request, 'Sesión cerrada exitosamente.')
        else:
            messages.warning(request, 'Error al cerrar sesión.')
        
        return redirect('frontend:login')

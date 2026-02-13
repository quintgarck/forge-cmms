"""
URL configuration for forge_api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Swagger/OpenAPI configuration
schema_view = get_schema_view(
    openapi.Info(
        title="ForgeDB API REST",
        default_version='v1',
        description="""
        API REST para Sistema de Gestión de Talleres Automotrices ForgeDB
        
        ## Características principales:
        - Gestión completa de clientes y equipos
        - Control de inventario con alertas automáticas
        - Órdenes de trabajo con flujo completo
        - Facturación y pagos integrados
        - Analytics y KPIs avanzados
        - Gestión de documentos
        
        ## Autenticación:
        Esta API utiliza JWT (JSON Web Tokens) para autenticación.
        Para obtener un token, use el endpoint `/api/v1/auth/login/`
        """,
        terms_of_service="https://www.forgedb.com/terms/",
        contact=openapi.Contact(email="api@forgedb.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
    
    # Frontend web interface
    path('', include('frontend.urls')),
    
    # API endpoints
    path('api/v1/', include('core.urls')),
    
    # API Documentation
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # API root - redirect to swagger for API users
    path('api/', schema_view.with_ui('swagger', cache_timeout=0), name='api-root'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
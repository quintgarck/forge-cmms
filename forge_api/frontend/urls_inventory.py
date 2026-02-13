"""
URL configuration for inventory module in ForgeDB frontend
"""
from django.urls import path
from . import views
from . import views_inventory

app_name = 'inventory'

urlpatterns = [
    # Inventory Dashboard
    path('', views_inventory.InventoryDashboardView.as_view(), name='inventory_dashboard'),
    path('dashboard/', views_inventory.InventoryDashboardView.as_view(), name='inventory_dashboard'),
    
    # Product Management
    path('products/', views_inventory.ProductListView.as_view(), name='product_list'),
    path('products/create/', views_inventory.ProductCreateView.as_view(), name='product_create'),
    path('products/<int:pk>/', views_inventory.ProductDetailView.as_view(), name='product_detail'),
    path('products/<int:pk>/edit/', views_inventory.ProductUpdateView.as_view(), name='product_update'),
    
    # Stock Management
    path('stock/', views_inventory.StockListView.as_view(), name='stock_list'),
    path('stock/movement/', views_inventory.StockMovementView.as_view(), name='stock_movement'),
    path('stock/movement/create/', views_inventory.StockMovementCreateView.as_view(), name='stock_movement_create'),
    
    # Transaction Management
    path('transactions/', views_inventory.TransactionListView.as_view(), name='transaction_list'),
    
    # Alerts and Notifications
    path('alerts/', views_inventory.InventoryAlertsView.as_view(), name='inventory_alerts'),
    
    # Analytics and Reporting
    path('analytics/', views_inventory.InventoryAnalyticsView.as_view(), name='inventory_analytics'),
    
    # API endpoints for AJAX calls
    path('api/low-stock-items/', views_inventory.get_low_stock_items, name='api_low_stock_items'),
    path('api/inventory-summary/', views_inventory.get_inventory_summary, name='api_inventory_summary'),
]
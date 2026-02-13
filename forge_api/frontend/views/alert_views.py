"""
ForgeDB Frontend - Alert Management Views
Automotive Workshop Management System
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, View
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
import json

from ..services.api_client import APIException
from ..mixins import APIClientMixin


class AlertDashboardView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Dashboard for alert management with severity classification."""
    template_name = 'frontend/alerts/alert_dashboard.html'
    login_url = 'frontend:login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            api_client = self.get_api_client()
            
            # Get all alerts with pagination
            alerts_data = api_client.get('alerts/', params={
                'page_size': 100,
                'ordering': '-created_at'
            })
            
            alerts = alerts_data.get('results', [])
            
            # Process alerts with severity classification
            for alert in alerts:
                # Add severity styling
                severity = alert.get('severity', '').lower()
                if severity == 'critical':
                    alert['severity_class'] = 'danger'
                    alert['severity_icon'] = 'bi-exclamation-triangle-fill'
                    alert['severity_badge'] = 'bg-danger'
                elif severity == 'high':
                    alert['severity_class'] = 'warning'
                    alert['severity_icon'] = 'bi-exclamation-circle-fill'
                    alert['severity_badge'] = 'bg-warning'
                elif severity == 'medium':
                    alert['severity_class'] = 'info'
                    alert['severity_icon'] = 'bi-info-circle-fill'
                    alert['severity_badge'] = 'bg-info'
                elif severity == 'low':
                    alert['severity_class'] = 'secondary'
                    alert['severity_icon'] = 'bi-info-circle'
                    alert['severity_badge'] = 'bg-secondary'
                else:
                    alert['severity_class'] = 'light'
                    alert['severity_icon'] = 'bi-circle'
                    alert['severity_badge'] = 'bg-light text-dark'
                
                # Add alert type icons
                alert_type = alert.get('alert_type', '').lower()
                if alert_type == 'inventory':
                    alert['type_icon'] = 'bi-box-seam'
                elif alert_type == 'maintenance':
                    alert['type_icon'] = 'bi-tools'
                elif alert_type == 'business':
                    alert['type_icon'] = 'bi-briefcase'
                elif alert_type == 'system':
                    alert['type_icon'] = 'bi-gear'
                else:
                    alert['type_icon'] = 'bi-bell'
                
                # Add status styling
                status = alert.get('status', '').lower()
                if status == 'new':
                    alert['status_class'] = 'primary'
                elif status == 'read':
                    alert['status_class'] = 'info'
                elif status == 'acknowledged':
                    alert['status_class'] = 'warning'
                elif status == 'resolved':
                    alert['status_class'] = 'success'
                else:
                    alert['status_class'] = 'secondary'
            
            # Calculate summary statistics
            total_alerts = len(alerts)
            critical_alerts = len([a for a in alerts if a.get('severity') == 'critical'])
            high_alerts = len([a for a in alerts if a.get('severity') == 'high'])
            medium_alerts = len([a for a in alerts if a.get('severity') == 'medium'])
            low_alerts = len([a for a in alerts if a.get('severity') == 'low'])
            
            new_alerts = len([a for a in alerts if a.get('status') == 'new'])
            acknowledged_alerts = len([a for a in alerts if a.get('status') == 'acknowledged'])
            resolved_alerts = len([a for a in alerts if a.get('status') == 'resolved'])
            
            # Group alerts by type
            alerts_by_type = {}
            for alert in alerts:
                alert_type = alert.get('alert_type', 'other')
                if alert_type not in alerts_by_type:
                    alerts_by_type[alert_type] = []
                alerts_by_type[alert_type].append(alert)
            
            context.update({
                'alerts': alerts,
                'total_alerts': total_alerts,
                'critical_alerts': critical_alerts,
                'high_alerts': high_alerts,
                'medium_alerts': medium_alerts,
                'low_alerts': low_alerts,
                'new_alerts': new_alerts,
                'acknowledged_alerts': acknowledged_alerts,
                'resolved_alerts': resolved_alerts,
                'alerts_by_type': alerts_by_type,
                'alert_types': ['inventory', 'maintenance', 'business', 'system'],
                'severity_levels': ['critical', 'high', 'medium', 'low'],
                'status_options': ['new', 'read', 'acknowledged', 'resolved']
            })
            
        except APIException as e:
            messages.error(self.request, f"Error loading alerts: {str(e)}")
            context.update({
                'alerts': [],
                'total_alerts': 0,
                'critical_alerts': 0,
                'high_alerts': 0,
                'medium_alerts': 0,
                'low_alerts': 0,
                'new_alerts': 0,
                'acknowledged_alerts': 0,
                'resolved_alerts': 0,
                'alerts_by_type': {},
                'alert_types': [],
                'severity_levels': [],
                'status_options': []
            })
        
        return context


class AlertDetailView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Detailed view for individual alert management."""
    template_name = 'frontend/alerts/alert_detail.html'
    login_url = 'frontend:login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        alert_id = kwargs.get('alert_id')
        
        try:
            api_client = self.get_api_client()
            alert = api_client.get(f'alerts/{alert_id}/')
            
            # Add styling information
            severity = alert.get('severity', '').lower()
            if severity == 'critical':
                alert['severity_class'] = 'danger'
                alert['severity_icon'] = 'bi-exclamation-triangle-fill'
            elif severity == 'high':
                alert['severity_class'] = 'warning'
                alert['severity_icon'] = 'bi-exclamation-circle-fill'
            elif severity == 'medium':
                alert['severity_class'] = 'info'
                alert['severity_icon'] = 'bi-info-circle-fill'
            elif severity == 'low':
                alert['severity_class'] = 'secondary'
                alert['severity_icon'] = 'bi-info-circle'
            
            context['alert'] = alert
            
        except APIException as e:
            messages.error(self.request, f"Error loading alert: {str(e)}")
            context['alert'] = None
        
        return context


class AlertActionView(LoginRequiredMixin, APIClientMixin, View):
    """Handle alert actions (acknowledge, resolve, etc.)."""
    login_url = 'frontend:login'

    def post(self, request, alert_id):
        try:
            api_client = self.get_api_client()
            action = request.POST.get('action')
            
            if action == 'acknowledge':
                data = {
                    'status': 'acknowledged',
                    'acknowledged_at': timezone.now().isoformat()
                }
                api_client.patch(f'alerts/{alert_id}/', data)
                messages.success(request, "Alert acknowledged successfully.")
                
            elif action == 'resolve':
                data = {
                    'status': 'resolved',
                    'resolved_at': timezone.now().isoformat()
                }
                api_client.patch(f'alerts/{alert_id}/', data)
                messages.success(request, "Alert resolved successfully.")
                
            elif action == 'mark_read':
                data = {
                    'status': 'read',
                    'read_at': timezone.now().isoformat()
                }
                api_client.patch(f'alerts/{alert_id}/', data)
                messages.success(request, "Alert marked as read.")
                
            elif action == 'assign':
                assigned_to = request.POST.get('assigned_to')
                if assigned_to:
                    data = {'assigned_to': int(assigned_to)}
                    api_client.patch(f'alerts/{alert_id}/', data)
                    messages.success(request, "Alert assigned successfully.")
                else:
                    messages.error(request, "Please select a user to assign.")
            
        except APIException as e:
            messages.error(request, f"Error updating alert: {str(e)}")
        except ValueError as e:
            messages.error(request, f"Invalid data: {str(e)}")
        
        return redirect('frontend:alert_detail', alert_id=alert_id)


class BusinessRuleManagementView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Management interface for business rules with visual editor."""
    template_name = 'frontend/alerts/business_rule_management.html'
    login_url = 'frontend:login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            api_client = self.get_api_client()
            
            # Get all business rules
            rules_data = api_client.get('business-rules/', params={
                'page_size': 100,
                'ordering': 'execution_order'
            })
            
            rules = rules_data.get('results', [])
            
            # Process rules for display
            for rule in rules:
                # Add status styling
                if rule.get('is_active'):
                    rule['status_class'] = 'success'
                    rule['status_text'] = 'Active'
                    rule['status_icon'] = 'bi-check-circle'
                else:
                    rule['status_class'] = 'secondary'
                    rule['status_text'] = 'Inactive'
                    rule['status_icon'] = 'bi-pause-circle'
                
                # Add severity styling
                severity = rule.get('severity', '').lower()
                if severity == 'critical':
                    rule['severity_class'] = 'danger'
                elif severity == 'high':
                    rule['severity_class'] = 'warning'
                elif severity == 'medium':
                    rule['severity_class'] = 'info'
                else:
                    rule['severity_class'] = 'secondary'
                
                # Add action type icons
                action_type = rule.get('action_type', '').lower()
                if action_type == 'alert':
                    rule['action_icon'] = 'bi-bell'
                elif action_type == 'block':
                    rule['action_icon'] = 'bi-shield-x'
                elif action_type == 'warn':
                    rule['action_icon'] = 'bi-exclamation-triangle'
                elif action_type == 'log':
                    rule['action_icon'] = 'bi-journal-text'
                else:
                    rule['action_icon'] = 'bi-gear'
            
            # Group rules by schema/table
            rules_by_schema = {}
            for rule in rules:
                schema = rule.get('applies_to_schema', 'general')
                if schema not in rules_by_schema:
                    rules_by_schema[schema] = []
                rules_by_schema[schema].append(rule)
            
            context.update({
                'rules': rules,
                'rules_by_schema': rules_by_schema,
                'condition_types': [
                    {'value': 'sql', 'label': 'SQL Query'},
                    {'value': 'python', 'label': 'Python Expression'},
                    {'value': 'regex', 'label': 'Regular Expression'}
                ],
                'action_types': [
                    {'value': 'alert', 'label': 'Generate Alert'},
                    {'value': 'block', 'label': 'Block Operation'},
                    {'value': 'warn', 'label': 'Show Warning'},
                    {'value': 'log', 'label': 'Log Event'}
                ],
                'trigger_events': [
                    {'value': 'insert', 'label': 'Insert'},
                    {'value': 'update', 'label': 'Update'},
                    {'value': 'delete', 'label': 'Delete'},
                    {'value': 'select', 'label': 'Select'}
                ],
                'severity_levels': [
                    {'value': 'low', 'label': 'Low'},
                    {'value': 'medium', 'label': 'Medium'},
                    {'value': 'high', 'label': 'High'},
                    {'value': 'critical', 'label': 'Critical'}
                ]
            })
            
        except APIException as e:
            messages.error(self.request, f"Error loading business rules: {str(e)}")
            context.update({
                'rules': [],
                'rules_by_schema': {},
                'condition_types': [],
                'action_types': [],
                'trigger_events': [],
                'severity_levels': []
            })
        
        return context


class AuditLogView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Audit log interface with advanced filtering."""
    template_name = 'frontend/alerts/audit_log.html'
    login_url = 'frontend:login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get filter parameters
        table_name = self.request.GET.get('table_name', '')
        action = self.request.GET.get('action', '')
        changed_by = self.request.GET.get('changed_by', '')
        date_from = self.request.GET.get('date_from', '')
        date_to = self.request.GET.get('date_to', '')
        page = self.request.GET.get('page', 1)
        
        try:
            api_client = self.get_api_client()
            
            # Build filter parameters
            params = {
                'page': page,
                'page_size': 50,
                'ordering': '-changed_at'
            }
            
            if table_name:
                params['table_name'] = table_name
            if action:
                params['action'] = action
            if changed_by:
                params['changed_by'] = changed_by
            if date_from:
                params['changed_at__gte'] = date_from
            if date_to:
                params['changed_at__lte'] = date_to
            
            # Get audit logs
            audit_data = api_client.get('audit-logs/', params=params)
            audit_logs = audit_data.get('results', [])
            
            # Process audit logs for display
            for log in audit_logs:
                # Add action styling
                action_type = log.get('action', '').upper()
                if action_type == 'INSERT':
                    log['action_class'] = 'success'
                    log['action_icon'] = 'bi-plus-circle'
                elif action_type == 'UPDATE':
                    log['action_class'] = 'warning'
                    log['action_icon'] = 'bi-pencil-circle'
                elif action_type == 'DELETE':
                    log['action_class'] = 'danger'
                    log['action_icon'] = 'bi-trash-circle'
                else:
                    log['action_class'] = 'secondary'
                    log['action_icon'] = 'bi-circle'
                
                # Format changed_at for display
                if log.get('changed_at'):
                    try:
                        changed_at = datetime.fromisoformat(log['changed_at'].replace('Z', '+00:00'))
                        log['changed_at_formatted'] = changed_at.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        log['changed_at_formatted'] = log['changed_at']
            
            # Get unique table names for filter dropdown
            tables_data = api_client.get('audit-logs/', params={
                'page_size': 1000,
                'fields': 'table_name'
            })
            unique_tables = list(set([log.get('table_name') for log in tables_data.get('results', []) if log.get('table_name')]))
            unique_tables.sort()
            
            context.update({
                'audit_logs': audit_logs,
                'pagination': {
                    'count': audit_data.get('count', 0),
                    'next': audit_data.get('next'),
                    'previous': audit_data.get('previous'),
                    'current_page': int(page),
                    'total_pages': (audit_data.get('count', 0) + 49) // 50  # Ceiling division
                },
                'filters': {
                    'table_name': table_name,
                    'action': action,
                    'changed_by': changed_by,
                    'date_from': date_from,
                    'date_to': date_to
                },
                'unique_tables': unique_tables,
                'action_choices': ['INSERT', 'UPDATE', 'DELETE']
            })
            
        except APIException as e:
            messages.error(self.request, f"Error loading audit logs: {str(e)}")
            context.update({
                'audit_logs': [],
                'pagination': {'count': 0, 'current_page': 1, 'total_pages': 0},
                'filters': {},
                'unique_tables': [],
                'action_choices': []
            })
        
        return context


class NotificationAPIView(LoginRequiredMixin, APIClientMixin, View):
    """API endpoint for real-time notifications."""
    login_url = 'frontend:login'

    def get(self, request):
        """Get recent notifications for current user."""
        try:
            api_client = self.get_api_client()
            
            # Get recent alerts for current user
            alerts_data = api_client.get('alerts/', params={
                'status': 'new',
                'page_size': 10,
                'ordering': '-created_at'
            })
            
            alerts = alerts_data.get('results', [])
            
            # Format notifications
            notifications = []
            for alert in alerts:
                notifications.append({
                    'id': alert.get('alert_id'),
                    'type': alert.get('alert_type'),
                    'title': alert.get('title'),
                    'message': alert.get('message'),
                    'severity': alert.get('severity'),
                    'created_at': alert.get('created_at'),
                    'url': f"/frontend/alerts/{alert.get('alert_id')}/"
                })
            
            return JsonResponse({
                'success': True,
                'notifications': notifications,
                'count': len(notifications)
            })
            
        except APIException as e:
            return JsonResponse({
                'success': False,
                'error': str(e),
                'notifications': [],
                'count': 0
            })
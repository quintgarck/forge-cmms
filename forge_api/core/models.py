"""
ForgeDB API REST - Django Models
Automotive Workshop Management System

This module contains Django models generated from the existing ForgeDB PostgreSQL database.
Models are organized by schema and include proper relationships and business logic.
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from datetime import date
import uuid


# =============================================================================
# APP SCHEMA - Application Management
# =============================================================================

class Alert(models.Model):
    """System alerts and notifications"""
    ALERT_TYPES = [
        ('inventory', 'Inventory'),
        ('maintenance', 'Maintenance'),
        ('business', 'Business Rule'),
        ('system', 'System'),
    ]
    
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('new', 'New'),
        ('read', 'Read'),
        ('acknowledged', 'Acknowledged'),
        ('resolved', 'Resolved'),
    ]

    alert_id = models.AutoField(primary_key=True)
    alert_type = models.CharField(max_length=30, choices=ALERT_TYPES)
    ref_entity = models.CharField(max_length=30, blank=True, null=True)
    ref_id = models.IntegerField(blank=True, null=True)
    ref_code = models.CharField(max_length=50, blank=True, null=True)
    title = models.CharField(max_length=200)
    message = models.TextField()
    details = models.JSONField(blank=True, null=True)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    assigned_to = models.IntegerField(blank=True, null=True)
    created_for = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(blank=True, null=True)
    acknowledged_at = models.DateTimeField(blank=True, null=True)
    resolved_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'alerts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['alert_type', 'status']),
            models.Index(fields=['severity', 'created_at']),
        ]

    def __str__(self):
        return f"{self.alert_type.title()}: {self.title}"


class ServiceAlertThreshold(models.Model):
    """
    Configuration thresholds for service alerts.
    Stores customizable thresholds for automatic alert detection.
    """
    threshold_id = models.AutoField(primary_key=True)
    threshold_key = models.CharField(max_length=50, unique=True)
    threshold_name = models.CharField(max_length=100)
    value = models.FloatField(help_text="Threshold value")
    unit = models.CharField(max_length=20, blank=True, null=True, help_text="Unit of measurement (e.g., hours, %, count)")
    category = models.CharField(max_length=50, default='general', help_text="Category: orders, technicians, inventory, etc.")
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.IntegerField(blank=True, null=True)
    
    class Meta:
        db_table = 'service_alert_thresholds'
        ordering = ['category', 'threshold_key']
        indexes = [
            models.Index(fields=['threshold_key', 'is_active']),
            models.Index(fields=['category']),
        ]
    
    def __str__(self):
        return f"{self.threshold_name}: {self.value} {self.unit or ''}"


class ServiceAlertEscalation(models.Model):
    """
    Tracks alert escalations when alerts are not resolved within time limits.
    """
    escalation_id = models.AutoField(primary_key=True)
    alert_id = models.IntegerField(help_text="Reference to app.alerts.alert_id")
    original_severity = models.CharField(max_length=10, choices=Alert.SEVERITY_CHOICES)
    escalated_severity = models.CharField(max_length=10, choices=Alert.SEVERITY_CHOICES)
    escalation_level = models.IntegerField(default=1, help_text="Number of times this alert has been escalated")
    escalated_at = models.DateTimeField(auto_now_add=True)
    escalated_by = models.IntegerField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'service_alert_escalations'
        ordering = ['-escalated_at']
        indexes = [
            models.Index(fields=['alert_id', 'escalated_at']),
            models.Index(fields=['escalation_level']),
        ]
    
    def __str__(self):
        return f"Alert #{self.alert_id}: {self.original_severity} -> {self.escalated_severity} (Level {self.escalation_level})"


class BusinessRule(models.Model):
    """Business rules and validation logic"""
    CONDITION_TYPES = [
        ('sql', 'SQL Query'),
        ('python', 'Python Expression'),
        ('regex', 'Regular Expression'),
    ]
    
    ACTION_TYPES = [
        ('alert', 'Generate Alert'),
        ('block', 'Block Operation'),
        ('warn', 'Show Warning'),
        ('log', 'Log Event'),
    ]
    
    TRIGGER_EVENTS = [
        ('insert', 'Insert'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('select', 'Select'),
    ]

    rule_id = models.AutoField(primary_key=True)
    rule_code = models.CharField(max_length=30, unique=True)
    rule_name = models.CharField(max_length=100)
    condition_text = models.TextField()
    condition_type = models.CharField(max_length=20, choices=CONDITION_TYPES, default='sql')
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    action_text = models.TextField()
    applies_to_table = models.CharField(max_length=50, blank=True, null=True)
    applies_to_schema = models.CharField(max_length=20, blank=True, null=True)
    trigger_event = models.CharField(max_length=20, choices=TRIGGER_EVENTS, blank=True, null=True)
    severity = models.CharField(max_length=10, choices=Alert.SEVERITY_CHOICES, default='medium')
    is_active = models.BooleanField(default=True)
    is_system_rule = models.BooleanField(default=False)
    execution_order = models.IntegerField(default=100)
    stop_on_match = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'business_rules'
        ordering = ['execution_order', 'rule_name']

    def __str__(self):
        return f"{self.rule_code}: {self.rule_name}"


class AuditLog(models.Model):
    """Audit trail for all database changes"""
    ACTION_CHOICES = [
        ('INSERT', 'Insert'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
    ]

    audit_id = models.BigAutoField(primary_key=True)
    table_name = models.CharField(max_length=50)
    record_id = models.BigIntegerField()
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    changed_by = models.IntegerField(blank=True, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    old_values = models.JSONField(blank=True, null=True)
    new_values = models.JSONField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'audit_logs'
        indexes = [
            models.Index(fields=['table_name', 'record_id']),
            models.Index(fields=['changed_at']),
            models.Index(fields=['changed_by']),
        ]

    def __str__(self):
        return f"{self.action} on {self.table_name}({self.record_id}) at {self.changed_at}"


# =============================================================================
# CAT SCHEMA - Catalog and Master Data
# =============================================================================

class Technician(models.Model):
    """Workshop technicians and users"""
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('SUSPENDED', 'Suspended'),
    ]

    technician_id = models.AutoField(primary_key=True)
    employee_code = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    hire_date = models.DateField(blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    specialization = ArrayField(models.CharField(max_length=100), default=list, blank=True, null=True)  # PostgreSQL ARRAY
    certification_level = models.CharField(max_length=50, blank=True, null=True)
    certifications = ArrayField(models.CharField(max_length=100), default=list, blank=True, null=True)  # PostgreSQL ARRAY
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'), blank=True, null=True)
    daily_rate = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'), blank=True, null=True)
    overtime_multiplier = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal('1.50'), blank=True, null=True)
    work_schedule = models.JSONField(blank=True, null=True)
    efficiency_avg = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('100.00'), blank=True, null=True)
    quality_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('100.00'), blank=True, null=True)
    jobs_completed = models.IntegerField(default=0, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE', blank=True, null=True)
    is_active = models.BooleanField(default=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'technicians'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.employee_code})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Client(models.Model):
    """Workshop clients and customers"""
    TYPE_CHOICES = [
        ('INDIVIDUAL', 'Individual'),
        ('EMPRESA', 'Business'),
        ('GOVERNMENT', 'Government'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('BLOCKED', 'Blocked'),
    ]

    client_id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    client_code = models.CharField(max_length=20, unique=True)
    type = models.CharField(max_length=15, choices=TYPE_CHOICES)
    name = models.CharField(max_length=150)
    legal_name = models.CharField(max_length=150, blank=True, null=True)
    tax_id = models.CharField(max_length=30, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    mobile = models.CharField(max_length=30, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    state = models.CharField(max_length=50, blank=True, null=True)
    country = models.CharField(max_length=50, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    payment_days = models.IntegerField(blank=True, null=True, default=30)
    credit_used = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), blank=True, null=True)
    preferred_contact_method = models.CharField(max_length=20, blank=True, null=True, default='EMAIL')
    send_reminders = models.BooleanField(default=True, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE', blank=True, null=True)
    created_by = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'clients'
        ordering = ['name']
        indexes = [
            models.Index(fields=['client_code']),
            models.Index(fields=['type', 'status']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return f"{self.name} ({self.client_code})"

    @property
    def available_credit(self):
        if self.credit_limit:
            return self.credit_limit - (self.credit_used or Decimal('0.00'))
        return None


# =============================================================================
# CAT SCHEMA - Catalog Reference Tables
# =============================================================================

class EquipmentType(models.Model):
    """Equipment types and categories"""
    type_id = models.AutoField(primary_key=True)
    type_code = models.CharField(max_length=20, unique=True)
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, db_column='category_id', blank=True, null=True, related_name='equipment_types')
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, blank=True, null=True)
    color = models.CharField(max_length=20, blank=True, null=True)
    attr_schema = models.JSONField(default=dict, blank=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'equipment_types'
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.type_code})"


class Category(models.Model):
    """Equipment categories - replaces static CATEGORY_CHOICES"""
    category_id = models.AutoField(primary_key=True)
    category_code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, null=True)
    color = models.CharField(max_length=20, blank=True, null=True)
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'categories'
        ordering = ['sort_order', 'name']
        verbose_name_plural = 'Categories'
    
    def __str__(self):
        return self.name


class FuelCode(models.Model):
    """Fuel type codes"""
    fuel_code = models.CharField(max_length=10, primary_key=True)
    name_es = models.CharField(max_length=30)
    name_en = models.CharField(max_length=30, blank=True, null=True)
    is_alternative = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'fuel_codes'
        ordering = ['fuel_code']
    
    def __str__(self):
        return f"{self.name_es} ({self.fuel_code})"


class AspirationCode(models.Model):
    """Engine aspiration codes"""
    aspiration_code = models.CharField(max_length=10, primary_key=True)
    name_es = models.CharField(max_length=30)
    name_en = models.CharField(max_length=30, blank=True, null=True)
    
    class Meta:
        db_table = 'aspiration_codes'
        ordering = ['aspiration_code']
    
    def __str__(self):
        return f"{self.name_es} ({self.aspiration_code})"


class TransmissionCode(models.Model):
    """Transmission type codes"""
    transmission_code = models.CharField(max_length=10, primary_key=True)
    name_es = models.CharField(max_length=30)
    name_en = models.CharField(max_length=30, blank=True, null=True)
    
    class Meta:
        db_table = 'transmission_codes'
        ordering = ['transmission_code']
    
    def __str__(self):
        return f"{self.name_es} ({self.transmission_code})"


class DrivetrainCode(models.Model):
    """Drivetrain type codes"""
    drivetrain_code = models.CharField(max_length=10, primary_key=True)
    name_es = models.CharField(max_length=30)
    name_en = models.CharField(max_length=30, blank=True, null=True)
    
    class Meta:
        db_table = 'drivetrain_codes'
        ordering = ['drivetrain_code']
    
    def __str__(self):
        return f"{self.name_es} ({self.drivetrain_code})"


class ColorCode(models.Model):
    """Color codes catalog"""
    color_id = models.AutoField(primary_key=True)
    color_code = models.CharField(max_length=10, unique=True)
    brand = models.CharField(max_length=30, default='GENERIC')
    name_es = models.CharField(max_length=50)
    name_en = models.CharField(max_length=50, blank=True, null=True)
    hex_code = models.CharField(max_length=7, blank=True, null=True)
    paint_type = models.CharField(max_length=20, blank=True, null=True)
    is_metallic = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'color_codes'
        unique_together = [['brand', 'color_code']]
        ordering = ['brand', 'sort_order', 'color_code']
    
    def __str__(self):
        return f"{self.name_es} ({self.color_code})"


class PositionCode(models.Model):
    """Position codes for parts"""
    POSITION_CATEGORIES = [
        ('SIDE', 'Side'),
        ('CORNER', 'Corner'),
        ('ZONE', 'Zone'),
        ('RELATIVE', 'Relative'),
    ]
    
    position_code = models.CharField(max_length=15, primary_key=True)
    name_es = models.CharField(max_length=50)
    name_en = models.CharField(max_length=50, blank=True, null=True)
    category = models.CharField(max_length=20, choices=POSITION_CATEGORIES, blank=True, null=True)
    sort_order = models.IntegerField(default=0)
    synonyms = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'position_codes'
        ordering = ['sort_order', 'position_code']
    
    def __str__(self):
        return f"{self.name_es} ({self.position_code})"


class FinishCode(models.Model):
    """Finish type codes"""
    finish_code = models.CharField(max_length=10, primary_key=True)
    name_es = models.CharField(max_length=50)
    name_en = models.CharField(max_length=50, blank=True, null=True)
    requires_color = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'finish_codes'
        ordering = ['sort_order', 'finish_code']
    
    def __str__(self):
        return f"{self.name_es} ({self.finish_code})"


class SourceCode(models.Model):
    """Source/quality codes"""
    QUALITY_LEVELS = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('PREMIUM', 'Premium'),
    ]
    
    source_code = models.CharField(max_length=10, primary_key=True)
    name_es = models.CharField(max_length=50)
    name_en = models.CharField(max_length=50, blank=True, null=True)
    quality_level = models.CharField(max_length=10, choices=QUALITY_LEVELS, blank=True, null=True)
    sort_order = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'source_codes'
        ordering = ['sort_order', 'source_code']
    
    def __str__(self):
        return f"{self.name_es} ({self.source_code})"


class ConditionCode(models.Model):
    """Condition codes for parts"""
    condition_code = models.CharField(max_length=10, primary_key=True)
    name_es = models.CharField(max_length=50)
    name_en = models.CharField(max_length=50, blank=True, null=True)
    requires_core = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'condition_codes'
        ordering = ['sort_order', 'condition_code']
    
    def __str__(self):
        return f"{self.name_es} ({self.condition_code})"


class UOMCode(models.Model):
    """Unit of measure codes"""
    uom_code = models.CharField(max_length=10, primary_key=True)
    name_es = models.CharField(max_length=50)
    name_en = models.CharField(max_length=50, blank=True, null=True)
    is_fractional = models.BooleanField(default=False)
    category = models.CharField(max_length=20, blank=True, null=True)
    
    class Meta:
        db_table = 'uom_codes'
        ordering = ['uom_code']
    
    def __str__(self):
        return f"{self.name_es} ({self.uom_code})"


class ProductCategory(models.Model):
    """Catálogo de categorías de producto (inventario)."""
    code = models.CharField(max_length=20, primary_key=True)
    name_es = models.CharField(max_length=80)
    name_en = models.CharField(max_length=80, blank=True, null=True)
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = '"cat"."product_category"'
        ordering = ['display_order', 'code']
        verbose_name = 'Categoría de producto'
        verbose_name_plural = 'Categorías de producto'

    def __str__(self):
        return self.name_es or self.code


class ProductType(models.Model):
    """Catálogo de tipos de producto (inventario)."""
    code = models.CharField(max_length=20, primary_key=True)
    name_es = models.CharField(max_length=80)
    name_en = models.CharField(max_length=80, blank=True, null=True)
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = '"cat"."product_type"'
        ordering = ['display_order', 'code']
        verbose_name = 'Tipo de producto'
        verbose_name_plural = 'Tipos de producto'

    def __str__(self):
        return self.name_es or self.code


class Currency(models.Model):
    """Currency codes and exchange rates"""
    currency_code = models.CharField(max_length=3, primary_key=True)
    name = models.CharField(max_length=50)
    symbol = models.CharField(max_length=5, blank=True, null=True)
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=4, default=Decimal('1.0'))
    decimals = models.IntegerField(default=2)
    is_active = models.BooleanField(default=True)
    is_base_currency = models.BooleanField(default=False)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'currencies'
        ordering = ['currency_code']
        verbose_name_plural = 'Currencies'
    
    def __str__(self):
        return f"{self.name} ({self.currency_code})"
    
    def save(self, *args, **kwargs):
        # Ensure only one base currency
        if self.is_base_currency:
            Currency.objects.filter(is_base_currency=True).exclude(
                currency_code=self.currency_code
            ).update(is_base_currency=False)
            # Base currency always has exchange_rate = 1.0
            self.exchange_rate = Decimal('1.0')
        super().save(*args, **kwargs)


class Supplier(models.Model):
    """Suppliers and vendors"""
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('SUSPENDED', 'Suspended'),
    ]
    
    supplier_id = models.AutoField(primary_key=True)
    supplier_code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    state = models.CharField(max_length=50, blank=True, null=True)
    country = models.CharField(max_length=50, blank=True, null=True)
    tax_id = models.CharField(max_length=30, blank=True, null=True)
    payment_terms = models.IntegerField(default=30)
    currency_code = models.CharField(max_length=3, default='USD')
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal('5.00'))
    delivery_time_avg = models.IntegerField(default=7)
    quality_score = models.DecimalField(max_digits=3, decimal_places=2, default=Decimal('5.00'))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    is_preferred = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'suppliers'
        ordering = ['name']
        indexes = [
            models.Index(fields=['supplier_code']),
            models.Index(fields=['status', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.supplier_code})"


class TaxonomySystem(models.Model):
    """Taxonomy systems (e.g., Engine, Transmission, etc.)"""
    system_code = models.CharField(max_length=10, primary_key=True)
    category = models.CharField(max_length=30, default='AUTOMOTRIZ')
    name_es = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100, blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, null=True)
    scope = models.TextField(blank=True, null=True)
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'taxonomy_systems'
        ordering = ['sort_order', 'system_code']
    
    def __str__(self):
        return f"{self.name_es} ({self.system_code})"


class TaxonomySubsystem(models.Model):
    """Taxonomy subsystems"""
    subsystem_code = models.CharField(max_length=20, primary_key=True)
    system_code = models.ForeignKey(TaxonomySystem, on_delete=models.CASCADE, db_column='system_code')
    name_es = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100, blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'taxonomy_subsystems'
        ordering = ['system_code', 'sort_order', 'subsystem_code']
    
    def __str__(self):
        return f"{self.name_es} ({self.subsystem_code})"


class TaxonomyGroup(models.Model):
    """Taxonomy groups"""
    group_code = models.CharField(max_length=20, primary_key=True)
    subsystem_code = models.ForeignKey(TaxonomySubsystem, on_delete=models.CASCADE, db_column='subsystem_code')
    system_code = models.ForeignKey(TaxonomySystem, on_delete=models.CASCADE, db_column='system_code')
    name_es = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    examples = models.TextField(blank=True, null=True)
    keywords = models.TextField(blank=True, null=True)
    requires_position = models.BooleanField(default=False)
    requires_color = models.BooleanField(default=False)
    requires_finish = models.BooleanField(default=False)
    requires_side = models.BooleanField(default=False)
    typical_position_set = models.TextField(blank=True, null=True)
    typical_uom = models.CharField(max_length=10, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'taxonomy_groups'
        ordering = ['system_code', 'subsystem_code', 'name_es']
        indexes = [
            models.Index(fields=['subsystem_code']),
        ]
    
    def __str__(self):
        return f"{self.name_es} ({self.group_code})"


class Equipment(models.Model):
    """Client vehicles and equipment"""
    STATUS_CHOICES = [
        ('ACTIVO', 'Active'),
        ('INACTIVO', 'Inactive'),
        ('sold', 'Sold'),
        ('scrapped', 'Scrapped'),
    ]

    equipment_id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    equipment_code = models.CharField(max_length=40, unique=True)
    type_id = models.IntegerField(null=True, blank=True, default=1)
    brand = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    year = models.SmallIntegerField(blank=True, null=True)
    serial_number = models.CharField(max_length=100, blank=True, null=True)
    vin = models.CharField(max_length=17, blank=True, null=True)
    license_plate = models.CharField(max_length=20, blank=True, null=True)
    color = models.CharField(max_length=30, blank=True, null=True)
    submodel_trim = models.CharField(max_length=40, blank=True, null=True)
    body_style = models.CharField(max_length=20, blank=True, null=True)
    doors = models.SmallIntegerField(blank=True, null=True)
    engine_desc = models.CharField(max_length=100, blank=True, null=True)
    fuel_code = models.CharField(max_length=10, blank=True, null=True)
    aspiration_code = models.CharField(max_length=10, blank=True, null=True)
    transmission_code = models.CharField(max_length=10, blank=True, null=True)
    drivetrain_code = models.CharField(max_length=10, blank=True, null=True)
    client_id = models.IntegerField(blank=True, null=True)
    purchase_date = models.DateField(blank=True, null=True)
    warranty_until = models.DateField(blank=True, null=True)
    last_service_date = models.DateField(blank=True, null=True)
    next_service_date = models.DateField(blank=True, null=True)
    total_service_hours = models.IntegerField(default=0, blank=True, null=True)
    total_service_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVO', blank=True, null=True)
    current_mileage_hours = models.IntegerField(default=0, blank=True, null=True)
    last_mileage_update = models.DateField(blank=True, null=True)
    custom_fields = models.JSONField(default=dict, blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True, null=True)
    created_by = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'equipment'
        ordering = ['client_id', 'year', 'brand', 'model']
        indexes = [
            models.Index(fields=['vin']),
            models.Index(fields=['license_plate']),
            models.Index(fields=['client_id', 'status']),
        ]

    def __str__(self):
        year_str = str(self.year) if self.year else 'N/A'
        return f"{year_str} {self.brand} {self.model} ({self.equipment_code})"
    
    @property
    def client(self):
        """Compatibility property for accessing client"""
        if self.client_id:
            try:
                return Client.objects.get(client_id=self.client_id)
            except Client.DoesNotExist:
                return None
        return None
    
    @property
    def mileage(self):
        """Compatibility property"""
        return self.current_mileage_hours


# =============================================================================
# INV SCHEMA - Inventory Management
# =============================================================================

class Warehouse(models.Model):
    """Inventory warehouses and locations"""
    warehouse_code = models.CharField(max_length=10, primary_key=True)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=50, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    contact_phone = models.CharField(max_length=30, blank=True, null=True)
    manager = models.CharField(max_length=100, blank=True, null=True)
    capacity = models.IntegerField(blank=True, null=True)
    current_occupancy = models.IntegerField(default=0, blank=True, null=True)
    is_active = models.BooleanField(default=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    class Meta:
        db_table = 'warehouses'
        ordering = ['warehouse_code']

    def __str__(self):
        return f"{self.warehouse_code}: {self.name}"
    
    @property
    def status(self):
        """Compatibility property - returns 'active' or 'inactive' based on is_active"""
        return 'active' if self.is_active else 'inactive'
    
    @property
    def is_main(self):
        """Compatibility property - could be determined by type or another logic"""
        return self.type == 'MAIN' if self.type else False


class ProductMaster(models.Model):
    """Master product catalog"""
    internal_sku = models.CharField(max_length=20, primary_key=True)
    group_code = models.CharField(max_length=50)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    brand = models.CharField(max_length=50, blank=True, null=True)
    oem_ref = models.CharField(max_length=50, blank=True, null=True)
    oem_code = models.CharField(max_length=10, blank=True, null=True)
    source_code = models.CharField(max_length=10)
    condition_code = models.CharField(max_length=10)
    position_code = models.CharField(max_length=10, blank=True, null=True)
    finish_code = models.CharField(max_length=10, blank=True, null=True)
    color_code = models.CharField(max_length=10, blank=True, null=True)
    uom_code = models.CharField(max_length=10)
    barcode = models.CharField(max_length=50, blank=True, null=True)
    supplier_mpn = models.CharField(max_length=50, blank=True, null=True)
    interchange_numbers = models.JSONField(default=list, blank=True, null=True)
    cross_references = models.JSONField(default=list, blank=True, null=True)
    weight_kg = models.DecimalField(max_digits=8, decimal_places=3, blank=True, null=True)
    dimensions_cm = models.CharField(max_length=100, blank=True, null=True)
    package_qty = models.IntegerField(default=1, blank=True, null=True)
    min_stock = models.IntegerField(default=0, blank=True, null=True)
    max_stock = models.IntegerField(default=1000, blank=True, null=True)
    reorder_point = models.IntegerField(default=0, blank=True, null=True)
    safety_stock = models.IntegerField(default=0, blank=True, null=True)
    lead_time_days = models.IntegerField(default=7, blank=True, null=True)
    core_required = models.BooleanField(default=False, blank=True, null=True)
    core_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), blank=True, null=True)
    warranty_days = models.IntegerField(default=90, blank=True, null=True)
    standard_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), blank=True, null=True)
    avg_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), blank=True, null=True)
    last_purchase_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), blank=True, null=True)
    is_active = models.BooleanField(default=True, blank=True, null=True)
    is_serialized = models.BooleanField(default=False, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'product_master'
        ordering = ['internal_sku']
        indexes = [
            models.Index(fields=['barcode']),
            models.Index(fields=['group_code']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.internal_sku}: {self.name}"
    
    # Compatibility properties
    @property
    def min_stock_level(self):
        return self.min_stock
    
    @property
    def status(self):
        return 'active' if self.is_active else 'inactive'


class Stock(models.Model):
    """Current stock levels by warehouse and product"""
    stock_id = models.AutoField(primary_key=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, db_column='warehouse_code', to_field='warehouse_code')
    product = models.ForeignKey(ProductMaster, on_delete=models.CASCADE, db_column='internal_sku', to_field='internal_sku')
    bin_id = models.IntegerField(blank=True, null=True)
    qty_on_hand = models.IntegerField(default=0)
    qty_reserved = models.IntegerField(default=0)
    qty_available = models.IntegerField(default=0, blank=True, null=True)
    qty_on_order = models.IntegerField(default=0, blank=True, null=True)
    batch_number = models.CharField(max_length=50, blank=True, null=True)
    serial_number = models.CharField(max_length=100, blank=True, null=True)
    expiration_date = models.DateField(blank=True, null=True)
    manufacturing_date = models.DateField(blank=True, null=True)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=4, default=Decimal('0.0000'), blank=True, null=True)
    total_cost = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    last_receipt_date = models.DateField(auto_now_add=True)
    last_count_date = models.DateField(blank=True, null=True)
    next_count_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, default='AVAILABLE', blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'stock'
        unique_together = [['warehouse', 'product']]
        indexes = [
            models.Index(fields=['warehouse']),
            models.Index(fields=['product']),
            models.Index(fields=['qty_on_hand']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.product.internal_sku} @ {self.warehouse.warehouse_code}: {self.qty_on_hand}"

    @property
    def is_below_minimum(self):
        return self.qty_available < getattr(self.product, 'min_stock_level', 0)

    @property
    def needs_reorder(self):
        return self.qty_available <= getattr(self.product, 'reorder_point', 0)


class Transaction(models.Model):
    """Inventory transactions and movements"""
    TRANSACTION_TYPES = [
        ('receipt', 'Receipt'),
        ('issue', 'Issue'),
        ('transfer', 'Transfer'),
        ('adjustment', 'Adjustment'),
        ('return', 'Return'),
        ('scrap', 'Scrap'),
    ]

    transaction_id = models.BigAutoField(primary_key=True)
    transaction_date = models.DateTimeField(auto_now_add=True)
    transaction_type = models.CharField(max_length=15, choices=TRANSACTION_TYPES)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    product = models.ForeignKey(ProductMaster, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    unit_cost = models.DecimalField(max_digits=12, decimal_places=4, blank=True, null=True)
    total_cost = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    reference_type = models.CharField(max_length=20, blank=True, null=True)
    reference_id = models.IntegerField(blank=True, null=True)
    reference_number = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(Technician, on_delete=models.SET_NULL, blank=True, null=True)

    class Meta:
        db_table = 'transactions'
        ordering = ['-transaction_date']
        indexes = [
            models.Index(fields=['transaction_date']),
            models.Index(fields=['warehouse', 'product']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['reference_type', 'reference_id']),
        ]

    def __str__(self):
        return f"{self.transaction_type.title()}: {self.product.product_code} ({self.quantity})"


# =============================================================================
# SVC SCHEMA - Service Management
# =============================================================================

class WorkOrder(models.Model):
    """Service work orders"""
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SCHEDULED', 'Scheduled'),
        ('IN_PROGRESS', 'In Progress'),
        ('WAITING_PARTS', 'Waiting Parts'),
        ('WAITING_APPROVAL', 'Waiting Approval'),
        ('COMPLETED', 'Completed'),
        ('INVOICED', 'Invoiced'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('NORMAL', 'Normal'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]
    
    SERVICE_TYPE_CHOICES = [
        ('MAINTENANCE', 'Maintenance'),
        ('REPAIR', 'Repair'),
        ('DIAGNOSIS', 'Diagnosis'),
        ('INSPECTION', 'Inspection'),
    ]

    wo_id = models.AutoField(primary_key=True)
    wo_number = models.CharField(max_length=20, unique=True)
    equipment_id = models.IntegerField()
    client_id = models.IntegerField()
    
    # Date fields matching database
    appointment_date = models.DateTimeField(blank=True, null=True)
    reception_date = models.DateTimeField(blank=True, null=True)
    diagnosis_date = models.DateTimeField(blank=True, null=True)
    estimated_start_date = models.DateTimeField(blank=True, null=True)
    actual_start_date = models.DateTimeField(blank=True, null=True)
    estimated_completion_date = models.DateTimeField(blank=True, null=True)
    actual_completion_date = models.DateTimeField(blank=True, null=True)
    qc_date = models.DateTimeField(blank=True, null=True)
    delivery_date = models.DateTimeField(blank=True, null=True)
    
    # Service information
    service_type = models.CharField(max_length=50, choices=SERVICE_TYPE_CHOICES)
    customer_complaints = models.TextField(blank=True, null=True)
    initial_findings = models.TextField(blank=True, null=True)
    technician_notes = models.TextField(blank=True, null=True)
    qc_notes = models.TextField(blank=True, null=True)
    final_report = models.TextField(blank=True, null=True)
    
    # Hours and efficiency
    flat_rate_hours = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'), blank=True, null=True)
    estimated_hours = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'), blank=True, null=True)
    actual_hours = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'), blank=True, null=True)
    efficiency_rate = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    
    # Cost and pricing
    labor_rate = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), blank=True, null=True)
    labor_cost = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    parts_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), blank=True, null=True)
    additional_costs = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), blank=True, null=True)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    quoted_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), blank=True, null=True)
    final_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    
    # Status and priority
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='DRAFT', blank=True, null=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='NORMAL', blank=True, null=True)
    
    # Personnel assignments
    advisor_id = models.IntegerField(blank=True, null=True)
    technician_id = models.IntegerField(blank=True, null=True)
    qc_technician_id = models.IntegerField(blank=True, null=True)
    
    # Mileage and hours tracking
    mileage_in = models.IntegerField(blank=True, null=True)
    mileage_out = models.IntegerField(blank=True, null=True)
    hours_in = models.IntegerField(blank=True, null=True)
    hours_out = models.IntegerField(blank=True, null=True)
    
    # Audit fields
    created_by = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    closed_at = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'work_orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['wo_number']),
            models.Index(fields=['client_id', 'status']),
            models.Index(fields=['equipment_id']),
            models.Index(fields=['technician_id', 'status']),
            models.Index(fields=['appointment_date']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"WO-{self.wo_number} ({self.status})"
    
    # Helper properties for compatibility
    @property
    def client(self):
        """Compatibility property for accessing client via client_id"""
        try:
            return Client.objects.get(client_id=self.client_id)
        except Client.DoesNotExist:
            return None
    
    @property
    def equipment(self):
        """Compatibility property for accessing equipment via equipment_id"""
        try:
            return Equipment.objects.get(equipment_id=self.equipment_id)
        except Equipment.DoesNotExist:
            return None
    
    @property
    def assigned_technician(self):
        """Compatibility property for accessing technician via technician_id"""
        if self.technician_id:
            try:
                return Technician.objects.get(technician_id=self.technician_id)
            except Technician.DoesNotExist:
                return None
        return None


class Invoice(models.Model):
    """Service invoices"""
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]

    invoice_id = models.AutoField(primary_key=True)
    invoice_number = models.CharField(max_length=20, unique=True)
    wo_id = models.IntegerField(blank=True, null=True)
    client_id = models.IntegerField()
    currency_code = models.CharField(max_length=3, blank=True, null=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), blank=True, null=True)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), blank=True, null=True)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), blank=True, null=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT', blank=True, null=True)
    issue_date = models.DateField(blank=True, null=True)
    due_date = models.DateField(blank=True, null=True)
    paid_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        db_table = 'invoices'
        ordering = ['-issue_date']
        indexes = [
            models.Index(fields=['invoice_number']),
            models.Index(fields=['client_id', 'status']),
            models.Index(fields=['due_date', 'status']),
            models.Index(fields=['wo_id']),
        ]

    def __str__(self):
        return f"INV-{self.invoice_number}: Cliente {self.client_id} (${self.total_amount})"
    
    @property
    def client(self):
        """Compatibility property for accessing client"""
        if self.client_id:
            try:
                return Client.objects.get(client_id=self.client_id)
            except Client.DoesNotExist:
                return None
        return None
    
    @property
    def work_order(self):
        """Compatibility property for accessing work order"""
        if self.wo_id:
            try:
                return WorkOrder.objects.get(wo_id=self.wo_id)
            except WorkOrder.DoesNotExist:
                return None
        return None
    
    @property
    def invoice_date(self):
        """Compatibility property"""
        return self.issue_date

    @property
    def is_overdue(self):
        from django.utils import timezone
        if self.due_date:
            return self.due_date < timezone.now().date() and self.status not in ['paid', 'cancelled']
        return False


# =============================================================================
# DOC SCHEMA - Document Management
# =============================================================================

class Document(models.Model):
    """Document storage and management"""
    DOCUMENT_TYPES = [
        ('invoice', 'Invoice'),
        ('estimate', 'Estimate'),
        ('photo', 'Photo'),
        ('manual', 'Manual'),
        ('certificate', 'Certificate'),
        ('report', 'Report'),
        ('other', 'Other'),
    ]

    document_id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    file_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    file_size = models.BigIntegerField()
    mime_type = models.CharField(max_length=100)
    ref_entity = models.CharField(max_length=30, blank=True, null=True)
    ref_id = models.IntegerField(blank=True, null=True)
    is_public = models.BooleanField(default=False)
    uploaded_by = models.ForeignKey(Technician, on_delete=models.SET_NULL, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'documents'
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['document_type']),
            models.Index(fields=['ref_entity', 'ref_id']),
            models.Index(fields=['uploaded_by']),
        ]

    def __str__(self):
        return f"{self.document_type.title()}: {self.title}"


# =============================================================================
# CAT SCHEMA - Additional Catalog Models
# =============================================================================

class Fitment(models.Model):
    """Fitment compatibility between products and equipment"""
    fitment_id = models.AutoField(primary_key=True)
    internal_sku = models.CharField(max_length=20, db_column='internal_sku', blank=True, null=True)
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, db_column='equipment_id')
    score = models.SmallIntegerField(default=100)
    notes = models.TextField(blank=True, null=True)
    verified_by = models.ForeignKey(Technician, on_delete=models.SET_NULL, db_column='verified_by', blank=True, null=True)
    verified_date = models.DateField(blank=True, null=True)
    is_primary_fit = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'fitment'
        unique_together = [['internal_sku', 'equipment']]
        ordering = ['equipment', '-is_primary_fit', '-score']
    
    def __str__(self):
        return f"{self.internal_sku} -> {self.equipment.equipment_code} ({self.score}%)"


# =============================================================================
# INV SCHEMA - Additional Inventory Models
# =============================================================================

class Bin(models.Model):
    """Warehouse bins and storage locations"""
    bin_id = models.AutoField(primary_key=True)
    warehouse_code = models.ForeignKey(Warehouse, on_delete=models.CASCADE, db_column='warehouse_code', to_field='warehouse_code')
    bin_code = models.CharField(max_length=30)
    description = models.CharField(max_length=100, blank=True, null=True)
    zone = models.CharField(max_length=30, blank=True, null=True)
    aisle = models.CharField(max_length=10, blank=True, null=True)
    rack = models.CharField(max_length=10, blank=True, null=True)
    level = models.CharField(max_length=10, blank=True, null=True)
    position = models.CharField(max_length=10, blank=True, null=True)
    capacity = models.IntegerField(blank=True, null=True)
    max_weight_kg = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    current_occupancy = models.IntegerField(default=0)
    temperature_zone = models.CharField(max_length=20, blank=True, null=True)
    hazard_level = models.CharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'bins'
        unique_together = [['warehouse_code', 'bin_code']]
        ordering = ['warehouse_code', 'zone', 'aisle', 'rack', 'level', 'position']
    
    def __str__(self):
        return f"{self.warehouse_code.warehouse_code}/{self.bin_code}"


class PriceList(models.Model):
    """Price lists for products"""
    price_list_id = models.AutoField(primary_key=True)
    price_list_code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    currency_code = models.CharField(max_length=3, blank=True, null=True)
    is_tax_included = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    valid_from = models.DateField(default=date.today)
    valid_until = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'price_lists'
        ordering = ['price_list_code']
    
    def __str__(self):
        return f"{self.name} ({self.price_list_code})"


class ProductPrice(models.Model):
    """Product prices by price list"""
    product_price_id = models.AutoField(primary_key=True)
    price_list = models.ForeignKey(PriceList, on_delete=models.CASCADE, db_column='price_list_id')
    internal_sku = models.CharField(max_length=20, db_column='internal_sku')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    min_qty = models.IntegerField(default=1)
    valid_from = models.DateField(default=date.today)
    valid_until = models.DateField(blank=True, null=True)
    
    class Meta:
        db_table = 'product_prices'
        unique_together = [['price_list', 'internal_sku', 'valid_from']]
        ordering = ['price_list', 'internal_sku', '-valid_from']
    
    def __str__(self):
        return f"{self.price_list.price_list_code} - {self.internal_sku}: {self.unit_price}"


class PurchaseOrder(models.Model):
    """Purchase orders"""
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('APPROVED', 'Approved'),
        ('ORDERED', 'Ordered'),
        ('RECEIVED', 'Received'),
        ('PARTIAL', 'Partially Received'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    po_id = models.AutoField(primary_key=True)
    po_number = models.CharField(max_length=30, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, db_column='supplier_id')
    order_date = models.DateField(default=date.today)
    expected_delivery_date = models.DateField(blank=True, null=True)
    actual_delivery_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    created_by = models.ForeignKey(Technician, on_delete=models.SET_NULL, db_column='created_by', blank=True, null=True)
    approved_by = models.ForeignKey(Technician, on_delete=models.SET_NULL, db_column='approved_by', related_name='approved_purchase_orders', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'purchase_orders'
        ordering = ['-order_date', 'po_number']
    
    def __str__(self):
        return f"{self.po_number} - {self.supplier.name}"


class POItem(models.Model):
    """Purchase order line items"""
    po_item_id = models.AutoField(primary_key=True)
    po = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, db_column='po_id')
    internal_sku = models.CharField(max_length=20, db_column='internal_sku', blank=True, null=True)
    supplier_sku = models.ForeignKey(
        'SupplierSKU', 
        on_delete=models.SET_NULL, 
        db_column='supplier_sku_id',
        blank=True, 
        null=True,
        related_name='po_items',
        help_text="Reference to supplier SKU mapping"
    )
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    quantity_received = models.IntegerField(default=0)
    quantity_rejected = models.IntegerField(default=0)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'po_items'
        ordering = ['po', 'po_item_id']
    
    def __str__(self):
        return f"{self.po.po_number} - {self.internal_sku if self.internal_sku else 'N/A'} x{self.quantity}"


# =============================================================================
# OEM SCHEMA - OEM Catalog Models
# =============================================================================

class BrandType(models.Model):
    """
    Catálogo de tipos de marca (referencia). Escalable: se gestiona desde BD
    sin desplegar código. OEMBrand.brand_type almacena el code de aquí.
    """
    code = models.CharField(max_length=20, primary_key=True)
    name_es = models.CharField(max_length=80)
    name_en = models.CharField(max_length=80, blank=True, null=True)
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = '"oem"."brand_types"'
        ordering = ['display_order', 'code']
        verbose_name = 'Tipo de marca'
        verbose_name_plural = 'Tipos de marca'

    def __str__(self):
        return self.name_es or self.code


class OEMBrand(models.Model):
    """Universal brands and manufacturers (vehicles, equipment, parts)"""
    # Valores por defecto para compatibilidad y get_brand_type_display() si no hay BrandType
    BRAND_TYPES = [
        ('VEHICLE_MFG', 'Vehicle Manufacturer'),
        ('EQUIPMENT_MFG', 'Equipment Manufacturer'),
        ('PARTS_SUPPLIER', 'Parts Supplier'),
        ('MIXED', 'Mixed (Manufacturer & Supplier)'),
    ]

    brand_id = models.AutoField(primary_key=True)
    oem_code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=50)
    brand_type = models.CharField(max_length=20, choices=BRAND_TYPES, default='PARTS_SUPPLIER',
                                   help_text='Type of brand: vehicle manufacturer, equipment manufacturer, or parts supplier')
    country = models.CharField(max_length=50, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    support_email = models.EmailField(blank=True, null=True)
    logo_url = models.URLField(blank=True, null=True, help_text='URL to brand logo image')
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0, help_text='Order for display in lists')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'oem_brands'
        ordering = ['display_order', 'name']

    def get_brand_type_label(self):
        """Etiqueta del tipo: desde catálogo BrandType si existe, si no desde choices."""
        try:
            bt = BrandType.objects.get(pk=self.brand_type)
            return bt.name_es or bt.code
        except (BrandType.DoesNotExist, Exception):
            return self.get_brand_type_display()
    
    def __str__(self):
        return f"{self.name} ({self.oem_code})"


class OEMCatalogItem(models.Model):
    """Universal catalog items (vehicle models, equipment models, parts)"""
    ITEM_TYPES = [
        ('VEHICLE_MODEL', 'Vehicle Model'),
        ('EQUIPMENT_MODEL', 'Equipment Model'),
        ('PART', 'Part/Component'),
    ]
    
    PART_NUMBER_TYPES = [
        ('BASIC_5', 'Basic 5'),
        ('DESIGN_5', 'Design 5'),
        ('FULL_12', 'Full 12'),
    ]
    
    catalog_id = models.AutoField(primary_key=True)
    oem_code = models.ForeignKey(OEMBrand, on_delete=models.CASCADE, db_column='oem_code', to_field='oem_code')
    item_type = models.CharField(max_length=20, choices=ITEM_TYPES, default='PART',
                                  help_text='Type of item: vehicle model, equipment model, or part')
    part_number = models.CharField(max_length=30, help_text='Part number or model code')
    part_number_type = models.CharField(max_length=15, choices=PART_NUMBER_TYPES, blank=True, null=True)
    description_es = models.TextField(blank=True, null=True)
    description_en = models.TextField(blank=True, null=True)
    group_code = models.ForeignKey(TaxonomyGroup, on_delete=models.SET_NULL, db_column='group_code', blank=True, null=True)
    
    # Vehicle/Equipment Model specific fields
    body_style = models.CharField(max_length=50, blank=True, null=True, 
                                   help_text='For vehicles/equipment: Sedan, SUV, Pickup, etc.')
    year_start = models.SmallIntegerField(blank=True, null=True, 
                                           help_text='First year of production')
    year_end = models.SmallIntegerField(blank=True, null=True, 
                                         help_text='Last year of production (null if still in production)')
    
    # Part specific fields
    weight_kg = models.DecimalField(max_digits=8, decimal_places=3, blank=True, null=True)
    dimensions = models.CharField(max_length=100, blank=True, null=True)
    material = models.CharField(max_length=50, blank=True, null=True)
    
    # Imagen principal del producto
    primary_image_url = models.URLField(max_length=500, blank=True, null=True,
                                         help_text='URL de la imagen principal del producto')
    
    # Fitment information (for parts)
    vin_patterns = models.JSONField(default=list, blank=True)
    model_codes = models.JSONField(default=list, blank=True)
    body_codes = models.JSONField(default=list, blank=True)
    engine_codes = models.JSONField(default=list, blank=True)
    transmission_codes = models.JSONField(default=list, blank=True)
    axle_codes = models.JSONField(default=list, blank=True)
    color_codes = models.JSONField(default=list, blank=True)
    trim_codes = models.JSONField(default=list, blank=True)
    manual_types = models.JSONField(default=list, blank=True)
    manual_refs = models.JSONField(default=list, blank=True)
    
    # Pricing
    list_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    net_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    currency_code = models.CharField(max_length=3, default='USD')
    oem_lead_time_days = models.IntegerField(blank=True, null=True)
    
    # Status
    is_discontinued = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    valid_from = models.DateField(blank=True, null=True)
    valid_until = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'catalog_items'
        unique_together = [['oem_code', 'part_number']]
        ordering = ['oem_code', 'display_order', 'part_number']
    
    def __str__(self):
        if self.item_type in ['VEHICLE_MODEL', 'EQUIPMENT_MODEL']:
            return f"{self.oem_code.name} {self.part_number}"
        return f"{self.oem_code.oem_code} {self.part_number}"


class OEMPartImage(models.Model):
    """
    Imágenes técnicas para partes OEM.
    Maneja múltiples tipos de imágenes incluyendo:
    - Figuras isométricas (vistas 3D del conjunto)
    - Diagramas arquitectónicos (exploded views)
    - Vistas detalladas de componentes
    - Diagramas de instalación
    - Imágenes de referencia
    """
    IMAGE_TYPES = [
        ('PRIMARY', 'Imagen Principal'),
        ('ISOMETRIC', 'Figura Isométrica'),
        ('EXPLODED', 'Vista Explodida'),
        ('DIAGRAM', 'Diagrama Arquitectónico'),
        ('DETAIL', 'Vista Detallada'),
        ('INSTALLATION', 'Diagrama de Instalación'),
        ('REFERENCE', 'Imagen de Referencia'),
        ('THUMBNAIL', 'Miniatura'),
        ('OTHER', 'Otro'),
    ]
    
    image_id = models.AutoField(primary_key=True)
    catalog_item = models.ForeignKey(
        OEMCatalogItem, 
        on_delete=models.CASCADE, 
        db_column='catalog_id',
        related_name='technical_images'
    )
    image_type = models.CharField(
        max_length=20, 
        choices=IMAGE_TYPES, 
        default='PRIMARY',
        help_text='Tipo de imagen técnica'
    )
    image_url = models.URLField(
        max_length=500,
        help_text='URL de la imagen'
    )
    thumbnail_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text='URL de la miniatura (opcional)'
    )
    title = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text='Título descriptivo de la imagen'
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text='Descripción de la imagen o notas técnicas'
    )
    # Coordenadas para hotspots en la imagen (para interactive diagrams)
    hotspot_data = models.JSONField(
        default=list,
        blank=True,
        help_text='Datos de hotspots para diagramas interactivos [{x, y, part_number, label}]'
    )
    # Posición del número de parte en el diagrama
    part_position = models.JSONField(
        default=dict,
        blank=True,
        help_text='Posición del número de parte en el diagrama {x, y, page_number}'
    )
    # Información de página para diagramas de múltiples páginas
    page_number = models.IntegerField(
        blank=True,
        null=True,
        help_text='Número de página si es parte de un diagrama de múltiples páginas'
    )
    total_pages = models.IntegerField(
        blank=True,
        null=True,
        help_text='Total de páginas del diagrama si es un documento de múltiples páginas'
    )
    # Dimensiones de la imagen original
    image_width = models.IntegerField(
        blank=True,
        null=True,
        help_text='Ancho original de la imagen en píxeles'
    )
    image_height = models.IntegerField(
        blank=True,
        null=True,
        help_text='Alto original de la imagen en píxeles'
    )
    # Metadata
    file_size = models.BigIntegerField(
        blank=True,
        null=True,
        help_text='Tamaño del archivo en bytes'
    )
    mime_type = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text='Tipo MIME del archivo (ej: image/jpeg, application/pdf)'
    )
    # Códigos de referencia en el diagrama
    reference_codes = models.JSONField(
        default=list,
        blank=True,
        help_text='Lista de códigos de parte referenciados en el diagrama'
    )
    # Orden de visualización
    display_order = models.IntegerField(
        default=0,
        help_text='Orden para mostrar en galerías'
    )
    # Estado
    is_active = models.BooleanField(
        default=True,
        help_text='Si la imagen está activa y visible'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        # PostgreSQL: schema.tabla debe ir como "oem"."oem_part_images" (o "oem"."part_images" si la tabla se llama part_images).
        db_table = '"oem"."oem_part_images"'
        ordering = ['catalog_item', 'display_order', 'image_type']
        verbose_name_plural = 'OEM Part Images'
    
    def __str__(self):
        return f"{self.catalog_item.part_number} - {self.get_image_type_display()}"


class OEMEquivalence(models.Model):
    """OEM to aftermarket part equivalences"""
    EQUIVALENCE_TYPES = [
        ('DIRECT', 'Direct'),
        ('COMPATIBLE', 'Compatible'),
        ('UPGRADE', 'Upgrade'),
        ('DOWNGRADE', 'Downgrade'),
    ]
    
    equivalence_id = models.AutoField(primary_key=True)
    oem_part_number = models.CharField(max_length=30)
    oem_code = models.ForeignKey(OEMBrand, on_delete=models.CASCADE, db_column='oem_code', to_field='oem_code')
    aftermarket_sku = models.CharField(max_length=20, db_column='aftermarket_sku', blank=True, null=True)
    equivalence_type = models.CharField(max_length=20, choices=EQUIVALENCE_TYPES, blank=True, null=True)
    confidence_score = models.IntegerField(blank=True, null=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    notes = models.TextField(blank=True, null=True)
    verified_by = models.ForeignKey(Technician, on_delete=models.SET_NULL, db_column='verified_by', blank=True, null=True)
    verified_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        # PostgreSQL requiere "schema"."tabla" (cada uno entre comillas). Con 'oem.equivalences'
        # Django genera "oem.equivalences" (un solo identificador) y la relación no existe.
        db_table = '"oem"."equivalences"'
        unique_together = [['oem_part_number', 'oem_code', 'aftermarket_sku']]
        ordering = ['oem_code', 'oem_part_number']
    
    def __str__(self):
        return f"{self.oem_code.oem_code} {self.oem_part_number} = {self.aftermarket_sku if self.aftermarket_sku else 'N/A'}"


# =============================================================================
# SVC SCHEMA - Additional Service Models
# =============================================================================

class WOItem(models.Model):
    """Work order items (parts used)"""
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('RESERVED', 'Reserved'),
        ('USED', 'Used'),
        ('RETURNED', 'Returned'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    item_id = models.AutoField(primary_key=True)
    wo = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, db_column='wo_id')
    internal_sku = models.CharField(max_length=20, db_column='internal_sku', blank=True, null=True)
    qty_ordered = models.DecimalField(max_digits=10, decimal_places=3, default=Decimal('1.0'))
    qty_used = models.DecimalField(max_digits=10, decimal_places=3, default=Decimal('0.0'))
    qty_returned = models.DecimalField(max_digits=10, decimal_places=3, default=Decimal('0.0'))
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    reserved_stock_id = models.BigIntegerField(blank=True, null=True)
    reserved_stock_date = models.DateField(blank=True, null=True)
    used_stock_id = models.BigIntegerField(blank=True, null=True)
    used_stock_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'wo_items'
        ordering = ['wo', 'item_id']
    
    def __str__(self):
        return f"{self.wo.wo_number} - {self.internal_sku if self.internal_sku else 'N/A'} x{self.qty_used}"


class FlatRateStandard(models.Model):
    """Flat rate time standards for services"""
    standard_id = models.AutoField(primary_key=True)
    service_code = models.CharField(max_length=20, unique=True)
    description_es = models.TextField()
    description_en = models.TextField(blank=True, null=True)
    equipment_type = models.ForeignKey(EquipmentType, on_delete=models.SET_NULL, db_column='equipment_type_id', blank=True, null=True)
    group_code = models.ForeignKey(TaxonomyGroup, on_delete=models.SET_NULL, db_column='group_code', blank=True, null=True)
    standard_hours = models.DecimalField(max_digits=5, decimal_places=2)
    min_hours = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    max_hours = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    difficulty_level = models.IntegerField(blank=True, null=True)
    required_tools = models.JSONField(default=list, blank=True)
    required_skills = models.JSONField(default=list, blank=True)
    manual_source = models.CharField(max_length=50, blank=True, null=True)
    manual_ref = models.CharField(max_length=100, blank=True, null=True)
    oem_ref = models.CharField(max_length=30, blank=True, null=True)
    valid_from = models.DateField(default=date.today)
    valid_until = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'flat_rate_standards'
        ordering = ['service_code']
    
    def __str__(self):
        return f"{self.service_code} - {self.standard_hours}h"


class WOService(models.Model):
    """Work order services (labor tasks)"""
    COMPLETION_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('SKIPPED', 'Skipped'),
    ]
    
    service_id = models.AutoField(primary_key=True)
    wo = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, db_column='wo_id')
    flat_rate = models.ForeignKey(FlatRateStandard, on_delete=models.SET_NULL, db_column='flat_rate_id', blank=True, null=True)
    service_code = models.CharField(max_length=20, blank=True, null=True)
    description = models.TextField()
    flat_hours = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    estimated_hours = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    actual_hours = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    completion_status = models.CharField(max_length=20, choices=COMPLETION_STATUS_CHOICES, default='PENDING')
    technician = models.ForeignKey(Technician, on_delete=models.SET_NULL, db_column='technician_id', blank=True, null=True)
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'wo_services'
        ordering = ['wo', 'service_id']
    
    def __str__(self):
        return f"{self.wo.wo_number} - {self.description[:50]}"


class ServiceChecklist(models.Model):
    """Service checklists for flat rate standards"""
    checklist_id = models.AutoField(primary_key=True)
    flat_rate = models.ForeignKey(FlatRateStandard, on_delete=models.CASCADE, db_column='flat_rate_id', blank=True, null=True)
    description = models.TextField()
    sequence_no = models.IntegerField()
    is_critical = models.BooleanField(default=False)
    expected_result = models.CharField(max_length=100, blank=True, null=True)
    tool_required = models.CharField(max_length=100, blank=True, null=True)
    estimated_minutes = models.IntegerField(blank=True, null=True)
    
    class Meta:
        db_table = 'service_checklists'
        unique_together = [['flat_rate', 'sequence_no']]
        ordering = ['flat_rate', 'sequence_no']
    
    def __str__(self):
        return f"{self.flat_rate.service_code if self.flat_rate else 'N/A'} - Step {self.sequence_no}"


class InvoiceItem(models.Model):
    """Invoice line items"""
    invoice_item_id = models.AutoField(primary_key=True)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, db_column='invoice_id')
    internal_sku = models.CharField(max_length=20, db_column='internal_sku', blank=True, null=True)
    description = models.TextField()
    qty = models.DecimalField(max_digits=10, decimal_places=3)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    
    class Meta:
        db_table = 'invoice_items'
        ordering = ['invoice', 'invoice_item_id']
    
    def __str__(self):
        return f"{self.invoice.invoice_number} - {self.description[:50]}"


class Payment(models.Model):
    """Payments against invoices"""
    PAYMENT_METHODS = [
        ('CASH', 'Cash'),
        ('CHECK', 'Check'),
        ('CARD', 'Credit/Debit Card'),
        ('TRANSFER', 'Bank Transfer'),
        ('OTHER', 'Other'),
    ]
    
    payment_id = models.AutoField(primary_key=True)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, db_column='invoice_id')
    payment_date = models.DateField(default=date.today)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency_code = models.CharField(max_length=3, blank=True, null=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    reference_number = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'payments'
        ordering = ['-payment_date', 'invoice']
    
    def __str__(self):
        return f"{self.invoice.invoice_number} - {self.amount} ({self.payment_method})"


class Quote(models.Model):
    """Service quotes/estimates"""
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SENT', 'Sent'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('EXPIRED', 'Expired'),
        ('CONVERTED', 'Converted to Work Order'),
    ]
    
    quote_id = models.AutoField(primary_key=True)
    quote_number = models.CharField(max_length=20, unique=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, db_column='client_id')
    equipment = models.ForeignKey(Equipment, on_delete=models.SET_NULL, db_column='equipment_id', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    quote_date = models.DateField(default=date.today)
    valid_until = models.DateField(blank=True, null=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('16.00'))
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_hours = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    currency_code = models.CharField(max_length=3, default='MXN')
    notes = models.TextField(blank=True, null=True)
    terms_and_conditions = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, related_name='quotes_created', blank=True, null=True)
    converted_to_wo = models.ForeignKey(WorkOrder, on_delete=models.SET_NULL, db_column='converted_to_wo_id', blank=True, null=True, related_name='source_quote')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'quotes'
        ordering = ['-quote_date', '-quote_number']
    
    def __str__(self):
        return f"{self.quote_number} - {self.client.name if self.client else 'N/A'}"
    
    def calculate_totals(self):
        """Calculate quote totals from items"""
        items = self.items.all()
        self.subtotal = sum(item.line_total for item in items)
        self.discount_amount = self.subtotal * (self.discount_percent / 100)
        after_discount = self.subtotal - self.discount_amount
        self.tax_amount = after_discount * (self.tax_percent / 100)
        self.total = after_discount + self.tax_amount
        self.total_hours = sum(item.hours * item.quantity for item in items)
        self.save()
    
    def generate_quote_number(self):
        """Generate unique quote number"""
        from datetime import datetime
        today = datetime.now()
        prefix = f"QT-{today.strftime('%Y%m')}"
        
        # Get last quote number for this month
        last_quote = Quote.objects.filter(
            quote_number__startswith=prefix
        ).order_by('-quote_number').first()
        
        if last_quote:
            try:
                last_num = int(last_quote.quote_number.split('-')[-1])
                new_num = last_num + 1
            except (ValueError, IndexError):
                new_num = 1
        else:
            new_num = 1
        
        self.quote_number = f"{prefix}-{new_num:04d}"
        return self.quote_number


class QuoteItem(models.Model):
    """Quote line items (services)"""
    quote_item_id = models.AutoField(primary_key=True)
    quote = models.ForeignKey(Quote, on_delete=models.CASCADE, db_column='quote_id', related_name='items')
    flat_rate = models.ForeignKey(FlatRateStandard, on_delete=models.SET_NULL, db_column='flat_rate_id', blank=True, null=True)
    service_code = models.CharField(max_length=20, blank=True, null=True)
    description = models.TextField()
    quantity = models.IntegerField(default=1)
    hours = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('500.00'))
    line_total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'quote_items'
        ordering = ['quote', 'quote_item_id']
    
    def __str__(self):
        return f"{self.quote.quote_number} - {self.description[:50]}"
    
    def save(self, *args, **kwargs):
        """Calculate line total before saving"""
        self.line_total = self.hours * self.hourly_rate * self.quantity
        super().save(*args, **kwargs)


# =============================================================================
# KPI SCHEMA - Key Performance Indicators
# =============================================================================

class WOMetric(models.Model):
    """Work order performance metrics"""
    metric_id = models.AutoField(primary_key=True)
    wo = models.OneToOneField(WorkOrder, on_delete=models.CASCADE, db_column='wo_id')
    efficiency_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    productivity_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    quality_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    customer_satisfaction = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    lead_time_days = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    process_time_days = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    wait_time_days = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    parts_fill_rate = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    parts_accuracy = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    return_rate = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    profitability = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    labor_utilization = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'wo_metrics'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Metrics for WO {self.wo.wo_number}"


# =============================================================================
# AUTH SCHEMA - Authentication and User Management (DEPRECATED - using TechnicianUser instead)
# =============================================================================

# class UserProfile(models.Model):
#     """
#     Extended user profile that links Django users with Technicians
#     DEPRECATED: Use TechnicianUser instead
#     """
#     user = models.OneToOneField(
#         'auth.User',
#         on_delete=models.CASCADE,
#         related_name='profile'
#     )
#     
#     technician = models.OneToOneField(
#         Technician, 
#         on_delete=models.CASCADE, 
#         null=True, 
#         blank=True,
#         related_name='user_profile'
#     )
#     
#     # Additional fields for role-based access
#     role = models.CharField(
#         max_length=20,
#         choices=[
#             ('admin', 'Administrator'),
#             ('manager', 'Manager'),
#             ('technician', 'Technician'),
#             ('viewer', 'Viewer'),
#         ],
#         default='technician'
#     )
#     
#     is_workshop_admin = models.BooleanField(default=False)
#     can_manage_inventory = models.BooleanField(default=False)
#     can_manage_clients = models.BooleanField(default=False)
#     can_view_reports = models.BooleanField(default=True)
#     
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     
#     class Meta:
#         db_table = 'auth_user_profile'
#         verbose_name = 'User Profile'
#         verbose_name_plural = 'User Profiles'
#     
#     def __str__(self):
#         if self.technician:
#             return f"{self.technician.full_name} ({self.user.username})"
#         return self.user.username
#     
#     @property
#     def full_name(self):
#         if self.technician:
#             return self.technician.full_name
#         return f"{self.user.first_name} {self.user.last_name}".strip()
#     
#     def get_tokens(self):
#         """Generate JWT tokens for this user"""
#         from rest_framework_simplejwt.tokens import RefreshToken
#         refresh = RefreshToken.for_user(self.user)
#         return {
#             'refresh': str(refresh),
#             'access': str(refresh.access_token),
#         }
#     
#     def has_workshop_permission(self, permission):
#         """Check if user has specific workshop permission"""
#         if self.user.is_superuser or self.is_workshop_admin:
#             return True
#             
#         permission_map = {
#             'manage_inventory': self.can_manage_inventory,
#             'manage_clients': self.can_manage_clients,
#             'view_reports': self.can_view_reports,
#         }
#         
#         return permission_map.get(permission, False)


# =============================================================================
# AUTHENTICATION - Custom User Model (COMMENTED OUT - using standard Django User)
# =============================================================================

# from django.contrib.auth.models import AbstractUser

# class TechnicianUser(AbstractUser):
#     """
#     Custom user model that extends Django's AbstractUser
#     and links to the Technician model for workshop operations
#     """
#     
#     # Link to technician profile
#     technician = models.OneToOneField(
#         Technician, 
#         on_delete=models.CASCADE, 
#         null=True, 
#         blank=True,
#         related_name='user_account'
#     )
#     
#     # Additional fields for role-based access
#     role = models.CharField(
#         max_length=20,
#         choices=[
#             ('admin', 'Administrator'),
#             ('manager', 'Manager'),
#             ('technician', 'Technician'),
#             ('viewer', 'Viewer'),
#         ],
#         default='technician'
#     )
#     
#     is_workshop_admin = models.BooleanField(default=False)
#     can_manage_inventory = models.BooleanField(default=False)
#     can_manage_clients = models.BooleanField(default=False)
#     can_view_reports = models.BooleanField(default=True)
#     
#     class Meta:
#         db_table = 'auth_technician_user'
#         verbose_name = 'Technician User'
#         verbose_name_plural = 'Technician Users'
#     
#     def __str__(self):
#         if self.technician:
#             return f"{self.technician.full_name} ({self.username})"
#         return self.username
#     
#     @property
#     def full_name(self):
#         if self.technician:
#             return self.technician.full_name
#         return f"{self.first_name} {self.last_name}".strip()
#     
#     def get_tokens(self):
#         """Generate JWT tokens for this user"""
#         from rest_framework_simplejwt.tokens import RefreshToken
#         refresh = RefreshToken.for_user(self)
#         return {
#             'refresh': str(refresh),
#             'access': str(refresh.access_token),
#         }
#     
#     def has_workshop_permission(self, permission):
#         """Check if user has specific workshop permission"""
#         if self.is_superuser or self.is_workshop_admin:
#             return True
#             
#         permission_map = {
#             'manage_inventory': self.can_manage_inventory,
#             'manage_clients': self.can_manage_clients,
#             'view_reports': self.can_view_reports,
#         }
#         
#         return permission_map.get(permission, False)


# =============================================================================
# AUTHENTICATION - Proxy User Model for Workshop Operations
# =============================================================================

from django.contrib.auth.models import User

class TechnicianUser(User):
    """
    Proxy model for Django's User that adds workshop-specific functionality
    """
    
    class Meta:
        proxy = True
        verbose_name = 'Technician User'
        verbose_name_plural = 'Technician Users'
    
    def get_technician(self):
        """Get the associated technician profile"""
        try:
            # Try to find technician by username (employee_code)
            return Technician.objects.get(employee_code=self.username, status='active')
        except Technician.DoesNotExist:
            return None
    
    @property
    def technician(self):
        """Property to access technician profile"""
        return self.get_technician()
    
    @property
    def full_name(self):
        """Get full name from technician or user fields"""
        technician = self.get_technician()
        if technician:
            return technician.full_name
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_tokens(self):
        """Generate JWT tokens for this user"""
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(self)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
    
    def has_workshop_permission(self, permission):
        """Check if user has specific workshop permission"""
        if self.is_superuser or self.is_staff:
            return True
            
        # For now, all authenticated users have basic permissions
        # This can be extended with groups and permissions later
        return True
    
    @property
    def is_workshop_admin(self):
        """Check if user is workshop admin"""
        return self.is_superuser or self.is_staff
    
    @property
    def can_manage_inventory(self):
        """Check if user can manage inventory"""
        return self.has_workshop_permission('manage_inventory')
    
    @property
    def can_manage_clients(self):
        """Check if user can manage clients"""
        return self.has_workshop_permission('manage_clients')
    
    @property
    def can_view_reports(self):
        """Check if user can view reports"""
        return self.has_workshop_permission('view_reports')


# =============================================================================
# INV SCHEMA - Supplier SKU Mapping
# =============================================================================

class SupplierSKU(models.Model):
    """
    Mapping table for supplier-specific SKUs.
    Allows multiple suppliers per product and multiple SKUs per supplier.
    """
    supplier_sku_id = models.AutoField(primary_key=True)
    internal_sku = models.ForeignKey(
        ProductMaster, 
        on_delete=models.CASCADE, 
        db_column='internal_sku',
        to_field='internal_sku',
        related_name='supplier_skus'
    )
    supplier = models.ForeignKey(
        Supplier, 
        on_delete=models.CASCADE, 
        db_column='supplier_id',
        related_name='supplier_skus'
    )
    supplier_sku_code = models.CharField(
        max_length=50, 
        blank=True, 
        null=True,
        help_text="Supplier's SKU/code for this product"
    )
    supplier_mpn = models.CharField(
        max_length=50, 
        blank=True, 
        null=True,
        help_text="Manufacturer's Part Number from supplier"
    )
    is_preferred = models.BooleanField(
        default=False,
        help_text="Preferred supplier for this product"
    )
    unit_cost = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00'),
        blank=True, 
        null=True,
        help_text="Last purchase cost from this supplier"
    )
    lead_time_days = models.IntegerField(
        default=7,
        blank=True, 
        null=True,
        help_text="Average lead time in days"
    )
    min_order_qty = models.IntegerField(
        default=1,
        blank=True, 
        null=True
    )
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'supplier_skus'
        unique_together = [['internal_sku', 'supplier']]
        ordering = ['supplier', 'internal_sku']
        indexes = [
            models.Index(fields=['supplier', 'internal_sku']),
            models.Index(fields=['supplier_sku_code']),
            models.Index(fields=['supplier_mpn']),
        ]
    
    def __str__(self):
        return f"{self.supplier.name} - {self.internal_sku.internal_sku} -> {self.supplier_sku_code or 'N/A'}"
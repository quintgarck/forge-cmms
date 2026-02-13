"""
Supplier forms for the frontend application.
Contains forms for creating, updating, and filtering suppliers.
"""
import re
from django import forms
from django.core.validators import EmailValidator, URLValidator
from django.core.exceptions import ValidationError


def phone_validator(value):
    """Validate phone number format"""
    if not value:
        return
    
    # Remove spaces, parentheses, hyphens and dots
    clean_value = re.sub(r'[\s\-\(\)\.]', '', value)
    
    # Allow formats like: 5512345678, (55) 1234-5678, 55 1234 5678
    if not re.match(r'^[\+]?[1-9][\d]{0,15}$', clean_value):
        raise ValidationError(
            'Formato de teléfono inválido. Ejemplos válidos: 5512345678, (55) 1234-5678, +1234567890'
        )


class SupplierBaseForm(forms.Form):
    """Base form for supplier with common fields and validation"""
    
    # Basic Information
    supplier_code = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'PROV-001',
            'maxlength': '20',
            'autocomplete': 'off'
        }),
        label='Código del Proveedor',
        help_text='Código único para identificar al proveedor'
    )
    
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre del proveedor',
            'maxlength': '100',
            'autocomplete': 'organization'
        }),
        label='Nombre del Proveedor',
        help_text='Nombre comercial o razón social del proveedor'
    )
    
    # Contact Information
    contact_person = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre del contacto principal',
            'maxlength': '100',
            'autocomplete': 'name'
        }),
        label='Persona de Contacto',
        help_text='Nombre de la persona principal de contacto'
    )
    
    contact_email = forms.EmailField(
        required=False,
        validators=[EmailValidator()],
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'contacto@proveedor.com',
            'autocomplete': 'email'
        }),
        label='Email de Contacto',
        help_text='Correo electrónico principal de contacto'
    )
    
    contact_phone = forms.CharField(
        max_length=20,
        required=False,
        validators=[phone_validator],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '(55) 1234-5678',
            'maxlength': '20',
            'autocomplete': 'tel'
        }),
        label='Teléfono de Contacto',
        help_text='Número telefónico principal de contacto'
    )
    
    website = forms.URLField(
        required=False,
        validators=[URLValidator()],
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://www.proveedor.com',
            'autocomplete': 'url'
        }),
        label='Sitio Web',
        help_text='Página web oficial del proveedor'
    )
    
    # Address Information
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Calle Principal #123, Colonia Centro',
            'rows': 3,
            'maxlength': '500'
        }),
        label='Dirección',
        help_text='Dirección completa del proveedor'
    )
    
    city = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ciudad de México',
            'maxlength': '50',
            'autocomplete': 'address-level2'
        }),
        label='Ciudad',
        help_text='Ciudad donde se encuentra el proveedor'
    )
    
    state = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'CDMX',
            'maxlength': '50',
            'autocomplete': 'address-level1'
        }),
        label='Estado/Provincia',
        help_text='Estado o provincia del proveedor'
    )
    
    country = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'México',
            'maxlength': '50',
            'autocomplete': 'country'
        }),
        label='País',
        help_text='País del proveedor'
    )
    
    # Business Information
    tax_id = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'RFC o identificación fiscal',
            'maxlength': '30'
        }),
        label='Identificación Fiscal',
        help_text='RFC, CIF u otro identificador fiscal'
    )
    
    payment_terms = forms.IntegerField(
        initial=30,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0',
            'max': '365',
            'step': '1'
        }),
        label='Términos de Pago',
        help_text='Días de crédito otorgados (por defecto: 30 días)'
    )
    
    currency_code = forms.ChoiceField(
        choices=[
            ('MXN', 'MXN - Peso Mexicano'),
            ('USD', 'USD - Dólar Estadounidense'),
            ('EUR', 'EUR - Euro'),
            ('CAD', 'CAD - Dólar Canadiense'),
            ('GBP', 'GBP - Libra Esterlina'),
        ],
        initial='MXN',
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Moneda',
        help_text='Moneda utilizada para transacciones'
    )
    
    # Status and Preferences
    status = forms.ChoiceField(
        choices=[
            ('ACTIVE', 'Activo'),
            ('INACTIVE', 'Inactivo'),
            ('SUSPENDED', 'Suspendido'),
        ],
        initial='ACTIVE',
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Estado',
        help_text='Estado actual del proveedor'
    )
    
    is_preferred = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Proveedor Preferido',
        help_text='Marcar si este es un proveedor preferencial'
    )
    
    # Additional Information
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Observaciones adicionales sobre el proveedor...',
            'rows': 4,
            'maxlength': '1000'
        }),
        label='Notas',
        help_text='Información adicional relevante'
    )
    
    def clean_supplier_code(self):
        """Clean and validate supplier code"""
        code = self.cleaned_data.get('supplier_code', '').strip().upper()
        if not code:
            raise ValidationError('El código del proveedor es obligatorio.')
        return code
    
    def clean_name(self):
        """Clean and validate supplier name"""
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise ValidationError('El nombre del proveedor es obligatorio.')
        return name
    
    def clean_payment_terms(self):
        """Validate payment terms"""
        terms = self.cleaned_data.get('payment_terms')
        if terms is not None and (terms < 0 or terms > 365):
            raise ValidationError('Los términos de pago deben estar entre 0 y 365 días.')
        return terms


class SupplierCreateForm(SupplierBaseForm):
    """Form for creating new suppliers"""
    pass


class SupplierUpdateForm(SupplierBaseForm):
    """Form for updating existing suppliers"""
    pass


class SupplierFilterForm(forms.Form):
    """Form for filtering supplier lists"""
    
    SEARCH_CHOICES = [
        ('name', 'Nombre'),
        ('supplier_code', 'Código'),
        ('contact_person', 'Contacto'),
        ('contact_email', 'Email'),
    ]
    
    SORT_CHOICES = [
        ('name', 'Nombre (A-Z)'),
        ('-name', 'Nombre (Z-A)'),
        ('supplier_code', 'Código (A-Z)'),
        ('-supplier_code', 'Código (Z-A)'),
        ('created_at', 'Más Antiguos'),
        ('-created_at', 'Más Recientes'),
        ('rating', 'Calificación (Menor-Mayor)'),
        ('-rating', 'Calificación (Mayor-Menor)'),
    ]
    
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control search-input',
            'placeholder': 'Buscar proveedores...',
            'autocomplete': 'off'
        }),
        label='Buscar'
    )
    
    search_by = forms.ChoiceField(
        choices=SEARCH_CHOICES,
        initial='name',
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Buscar por'
    )
    
    status = forms.ChoiceField(
        choices=[
            ('', 'Todos los estados'),
            ('ACTIVE', 'Activos'),
            ('INACTIVE', 'Inactivos'),
            ('SUSPENDED', 'Suspendidos'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Estado'
    )
    
    sort_by = forms.ChoiceField(
        choices=SORT_CHOICES,
        initial='-created_at',
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Ordenar por'
    )
    
    show_inactive = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Mostrar inactivos',
        help_text='Incluir proveedores inactivos en los resultados'
    )

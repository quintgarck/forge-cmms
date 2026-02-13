"""
Forms para el módulo de Currencies (Monedas)
ForgeDB Frontend Web Application

Este módulo contiene formularios para la gestión completa de monedas,
incluyendo validaciones client-side y server-side.
"""

from django import forms
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
import re


class CurrencyForm(forms.Form):
    """
    Formulario principal para crear y editar monedas
    """
    
    # Validadores
    currency_code_validator = RegexValidator(
        regex=r'^[A-Z]{3}$',
        message="El código de moneda debe ser exactamente 3 letras mayúsculas (ISO 4217)."
    )
    
    symbol_validator = RegexValidator(
        regex=r'^.{1,5}$',
        message="El símbolo debe tener entre 1 y 5 caracteres."
    )
    
    # Campos del formulario
    currency_code = forms.CharField(
        max_length=3,
        min_length=3,
        validators=[currency_code_validator],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'USD',
            'maxlength': '3',
            'minlength': '3',
            'required': True,
            'style': 'text-transform: uppercase;',
            'data-validation': 'currency-code',
            'autocomplete': 'off',
            'pattern': '[A-Z]{3}'
        }),
        label='Código de Moneda',
        help_text='Código ISO 4217 de 3 letras (ej: USD, EUR, MXN)'
    )
    
    name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'US Dollar',
            'maxlength': '50',
            'required': True
        }),
        label='Nombre',
        help_text='Nombre completo de la moneda'
    )
    
    symbol = forms.CharField(
        max_length=5,
        required=False,
        validators=[symbol_validator],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '$',
            'maxlength': '5'
        }),
        label='Símbolo',
        help_text='Símbolo de la moneda (ej: $, €, £)'
    )
    
    exchange_rate = forms.DecimalField(
        max_digits=10,
        decimal_places=4,
        initial=1.0,
        validators=[MinValueValidator(0.0001)],
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '1.0000',
            'step': '0.0001',
            'min': '0.0001',
            'required': True
        }),
        label='Tipo de Cambio',
        help_text='Tipo de cambio respecto a la moneda base (debe ser mayor a 0)'
    )
    
    decimals = forms.IntegerField(
        initial=2,
        validators=[MinValueValidator(0), MaxValueValidator(8)],
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '2',
            'min': '0',
            'max': '8',
            'required': True
        }),
        label='Decimales',
        help_text='Número de decimales para mostrar (0-8)'
    )
    
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Activa',
        help_text='Indica si la moneda está activa y disponible para uso'
    )
    
    def __init__(self, *args, **kwargs):
        """Inicializar formulario con datos del objeto existente si es edición"""
        self.instance_code = kwargs.pop('instance_code', None)
        super().__init__(*args, **kwargs)
        
        # Si estamos editando (instance_code existe), hacer currency_code opcional
        if self.instance_code:
            self.fields['currency_code'].required = False
            self.fields['currency_code'].widget.attrs['required'] = False
    
    def clean_currency_code(self):
        """Limpiar y validar código de moneda, verificando duplicados"""
        currency_code = self.cleaned_data.get('currency_code', '').strip().upper()
        
        # Si estamos editando y el código está vacío, usar el código actual de la instancia
        if self.instance_code and not currency_code:
            currency_code = self.instance_code.upper()
        
        if not currency_code:
            raise ValidationError("El código de moneda es obligatorio.")
        
        if len(currency_code) != 3:
            raise ValidationError("El código de moneda debe tener exactamente 3 caracteres.")
        
        # Validar que sean solo letras
        if not currency_code.isalpha():
            raise ValidationError("El código de moneda solo puede contener letras.")
        
        # Si estamos editando y el código cambió, verificar que no exista
        if self.instance_code and currency_code != self.instance_code:
            # Verificar si el código ya existe
            from ..services.api_client import ForgeAPIClient
            try:
                api_client = ForgeAPIClient()
                existing = api_client.get_currency(currency_code)
                if existing:
                    raise ValidationError(
                        f"El código '{currency_code}' ya está en uso por otra moneda."
                    )
            except Exception:
                # Si hay error al verificar, asumimos que no existe
                pass
        
        return currency_code
    
    def clean_name(self):
        """Limpiar y validar nombre"""
        name = self.cleaned_data.get('name', '').strip()
        
        if not name:
            raise ValidationError("El nombre es obligatorio.")
        
        if len(name) < 2:
            raise ValidationError("El nombre debe tener al menos 2 caracteres.")
        
        return name
    
    def clean_exchange_rate(self):
        """Validar tipo de cambio"""
        exchange_rate = self.cleaned_data.get('exchange_rate')
        
        if exchange_rate is None:
            raise ValidationError("El tipo de cambio es obligatorio.")
        
        if exchange_rate <= 0:
            raise ValidationError("El tipo de cambio debe ser mayor a 0.")
        
        return exchange_rate
    
    def clean_decimals(self):
        """Validar número de decimales"""
        decimals = self.cleaned_data.get('decimals')
        
        if decimals is None:
            decimals = 2
        
        if decimals < 0:
            raise ValidationError("El número de decimales no puede ser negativo.")
        
        if decimals > 8:
            raise ValidationError("El número de decimales no puede ser mayor a 8.")
        
        return decimals
    
    def clean(self):
        """Validación cruzada de campos"""
        cleaned_data = super().clean()
        
        currency_code = cleaned_data.get('currency_code')
        exchange_rate = cleaned_data.get('exchange_rate')
        
        # Si el tipo de cambio es 1.0, probablemente es la moneda base
        if exchange_rate == 1.0 and currency_code:
            # Esto es solo informativo, no un error
            pass
        
        return cleaned_data


class CurrencySearchForm(forms.Form):
    """
    Formulario para búsqueda y filtrado de monedas
    """
    
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por código, nombre o símbolo...',
            'autocomplete': 'off'
        }),
        label='Búsqueda'
    )
    
    is_active = forms.ChoiceField(
        choices=[
            ('', 'Todos los estados'),
            ('true', 'Solo activas'),
            ('false', 'Solo inactivas')
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Estado'
    )
    
    def clean_search(self):
        """Limpiar término de búsqueda"""
        search = self.cleaned_data.get('search', '').strip()
        return search

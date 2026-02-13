"""
Forms para el módulo de Quote (Cotizaciones)
Tarea 6.4: Gestión de cotizaciones
"""
from django import forms
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from datetime import datetime, date, timedelta
from decimal import Decimal


class QuoteForm(forms.Form):
    """Formulario para crear/editar cotizaciones."""
    
    # Campos básicos
    client_id = forms.IntegerField(
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        }),
        label='Cliente',
        help_text='Cliente para la cotización'
    )
    
    equipment_id = forms.IntegerField(
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Equipo',
        help_text='Equipo asociado (opcional)'
    )
    
    quote_date = forms.DateField(
        initial=date.today,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Fecha de Cotización'
    )
    
    valid_until = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Válida Hasta',
        help_text='Fecha de validez de la cotización (por defecto: 30 días)'
    )
    
    currency_code = forms.CharField(
        max_length=3,
        initial='MXN',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'MXN',
            'maxlength': '3',
            'style': 'text-transform: uppercase;'
        }),
        label='Moneda',
        help_text='Código ISO de la moneda'
    )
    
    # Descuentos e impuestos
    discount_percent = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        min_value=0,
        max_value=100,
        required=False,
        initial=0.00,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'min': '0',
            'max': '100',
            'step': '0.01'
        }),
        label='Descuento (%)',
        help_text='Porcentaje de descuento (0-100%)'
    )
    
    tax_percent = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        min_value=0,
        max_value=100,
        required=False,
        initial=16.00,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '16.00',
            'min': '0',
            'max': '100',
            'step': '0.01'
        }),
        label='Impuesto (%)',
        help_text='Porcentaje de IVA'
    )
    
    # Notas y términos
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Notas adicionales sobre la cotización...'
        }),
        label='Notas',
        help_text='Notas internas sobre la cotización'
    )
    
    terms_and_conditions = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Términos y condiciones de la cotización...'
        }),
        label='Términos y Condiciones',
        help_text='Términos y condiciones que aparecerán en la cotización'
    )
    
    def clean_valid_until(self):
        """Validar que valid_until sea posterior a quote_date."""
        valid_until = self.cleaned_data.get('valid_until')
        quote_date = self.cleaned_data.get('quote_date')
        
        if valid_until and quote_date:
            if valid_until < quote_date:
                raise ValidationError("La fecha de validez debe ser posterior a la fecha de cotización.")
        
        return valid_until


class QuoteItemForm(forms.Form):
    """Formulario para items de cotización."""
    
    flat_rate_id = forms.IntegerField(
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Estándar de Tiempo',
        help_text='Estándar de tiempo plano asociado (opcional)'
    )
    
    service_code = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'SERV-001',
            'maxlength': '20'
        }),
        label='Código de Servicio',
        help_text='Código del servicio'
    )
    
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Descripción del servicio...',
            'required': True
        }),
        label='Descripción',
        help_text='Descripción detallada del servicio'
    )
    
    quantity = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'step': '1'
        }),
        label='Cantidad',
        help_text='Cantidad de servicios'
    )
    
    hours = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        min_value=0,
        initial=0.00,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'min': '0',
            'step': '0.01'
        }),
        label='Horas',
        help_text='Horas de trabajo estimadas'
    )
    
    hourly_rate = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0,
        initial=500.00,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '500.00',
            'min': '0',
            'step': '0.01'
        }),
        label='Tarifa por Hora',
        help_text='Tarifa horaria del servicio'
    )
    
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Notas sobre este item...'
        }),
        label='Notas',
        help_text='Notas adicionales sobre este item'
    )

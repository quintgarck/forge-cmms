"""
Forms para el módulo de Invoice (Facturas) actualizados a la nueva estructura del modelo.
"""
from django import forms
from django.core.validators import RegexValidator, MinValueValidator
from django.core.exceptions import ValidationError
from datetime import datetime, date, timedelta
from decimal import Decimal


class InvoiceForm(forms.Form):
    """
    Formulario actualizado para Invoice con todos los campos sincronizados con el modelo.
    """
    # Validadores
    invoice_number_validator = RegexValidator(
        regex=r'^[A-Z0-9\-]+$',
        message="El número de factura solo puede contener letras mayúsculas, números y guiones."
    )

    # Campos básicos
    invoice_number = forms.CharField(
        max_length=50,
        validators=[invoice_number_validator],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'INV-2024-001',
            'maxlength': '50',
            'required': True,
            'style': 'text-transform: uppercase;'
        }),
        label='Número de Factura',
        help_text='Número único de la factura'
    )

    wo_id = forms.IntegerField(
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Orden de Trabajo',
        help_text='Orden de trabajo asociada (opcional)'
    )

    client_id = forms.IntegerField(
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        }),
        label='Cliente',
        help_text='Cliente al que se factura'
    )

    # Montos
    currency_code = forms.CharField(
        max_length=3,
        initial='MXN',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'MXN',
            'maxlength': '3',
            'style': 'text-transform: uppercase;'
        }),
        label='Código de Moneda',
        help_text='Código ISO de la moneda (MXN, USD, EUR)'
    )

    subtotal = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=0,
        initial=0.00,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'min': '0',
            'step': '0.01'
        }),
        label='Subtotal',
        help_text='Monto antes de impuestos y descuentos'
    )

    tax_amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=0,
        required=False,
        initial=0.00,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'min': '0',
            'step': '0.01'
        }),
        label='Impuestos',
        help_text='Monto total de impuestos'
    )

    discount_amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=0,
        required=False,
        initial=0.00,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'min': '0',
            'step': '0.01'
        }),
        label='Descuento',
        help_text='Monto total de descuentos aplicados'
    )

    total_amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=0,
        initial=0.00,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'min': '0',
            'step': '0.01'
        }),
        label='Total',
        help_text='Monto total de la factura'
    )

    # Fechas
    issue_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Fecha de Emisión',
        help_text='Fecha en que se emite la factura'
    )

    due_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Fecha de Vencimiento',
        help_text='Fecha límite de pago'
    )

    paid_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Fecha de Pago',
        help_text='Fecha en que se realizó el pago (dejar vacío si no pagado)'
    )

    # Estado
    status = forms.ChoiceField(
        choices=[
            ('DRAFT', 'Borrador'),
            ('PENDING', 'Pendiente'),
            ('PAID', 'Pagada'),
            ('OVERDUE', 'Vencida'),
            ('CANCELLED', 'Cancelada'),
            ('REFUNDED', 'Reembolsada'),
        ],
        initial='PENDING',
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Estado',
        help_text='Estado actual de la factura'
    )

    # Notas
    notes = forms.CharField(
        max_length=5000,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Notas o comentarios adicionales...',
            'rows': 4,
            'maxlength': '5000'
        }),
        label='Notas',
        help_text='Información adicional sobre la factura'
    )

    def clean_invoice_number(self):
        """Limpiar y validar número de factura."""
        invoice_number = self.cleaned_data.get('invoice_number', '').strip().upper()

        if not invoice_number:
            raise ValidationError("El número de factura es obligatorio.")

        if len(invoice_number) < 3:
            raise ValidationError("El número de factura debe tener al menos 3 caracteres.")

        return invoice_number

    def clean_currency_code(self):
        """Limpiar y validar código de moneda."""
        currency_code = self.cleaned_data.get('currency_code', '').strip().upper()

        if not currency_code:
            return 'MXN'  # Default

        if len(currency_code) != 3:
            raise ValidationError("El código de moneda debe tener exactamente 3 caracteres.")

        valid_currencies = ['MXN', 'USD', 'EUR', 'CAD', 'GBP', 'JPY', 'CNY']
        if currency_code not in valid_currencies:
            raise ValidationError(f"Código de moneda inválido. Use uno de: {', '.join(valid_currencies)}")

        return currency_code

    def clean_subtotal(self):
        """Limpiar y validar subtotal."""
        subtotal = self.cleaned_data.get('subtotal')

        if subtotal is None:
            raise ValidationError("El subtotal es obligatorio.")

        if subtotal < 0:
            raise ValidationError("El subtotal no puede ser negativo.")

        if subtotal > Decimal('9999999999.99'):
            raise ValidationError("El subtotal excede el límite máximo.")

        return subtotal

    def clean_tax_amount(self):
        """Limpiar y validar monto de impuestos."""
        tax_amount = self.cleaned_data.get('tax_amount')

        if tax_amount is None:
            return Decimal('0.00')

        if tax_amount < 0:
            raise ValidationError("El monto de impuestos no puede ser negativo.")

        return tax_amount

    def clean_discount_amount(self):
        """Limpiar y validar monto de descuento."""
        discount_amount = self.cleaned_data.get('discount_amount')

        if discount_amount is None:
            return Decimal('0.00')

        if discount_amount < 0:
            raise ValidationError("El monto de descuento no puede ser negativo.")

        return discount_amount

    def clean_total_amount(self):
        """Limpiar y validar monto total."""
        total_amount = self.cleaned_data.get('total_amount')

        if total_amount is None:
            raise ValidationError("El monto total es obligatorio.")

        if total_amount < 0:
            raise ValidationError("El monto total no puede ser negativo.")

        return total_amount

    def clean_issue_date(self):
        """Limpiar y validar fecha de emisión."""
        issue_date = self.cleaned_data.get('issue_date')

        if not issue_date:
            raise ValidationError("La fecha de emisión es obligatoria.")

        # Permitir fechas futuras para facturas programadas
        # pero advertir si es muy lejana
        if issue_date > date.today() + timedelta(days=365):
            raise ValidationError("La fecha de emisión no puede ser más de 1 año en el futuro.")

        return issue_date

    def clean_due_date(self):
        """Limpiar y validar fecha de vencimiento."""
        due_date = self.cleaned_data.get('due_date')

        if due_date:
            # La fecha de vencimiento debe validarse contra la fecha de emisión en clean()
            pass

        return due_date

    def clean_paid_date(self):
        """Limpiar y validar fecha de pago."""
        paid_date = self.cleaned_data.get('paid_date')
        status = self.cleaned_data.get('status')

        # Si hay fecha de pago, el estado debería ser PAID
        if paid_date and status != 'PAID':
            # Advertencia: permitimos pero sugerimos cambiar el estado
            pass

        return paid_date

    def clean(self):
        """Validación cruzada de campos."""
        cleaned_data = super().clean()

        subtotal = cleaned_data.get('subtotal', Decimal('0.00'))
        tax_amount = cleaned_data.get('tax_amount', Decimal('0.00'))
        discount_amount = cleaned_data.get('discount_amount', Decimal('0.00'))
        total_amount = cleaned_data.get('total_amount', Decimal('0.00'))
        issue_date = cleaned_data.get('issue_date')
        due_date = cleaned_data.get('due_date')
        paid_date = cleaned_data.get('paid_date')
        status = cleaned_data.get('status')

        # Validar cálculo de montos
        calculated_total = subtotal + tax_amount - discount_amount
        if abs(calculated_total - total_amount) > Decimal('0.01'):
            raise ValidationError(
                f"El monto total ({total_amount}) no coincide con el cálculo "
                f"(Subtotal {subtotal} + Impuestos {tax_amount} - Descuento {discount_amount} = {calculated_total})"
            )

        # Validar descuento no exceda subtotal
        if discount_amount > subtotal:
            raise ValidationError("El descuento no puede ser mayor que el subtotal.")

        # Validar fechas
        if issue_date and due_date:
            if due_date < issue_date:
                raise ValidationError("La fecha de vencimiento no puede ser anterior a la fecha de emisión.")

        if issue_date and paid_date:
            if paid_date < issue_date:
                raise ValidationError("La fecha de pago no puede ser anterior a la fecha de emisión.")

        # Validar estado vs fecha de pago
        if status == 'PAID' and not paid_date:
            raise ValidationError("Si el estado es 'Pagada', debe especificar la fecha de pago.")

        if paid_date and status not in ['PAID', 'REFUNDED']:
            raise ValidationError("Si hay fecha de pago, el estado debe ser 'Pagada' o 'Reembolsada'.")

        return cleaned_data


class InvoiceSearchForm(forms.Form):
    """
    Formulario para búsqueda y filtrado de facturas.
    """
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por número de factura, cliente...',
            'autocomplete': 'off'
        }),
        label='Buscar'
    )

    status = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Todos los estados'),
            ('DRAFT', 'Borrador'),
            ('PENDING', 'Pendiente'),
            ('PAID', 'Pagada'),
            ('OVERDUE', 'Vencida'),
            ('CANCELLED', 'Cancelada'),
            ('REFUNDED', 'Reembolsada'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Estado'
    )

    client_id = forms.IntegerField(
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Cliente'
    )

    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Desde'
    )

    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Hasta'
    )

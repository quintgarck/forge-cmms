"""
Client forms for ForgeDB frontend application.
"""
from django import forms
from django.core.validators import RegexValidator, EmailValidator
from django.core.exceptions import ValidationError
import re


class ClientForm(forms.Form):
    """
    Enhanced form for client creation and editing with comprehensive validation.
    """

    # Client code validator (alphanumeric, hyphens, underscores)
    client_code_validator = RegexValidator(
        regex=r'^[A-Z0-9\-_]+$',
        message="El código de cliente solo puede contener letras mayúsculas, números, guiones y guiones bajos."
    )

    # Phone number validator - More flexible for Mexican numbers
    phone_validator = RegexValidator(
        regex=r'^[\d\s\-\(\)\+\.]+$',
        message="Ingrese un número de teléfono válido. Puede incluir números, espacios, guiones y paréntesis."
    )

    # Name validator (letters, spaces, hyphens, apostrophes)
    name_validator = RegexValidator(
        regex=r"^[a-zA-ZÀ-ÿ\u00f1\u00d1\s\-'\.]+$",
        message="El nombre solo puede contener letras, espacios, guiones y apostrofes."
    )

    client_code = forms.CharField(
        max_length=20,
        validators=[client_code_validator],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'CLI-001',
            'maxlength': '20',
            'required': True,
            'style': 'text-transform: uppercase;'
        }),
        label='Código de Cliente',
        help_text='Código único para identificar al cliente (ej: CLI-001)'
    )

    type = forms.ChoiceField(
        choices=[
            ('INDIVIDUAL', 'Persona Física'),
            ('EMPRESA', 'Empresa'),
            ('GOVERNMENT', 'Gobierno'),
        ],
        initial='INDIVIDUAL',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        }),
        label='Tipo de Cliente',
        help_text='Seleccione el tipo de cliente'
    )

    name = forms.CharField(
        max_length=100,
        validators=[name_validator],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese el nombre completo del cliente',
            'maxlength': '100',
            'required': True,
            'autocomplete': 'name'
        }),
        label='Nombre Completo',
        help_text='Nombre completo del cliente (máximo 100 caracteres)'
    )

    email = forms.EmailField(
        max_length=254,
        validators=[EmailValidator(message="Ingrese un correo electrónico válido")],
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'ejemplo@correo.com',
            'maxlength': '254',
            'required': True,
            'autocomplete': 'email'
        }),
        label='Correo Electrónico',
        help_text='Dirección de correo electrónico válida'
    )

    phone = forms.CharField(
        max_length=20,
        validators=[phone_validator],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '82363829 o (55) 1234-5678',
            'maxlength': '20',
            'required': True,
            'autocomplete': 'tel'
        }),
        label='Teléfono',
        help_text='Número de teléfono de contacto (acepta formatos locales e internacionales)'
    )

    address = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese la dirección completa del cliente',
            'rows': 3,
            'maxlength': '500'
        }),
        label='Dirección',
        help_text='Dirección completa incluyendo calle, número, colonia, ciudad y código postal'
    )

    credit_limit = forms.DecimalField(
        max_digits=10,
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
        label='Límite de Crédito',
        help_text='Monto máximo de crédito autorizado para este cliente'
    )

    def clean_client_code(self):
        """Clean and validate client code field."""
        client_code = self.cleaned_data.get('client_code', '').strip().upper()

        if not client_code:
            raise ValidationError("El código de cliente es obligatorio.")

        if len(client_code) < 3:
            raise ValidationError("El código de cliente debe tener al menos 3 caracteres.")

        return client_code

    def clean_name(self):
        """Clean and validate name field."""
        name = self.cleaned_data.get('name', '').strip()

        if not name:
            raise ValidationError("El nombre es obligatorio.")

        if len(name) < 2:
            raise ValidationError("El nombre debe tener al menos 2 caracteres.")

        # Check for consecutive spaces
        if '  ' in name:
            raise ValidationError("El nombre no puede tener espacios consecutivos.")

        # Capitalize each word properly
        name = ' '.join(word.capitalize() for word in name.split())

        return name

    def clean_email(self):
        """Clean and validate email field."""
        email = self.cleaned_data.get('email', '').strip().lower()

        if not email:
            raise ValidationError("El correo electrónico es obligatorio.")

        # Additional email validation
        if email.count('@') != 1:
            raise ValidationError("El correo electrónico debe contener exactamente un símbolo @.")

        local_part, domain = email.split('@')

        if not local_part or not domain:
            raise ValidationError("El correo electrónico no tiene un formato válido.")

        if len(local_part) > 64:
            raise ValidationError("La parte local del correo es demasiado larga.")

        return email

    def clean_phone(self):
        """Clean and validate phone field."""
        phone = self.cleaned_data.get('phone', '').strip()

        if not phone:
            raise ValidationError("El teléfono es obligatorio.")

        # Remove all non-digit characters for validation
        digits_only = re.sub(r'\D', '', phone)

        if len(digits_only) < 8:
            raise ValidationError("El número de teléfono debe tener al menos 8 dígitos.")

        if len(digits_only) > 15:
            raise ValidationError("El número de teléfono no puede tener más de 15 dígitos.")

        # Return the original formatted phone for display
        return phone

    def clean_address(self):
        """Clean and validate address field."""
        address = self.cleaned_data.get('address', '').strip()

        if address:
            # Remove excessive whitespace
            address = re.sub(r'\s+', ' ', address)

            if len(address) < 10:
                raise ValidationError("La dirección debe tener al menos 10 caracteres si se proporciona.")

        return address

    def clean_credit_limit(self):
        """Clean and validate credit limit field."""
        credit_limit = self.cleaned_data.get('credit_limit')

        if credit_limit is None:
            return 0.00

        if credit_limit < 0:
            raise ValidationError("El límite de crédito no puede ser negativo.")

        if credit_limit > 999999.99:
            raise ValidationError("El límite de crédito no puede exceder $999,999.99.")

        return credit_limit

    def clean(self):
        """Perform cross-field validation."""
        cleaned_data = super().clean()

        name = cleaned_data.get('name')
        email = cleaned_data.get('email')
        phone = cleaned_data.get('phone')

        # For now, we'll make email and phone both required individually
        # The cross-field validation can be adjusted based on business requirements

        return cleaned_data


class ClientSearchForm(forms.Form):
    """Form for client search and filtering."""

    SORT_CHOICES = [
        ('name', 'Nombre'),
        ('email', 'Email'),
        ('created_at', 'Fecha de creación'),
        ('credit_limit', 'Límite de crédito'),
        ('credit_used', 'Crédito utilizado'),
    ]

    ORDER_CHOICES = [
        ('asc', 'Ascendente'),
        ('desc', 'Descendente'),
    ]

    STATUS_CHOICES = [
        ('', 'Todos los estados'),
        ('active', 'Activos'),
        ('credit_exceeded', 'Límite excedido'),
        ('with_balance', 'Con saldo pendiente'),
    ]

    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control search-input',
            'placeholder': 'Buscar por nombre, email o teléfono...',
            'autocomplete': 'off'
        }),
        label='Buscar'
    )

    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Estado'
    )

    sort = forms.ChoiceField(
        choices=SORT_CHOICES,
        required=False,
        initial='name',
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Ordenar por'
    )

    order = forms.ChoiceField(
        choices=ORDER_CHOICES,
        required=False,
        initial='asc',
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Orden'
    )

    def clean_search(self):
        """Clean search query."""
        search = self.cleaned_data.get('search', '').strip()

        if search and len(search) < 2:
            raise ValidationError("La búsqueda debe tener al menos 2 caracteres.")

        return search
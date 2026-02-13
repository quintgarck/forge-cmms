"""
Forms para el módulo de Equipment (Equipos) actualizados a la nueva estructura del modelo.
"""
from django import forms
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from datetime import datetime


class EquipmentForm(forms.Form):
    """
    Formulario actualizado para Equipment con todos los campos sincronizados con el modelo.
    """
    # Validadores
    equipment_code_validator = RegexValidator(
        regex=r'^[A-Z0-9\-_]+$',
        message="El código de equipo solo puede contener letras mayúsculas, números, guiones y guiones bajos."
    )

    vin_validator = RegexValidator(
        regex=r'^[A-HJ-NPR-Z0-9]{17}$',
        message="El VIN debe tener exactamente 17 caracteres alfanuméricos (sin I, O, Q)."
    )

    license_plate_validator = RegexValidator(
        regex=r'^[A-Z0-9\-\s]+$',
        message="La placa solo puede contener letras mayúsculas, números, guiones y espacios."
    )

    # Campos básicos
    equipment_code = forms.CharField(
        max_length=40,
        validators=[equipment_code_validator],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'EQ-001',
            'maxlength': '40',
            'required': True,
            'style': 'text-transform: uppercase;'
        }),
        label='Código de Equipo',
        help_text='Código único para identificar el equipo'
    )

    type_id = forms.IntegerField(
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        }),
        label='Tipo de Equipo',
        help_text='Categoría del equipo (ej: Automotriz, Industrial)'
    )

    client_id = forms.IntegerField(
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        }),
        label='Cliente Propietario',
        help_text='Cliente al que pertenece este equipo'
    )

    # Información del vehículo
    brand = forms.CharField(
        max_length=50,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True,
            'id': 'id_brand',
        }),
        label='Marca',
        help_text='Marca del vehículo (ej: Toyota, Ford, Chevrolet)'
    )

    model = forms.CharField(
        max_length=50,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True,
            'id': 'id_model',
        }),
        label='Modelo',
        help_text='Modelo del vehículo'
    )

    year = forms.IntegerField(
        min_value=1900,
        max_value=2030,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '2020',
            'min': '1900',
            'max': '2030'
        }),
        label='Año',
        help_text='Año de fabricación del vehículo'
    )

    serial_number = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'SN123456',
            'maxlength': '100'
        }),
        label='Número de Serie',
        help_text='Número de serie del equipo'
    )

    vin = forms.CharField(
        max_length=17,
        required=False,
        validators=[vin_validator],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '1HGBH41JXMN109186',
            'maxlength': '17',
            'style': 'text-transform: uppercase;'
        }),
        label='VIN',
        help_text='Número de identificación vehicular de 17 caracteres'
    )

    license_plate = forms.CharField(
        max_length=20,
        required=False,
        validators=[license_plate_validator],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'ABC-123',
            'maxlength': '20',
            'style': 'text-transform: uppercase;'
        }),
        label='Placa',
        help_text='Número de placa del vehículo'
    )

    color = forms.CharField(
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': False
        }),
        label='Color',
        help_text='Color del vehículo'
    )

    # Detalles del vehículo
    submodel_trim = forms.CharField(
        max_length=40,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'LE, XLE, Limited',
            'maxlength': '40'
        }),
        label='Submodelo/Versión',
        help_text='Versión o nivel de equipamiento'
    )

    body_style = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Sedan, SUV, Pickup',
            'maxlength': '20'
        }),
        label='Estilo de Carrocería',
        help_text='Tipo de carrocería del vehículo'
    )

    doors = forms.IntegerField(
        min_value=2,
        max_value=6,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '4',
            'min': '2',
            'max': '6'
        }),
        label='Número de Puertas',
        help_text='Cantidad de puertas del vehículo'
    )

    engine_desc = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '2.0L 4-Cyl Turbo',
            'maxlength': '100'
        }),
        label='Descripción del Motor',
        help_text='Especificaciones del motor'
    )

    fuel_code = forms.ChoiceField(
        choices=[('', 'Seleccionar tipo de combustible')],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Código de Combustible',
        help_text='Tipo de combustible que utiliza el vehículo'
    )

    aspiration_code = forms.ChoiceField(
        choices=[('', 'Seleccionar tipo de aspiración')],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Código de Aspiración',
        help_text='Tipo de aspiración del motor'
    )

    transmission_code = forms.ChoiceField(
        choices=[('', 'Seleccionar tipo de transmisión')],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Código de Transmisión',
        help_text='Tipo de transmisión del vehículo'
    )

    drivetrain_code = forms.ChoiceField(
        choices=[('', 'Seleccionar tipo de tracción')],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Código de Tracción',
        help_text='Tipo de tracción del vehículo'
    )

    # Fechas importantes
    purchase_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Fecha de Compra',
        help_text='Fecha en que se adquirió el vehículo'
    )

    warranty_until = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Garantía Hasta',
        help_text='Fecha de vencimiento de la garantía'
    )

    last_service_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Último Servicio',
        help_text='Fecha del último servicio realizado'
    )

    next_service_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Próximo Servicio',
        help_text='Fecha programada para el próximo servicio'
    )

    # Kilometraje y horas
    current_mileage_hours = forms.IntegerField(
        min_value=0,
        required=False,
        initial=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '50000',
            'min': '0'
        }),
        label='Kilometraje/Horas Actual',
        help_text='Kilometraje actual del vehículo o horas de uso'
    )

    last_mileage_update = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Última Actualización de Kilometraje',
        help_text='Fecha de la última actualización del kilometraje'
    )

    # Estado
    status = forms.ChoiceField(
        choices=[
            ('ACTIVO', 'Activo'),
            ('INACTIVO', 'Inactivo'),
            ('sold', 'Vendido'),
            ('scrapped', 'Desechado'),
        ],
        initial='ACTIVO',
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Estado',
        help_text='Estado actual del equipo'
    )

    # Notas
    notes = forms.CharField(
        max_length=5000,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Notas adicionales sobre el equipo...',
            'rows': 4,
            'maxlength': '5000'
        }),
        label='Notas',
        help_text='Información adicional sobre el equipo'
    )

    def clean_equipment_code(self):
        """Limpiar y validar código de equipo."""
        equipment_code = self.cleaned_data.get('equipment_code', '').strip().upper()

        if not equipment_code:
            raise ValidationError("El código de equipo es obligatorio.")

        if len(equipment_code) < 3:
            raise ValidationError("El código de equipo debe tener al menos 3 caracteres.")

        return equipment_code

    def clean_vin(self):
        """Limpiar y validar VIN."""
        vin = self.cleaned_data.get('vin', '').strip().upper()

        if vin:
            vin = vin.replace(' ', '').replace('-', '')
            
            if len(vin) != 17:
                raise ValidationError("El VIN debe tener exactamente 17 caracteres.")
            
            invalid_chars = set(vin) & {'I', 'O', 'Q'}
            if invalid_chars:
                raise ValidationError(f"El VIN no puede contener los caracteres: {', '.join(invalid_chars)}")

        return vin

    def clean_brand(self):
        """Limpiar y validar marca."""
        brand = self.cleaned_data.get('brand', '').strip()

        if not brand:
            raise ValidationError("La marca es obligatoria.")

        if len(brand) < 2:
            raise ValidationError("La marca debe tener al menos 2 caracteres.")

        return brand.title()

    def clean_model(self):
        """Limpiar y validar modelo."""
        model = self.cleaned_data.get('model', '').strip()

        if not model:
            raise ValidationError("El modelo es obligatorio.")

        if len(model) < 1:
            raise ValidationError("El modelo debe tener al menos 1 caracter.")

        return model

    def clean_year(self):
        """Limpiar y validar año."""
        year = self.cleaned_data.get('year')

        if year:
            current_year = datetime.now().year

            if year > current_year + 1:
                raise ValidationError(f"El año no puede ser mayor que {current_year + 1}.")

            if year < 1900:
                raise ValidationError("El año no puede ser menor que 1900.")

        return year

    def clean_current_mileage_hours(self):
        """Limpiar y validar kilometraje."""
        mileage = self.cleaned_data.get('current_mileage_hours')

        if mileage is not None:
            if mileage < 0:
                raise ValidationError("El kilometraje no puede ser negativo.")

            if mileage > 9999999:
                raise ValidationError("El kilometraje no puede exceder 9,999,999.")

        return mileage or 0

    def clean(self):
        """Validación cruzada de campos."""
        cleaned_data = super().clean()

        purchase_date = cleaned_data.get('purchase_date')
        warranty_until = cleaned_data.get('warranty_until')
        year = cleaned_data.get('year')
        last_service_date = cleaned_data.get('last_service_date')
        next_service_date = cleaned_data.get('next_service_date')

        # Validar fecha de compra vs año
        if purchase_date and year:
            if purchase_date.year < year:
                raise ValidationError("La fecha de compra no puede ser anterior al año de fabricación.")

        # Validar garantía vs fecha de compra
        if purchase_date and warranty_until:
            if warranty_until < purchase_date:
                raise ValidationError("La fecha de garantía no puede ser anterior a la fecha de compra.")

        # Validar fechas de servicio
        if last_service_date and next_service_date:
            if next_service_date < last_service_date:
                raise ValidationError("La fecha del próximo servicio no puede ser anterior al último servicio.")

        return cleaned_data

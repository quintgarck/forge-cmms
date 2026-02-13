"""
Django forms for ForgeDB frontend application.
"""
import logging
from django import forms
from django.core.validators import RegexValidator, EmailValidator
from django.core.exceptions import ValidationError
from django.db import connection
import re

logger = logging.getLogger(__name__)


class EquipmentForm(forms.Form):
    """
    Form for equipment creation and editing with comprehensive validation.
    """

    # Equipment code validator (alphanumeric, hyphens, underscores)
    equipment_code_validator = RegexValidator(
        regex=r'^[A-Z0-9\-_]+$',
        message="El código de equipo solo puede contener letras mayúsculas, números, guiones y guiones bajos."
    )

    # VIN validator (17 characters, alphanumeric)
    vin_validator = RegexValidator(
        regex=r'^[A-HJ-NPR-Z0-9]{17}$',
        message="El VIN debe tener exactamente 17 caracteres alfanuméricos (sin I, O, Q)."
    )

    # License plate validator (flexible format)
    license_plate_validator = RegexValidator(
        regex=r'^[A-Z0-9\-\s]+$',
        message="La placa solo puede contener letras mayúsculas, números, guiones y espacios."
    )

    equipment_code = forms.CharField(
        max_length=30,
        validators=[equipment_code_validator],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'EQ-001',
            'maxlength': '30',
            'required': True,
            'style': 'text-transform: uppercase;'
        }),
        label='Código de Equipo',
        help_text='Código único para identificar el equipo (ej: EQ-001)'
    )

    client_id = forms.IntegerField(
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        }),
        label='Cliente Propietario',
        help_text='Cliente al que pertenece este equipo'
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
        label='VIN (Número de Identificación Vehicular)',
        help_text='Número de identificación vehicular de 17 caracteres (opcional)'
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
        help_text='Número de placa del vehículo (opcional)'
    )

    year = forms.IntegerField(
        min_value=1900,
        max_value=2030,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '2020',
            'min': '1900',
            'max': '2030'
        }),
        label='Año',
        help_text='Año de fabricación del vehículo'
    )

    make = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Toyota',
            'maxlength': '50',
            'required': True
        }),
        label='Marca',
        help_text='Marca del vehículo (ej: Toyota, Ford, Chevrolet)'
    )

    model = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Corolla',
            'maxlength': '50',
            'required': True
        }),
        label='Modelo',
        help_text='Modelo del vehículo (ej: Corolla, F-150, Silverado)'
    )

    engine = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '2.0L 4-Cyl',
            'maxlength': '50'
        }),
        label='Motor',
        help_text='Especificaciones del motor (opcional)'
    )

    transmission = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Automática CVT',
            'maxlength': '50'
        }),
        label='Transmisión',
        help_text='Tipo de transmisión (opcional)'
    )

    color = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Blanco',
            'maxlength': '30'
        }),
        label='Color',
        help_text='Color del vehículo (opcional)'
    )

    mileage = forms.IntegerField(
        min_value=0,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '50000',
            'min': '0'
        }),
        label='Kilometraje',
        help_text='Kilometraje actual del vehículo (opcional)'
    )

    fuel_type = forms.ChoiceField(
        choices=[
            ('', 'Seleccionar tipo de combustible'),
            ('gasoline', 'Gasolina'),
            ('diesel', 'Diésel'),
            ('hybrid', 'Híbrido'),
            ('electric', 'Eléctrico'),
            ('lpg', 'Gas LP'),
            ('cng', 'Gas Natural'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Tipo de Combustible',
        help_text='Tipo de combustible que utiliza el vehículo'
    )

    status = forms.ChoiceField(
        choices=[
            ('active', 'Activo'),
            ('inactive', 'Inactivo'),
            ('sold', 'Vendido'),
            ('scrapped', 'Desechado'),
        ],
        initial='active',
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Estado',
        help_text='Estado actual del equipo'
    )

    purchase_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Fecha de Compra',
        help_text='Fecha en que se adquirió el vehículo (opcional)'
    )

    warranty_expiry = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Vencimiento de Garantía',
        help_text='Fecha de vencimiento de la garantía (opcional)'
    )

    notes = forms.CharField(
        max_length=1000,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Notas adicionales sobre el equipo...',
            'rows': 4,
            'maxlength': '1000'
        }),
        label='Notas',
        help_text='Información adicional sobre el equipo (opcional)'
    )

    def clean_equipment_code(self):
        """Clean and validate equipment code field."""
        equipment_code = self.cleaned_data.get('equipment_code', '').strip().upper()

        if not equipment_code:
            raise ValidationError("El código de equipo es obligatorio.")

        if len(equipment_code) < 3:
            raise ValidationError("El código de equipo debe tener al menos 3 caracteres.")

        return equipment_code

    def clean_vin(self):
        """Clean and validate VIN field."""
        vin = self.cleaned_data.get('vin', '').strip().upper()

        if vin:
            # Remove spaces and hyphens
            vin = vin.replace(' ', '').replace('-', '')
            
            if len(vin) != 17:
                raise ValidationError("El VIN debe tener exactamente 17 caracteres.")
            
            # Check for invalid characters
            invalid_chars = set(vin) & {'I', 'O', 'Q'}
            if invalid_chars:
                raise ValidationError(f"El VIN no puede contener los caracteres: {', '.join(invalid_chars)}")

        return vin

    def clean_license_plate(self):
        """Clean and validate license plate field."""
        license_plate = self.cleaned_data.get('license_plate', '').strip().upper()

        if license_plate:
            if len(license_plate) < 3:
                raise ValidationError("La placa debe tener al menos 3 caracteres.")

        return license_plate

    def clean_make(self):
        """Clean and validate make field."""
        make = self.cleaned_data.get('make', '').strip()

        if not make:
            raise ValidationError("La marca es obligatoria.")

        if len(make) < 2:
            raise ValidationError("La marca debe tener al menos 2 caracteres.")

        # Capitalize first letter of each word
        make = ' '.join(word.capitalize() for word in make.split())

        return make

    def clean_model(self):
        """Clean and validate model field."""
        model = self.cleaned_data.get('model', '').strip()

        if not model:
            raise ValidationError("El modelo es obligatorio.")

        if len(model) < 1:
            raise ValidationError("El modelo debe tener al menos 1 caracter.")

        return model

    def clean_year(self):
        """Clean and validate year field."""
        year = self.cleaned_data.get('year')

        if not year:
            raise ValidationError("El año es obligatorio.")

        from datetime import datetime
        current_year = datetime.now().year

        if year > current_year + 1:
            raise ValidationError(f"El año no puede ser mayor que {current_year + 1}.")

        return year

    def clean_mileage(self):
        """Clean and validate mileage field."""
        mileage = self.cleaned_data.get('mileage')

        if mileage is not None:
            if mileage < 0:
                raise ValidationError("El kilometraje no puede ser negativo.")

            if mileage > 9999999:
                raise ValidationError("El kilometraje no puede exceder 9,999,999 km.")

        return mileage

    def clean(self):
        """Perform cross-field validation."""
        cleaned_data = super().clean()

        purchase_date = cleaned_data.get('purchase_date')
        warranty_expiry = cleaned_data.get('warranty_expiry')
        year = cleaned_data.get('year')

        # Validate purchase date vs year
        if purchase_date and year:
            if purchase_date.year < year:
                raise ValidationError("La fecha de compra no puede ser anterior al año de fabricación.")

        # Validate warranty expiry vs purchase date
        if purchase_date and warranty_expiry:
            if warranty_expiry < purchase_date:
                raise ValidationError("La fecha de vencimiento de garantía no puede ser anterior a la fecha de compra.")

        return cleaned_data


class EquipmentSearchForm(forms.Form):
    """Form for equipment search and filtering."""

    STATUS_CHOICES = [
        ('', 'Todos los Estados'),
        ('active', 'Activos'),
        ('inactive', 'Inactivos'),
        ('sold', 'Vendidos'),
        ('scrapped', 'Desechados'),
    ]

    FUEL_TYPE_CHOICES = [
        ('', 'Todos los Combustibles'),
        ('gasoline', 'Gasolina'),
        ('diesel', 'Diésel'),
        ('hybrid', 'Híbrido'),
        ('electric', 'Eléctrico'),
        ('lpg', 'Gas LP'),
        ('cng', 'Gas Natural'),
    ]

    SORT_CHOICES = [
        ('equipment_code', 'Código'),
        ('make', 'Marca'),
        ('model', 'Modelo'),
        ('year', 'Año'),
        ('client__name', 'Cliente'),
        ('created_at', 'Fecha de Registro'),
        ('mileage', 'Kilometraje'),
    ]

    ORDER_CHOICES = [
        ('asc', 'Ascendente'),
        ('desc', 'Descendente'),
    ]

    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control search-input',
            'placeholder': 'Buscar por código, marca, modelo, VIN o placa...',
            'autocomplete': 'off'
        }),
        label='Buscar'
    )

    client = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Cliente'
    )

    make = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Filtrar por marca...'
        }),
        label='Marca'
    )

    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Estado'
    )

    fuel_type = forms.ChoiceField(
        choices=FUEL_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Tipo de Combustible'
    )

    year_from = forms.IntegerField(
        min_value=1900,
        max_value=2030,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '2000',
            'min': '1900',
            'max': '2030'
        }),
        label='Año Desde'
    )

    year_to = forms.IntegerField(
        min_value=1900,
        max_value=2030,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '2024',
            'min': '1900',
            'max': '2030'
        }),
        label='Año Hasta'
    )

    sort = forms.ChoiceField(
        choices=SORT_CHOICES,
        required=False,
        initial='equipment_code',
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

    def clean(self):
        """Cross-field validation."""
        cleaned_data = super().clean()
        year_from = cleaned_data.get('year_from')
        year_to = cleaned_data.get('year_to')

        if year_from and year_to and year_from > year_to:
            raise ValidationError("El año 'Desde' no puede ser mayor que el año 'Hasta'.")

        return cleaned_data


class MaintenanceScheduleForm(forms.Form):
    """
    Form for scheduling maintenance tasks with comprehensive validation.
    """

    MAINTENANCE_TYPES = [
        ('preventive', 'Mantenimiento Preventivo'),
        ('corrective', 'Mantenimiento Correctivo'),
        ('inspection', 'Inspección'),
        ('service', 'Servicio General'),
        ('repair', 'Reparación'),
        ('calibration', 'Calibración'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Baja'),
        ('normal', 'Normal'),
        ('high', 'Alta'),
        ('urgent', 'Urgente'),
    ]

    RECURRENCE_CHOICES = [
        ('', 'Sin recurrencia'),
        ('weekly', 'Semanal'),
        ('monthly', 'Mensual'),
        ('quarterly', 'Trimestral'),
        ('biannual', 'Semestral'),
        ('annual', 'Anual'),
        ('custom', 'Personalizado'),
    ]

    equipment_id = forms.IntegerField(
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        }),
        label='Equipo',
        help_text='Seleccione el equipo para el mantenimiento'
    )

    maintenance_type = forms.ChoiceField(
        choices=MAINTENANCE_TYPES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        }),
        label='Tipo de Mantenimiento',
        help_text='Tipo de mantenimiento a realizar'
    )

    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Título del mantenimiento',
            'maxlength': '200',
            'required': True
        }),
        label='Título',
        help_text='Título descriptivo del mantenimiento'
    )

    description = forms.CharField(
        max_length=1000,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Descripción detallada del mantenimiento...',
            'rows': 4,
            'maxlength': '1000',
            'required': True
        }),
        label='Descripción',
        help_text='Descripción detallada del trabajo a realizar'
    )

    scheduled_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'required': True
        }),
        label='Fecha Programada',
        help_text='Fecha en que se realizará el mantenimiento'
    )

    scheduled_time = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={
            'class': 'form-control',
            'type': 'time'
        }),
        label='Hora Programada',
        help_text='Hora específica para el mantenimiento (opcional)'
    )

    estimated_duration = forms.DecimalField(
        max_digits=6,
        decimal_places=2,
        min_value=0.25,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0.25',
            'step': '0.25',
            'placeholder': '2.00'
        }),
        label='Duración Estimada (horas)',
        help_text='Tiempo estimado en horas para completar el mantenimiento'
    )

    assigned_technician_id = forms.IntegerField(
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Técnico Asignado',
        help_text='Técnico responsable del mantenimiento (opcional)'
    )

    priority = forms.ChoiceField(
        choices=PRIORITY_CHOICES,
        initial='normal',
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Prioridad',
        help_text='Prioridad del mantenimiento'
    )

    recurrence = forms.ChoiceField(
        choices=RECURRENCE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Recurrencia',
        help_text='Frecuencia de repetición del mantenimiento'
    )

    recurrence_interval = forms.IntegerField(
        min_value=1,
        max_value=365,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'max': '365',
            'placeholder': '30'
        }),
        label='Intervalo (días)',
        help_text='Intervalo en días para recurrencia personalizada'
    )

    notes = forms.CharField(
        max_length=1000,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Notas adicionales sobre el mantenimiento...',
            'rows': 3,
            'maxlength': '1000'
        }),
        label='Notas',
        help_text='Información adicional sobre el mantenimiento (opcional)'
    )

    def clean_title(self):
        """Clean and validate title field."""
        title = self.cleaned_data.get('title', '').strip()

        if not title:
            raise ValidationError("El título es obligatorio.")

        if len(title) < 5:
            raise ValidationError("El título debe tener al menos 5 caracteres.")

        return title

    def clean_description(self):
        """Clean and validate description field."""
        description = self.cleaned_data.get('description', '').strip()

        if not description:
            raise ValidationError("La descripción es obligatoria.")

        if len(description) < 10:
            raise ValidationError("La descripción debe tener al menos 10 caracteres.")

        return description

    def clean_scheduled_date(self):
        """Clean and validate scheduled date field."""
        scheduled_date = self.cleaned_data.get('scheduled_date')

        if not scheduled_date:
            raise ValidationError("La fecha programada es obligatoria.")

        from datetime import date
        if scheduled_date < date.today():
            raise ValidationError("La fecha programada no puede ser anterior a hoy.")

        return scheduled_date

    def clean_estimated_duration(self):
        """Clean and validate estimated duration field."""
        duration = self.cleaned_data.get('estimated_duration')

        if not duration:
            raise ValidationError("La duración estimada es obligatoria.")

        if duration < 0.25:
            raise ValidationError("La duración mínima es 0.25 horas (15 minutos).")

        if duration > 24:
            raise ValidationError("La duración máxima es 24 horas.")

        return duration

    def clean(self):
        """Perform cross-field validation."""
        cleaned_data = super().clean()

        recurrence = cleaned_data.get('recurrence')
        recurrence_interval = cleaned_data.get('recurrence_interval')

        # If custom recurrence is selected, interval is required
        if recurrence == 'custom' and not recurrence_interval:
            raise ValidationError("Debe especificar el intervalo para recurrencia personalizada.")

        # If recurrence is not custom, clear interval
        if recurrence != 'custom':
            cleaned_data['recurrence_interval'] = None

        return cleaned_data


class MaintenanceSearchForm(forms.Form):
    """Form for maintenance search and filtering."""

    STATUS_CHOICES = [
        ('', 'Todos los Estados'),
        ('scheduled', 'Programado'),
        ('in_progress', 'En Progreso'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado'),
        ('overdue', 'Vencido'),
    ]

    TYPE_CHOICES = [
        ('', 'Todos los Tipos'),
        ('preventive', 'Preventivo'),
        ('corrective', 'Correctivo'),
        ('inspection', 'Inspección'),
        ('service', 'Servicio General'),
        ('repair', 'Reparación'),
        ('calibration', 'Calibración'),
    ]

    PRIORITY_CHOICES = [
        ('', 'Todas las Prioridades'),
        ('low', 'Baja'),
        ('normal', 'Normal'),
        ('high', 'Alta'),
        ('urgent', 'Urgente'),
    ]

    SORT_CHOICES = [
        ('scheduled_date', 'Fecha Programada'),
        ('priority', 'Prioridad'),
        ('maintenance_type', 'Tipo'),
        ('equipment__make', 'Marca del Equipo'),
        ('created_at', 'Fecha de Creación'),
    ]

    ORDER_CHOICES = [
        ('asc', 'Ascendente'),
        ('desc', 'Descendente'),
    ]

    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control search-input',
            'placeholder': 'Buscar por título, equipo o descripción...',
            'autocomplete': 'off'
        }),
        label='Buscar'
    )

    equipment = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Equipo'
    )

    maintenance_type = forms.ChoiceField(
        choices=TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Tipo'
    )

    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Estado'
    )

    priority = forms.ChoiceField(
        choices=PRIORITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Prioridad'
    )

    technician = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Técnico'
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

    sort = forms.ChoiceField(
        choices=SORT_CHOICES,
        required=False,
        initial='scheduled_date',
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

    def clean(self):
        """Cross-field validation."""
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')

        if date_from and date_to and date_from > date_to:
            raise ValidationError("La fecha 'Desde' no puede ser posterior a la fecha 'Hasta'.")

        return cleaned_data


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
            ('individual', 'Persona Física'),
            ('business', 'Empresa'),
            ('fleet', 'Flota'),
        ],
        initial='individual',
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


class WorkOrderWizardForm(forms.Form):
    """Multi-step work order creation form."""
    
    # Step 1: Client and Equipment Selection
    client_id = forms.IntegerField(
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        }),
        label='Cliente'
    )
    
    equipment_id = forms.IntegerField(
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        }),
        label='Equipo'
    )
    
    # Step 2: Service Selection (handled dynamically in template)
    
    # Step 3: Scheduling and Details
    description = forms.CharField(
        max_length=1000,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Describa el trabajo a realizar...',
            'required': True
        }),
        label='Descripción del Trabajo'
    )
    
    complaint = forms.CharField(
        max_length=1000,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Describa el problema reportado por el cliente...'
        }),
        label='Queja/Problema del Cliente'
    )
    
    priority = forms.ChoiceField(
        choices=[
            ('low', 'Baja'),
            ('normal', 'Normal'),
            ('high', 'Alta'),
            ('urgent', 'Urgente'),
        ],
        initial='normal',
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Prioridad'
    )
    
    status = forms.ChoiceField(
        choices=[
            ('draft', 'Borrador'),
            ('scheduled', 'Programada'),
        ],
        initial='draft',
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Estado Inicial'
    )
    
    technician_id = forms.IntegerField(
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Técnico Asignado'
    )
    
    scheduled_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Fecha Programada'
    )
    
    scheduled_time = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={
            'class': 'form-control',
            'type': 'time'
        }),
        label='Hora Programada'
    )
    
    estimated_hours = forms.DecimalField(
        max_digits=6,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0',
            'step': '0.25',
            'placeholder': '0.00'
        }),
        label='Horas Estimadas'
    )
    
    def clean_description(self):
        """Clean and validate description."""
        description = self.cleaned_data.get('description', '').strip()
        
        if not description:
            raise ValidationError("La descripción del trabajo es obligatoria.")
        
        if len(description) < 10:
            raise ValidationError("La descripción debe tener al menos 10 caracteres.")
        
        return description
    
    def clean_estimated_hours(self):
        """Clean and validate estimated hours."""
        hours = self.cleaned_data.get('estimated_hours')
        
        if hours is not None and hours < 0:
            raise ValidationError("Las horas estimadas no pueden ser negativas.")
        
        if hours is not None and hours > 100:
            raise ValidationError("Las horas estimadas no pueden exceder 100 horas.")
        
        return hours
    
    def clean(self):
        """Cross-field validation."""
        cleaned_data = super().clean()
        
        scheduled_date = cleaned_data.get('scheduled_date')
        status = cleaned_data.get('status')
        
        # If status is scheduled, date should be provided
        if status == 'scheduled' and not scheduled_date:
            raise ValidationError("Debe proporcionar una fecha programada si el estado es 'Programada'.")
        
        return cleaned_data


class WorkOrderForm(forms.Form):
    """Simple work order form for basic creation/editing."""
    
    wo_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'readonly': True
        }),
        label='Número de Orden'
    )
    
    client_id = forms.IntegerField(
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        }),
        label='Cliente'
    )
    
    equipment_id = forms.IntegerField(
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        }),
        label='Equipo'
    )
    
    description = forms.CharField(
        max_length=1000,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'required': True
        }),
        label='Descripción'
    )
    
    complaint = forms.CharField(
        max_length=1000,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3
        }),
        label='Queja del Cliente'
    )
    
    diagnosis = forms.CharField(
        max_length=1000,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3
        }),
        label='Diagnóstico'
    )
    
    resolution = forms.CharField(
        max_length=1000,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3
        }),
        label='Resolución'
    )
    
    status = forms.ChoiceField(
        choices=[
            ('draft', 'Borrador'),
            ('scheduled', 'Programada'),
            ('in_progress', 'En Progreso'),
            ('waiting_parts', 'Esperando Partes'),
            ('waiting_approval', 'Esperando Aprobación'),
            ('completed', 'Completada'),
            ('invoiced', 'Facturada'),
            ('cancelled', 'Cancelada'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Estado'
    )
    
    priority = forms.ChoiceField(
        choices=[
            ('low', 'Baja'),
            ('normal', 'Normal'),
            ('high', 'Alta'),
            ('urgent', 'Urgente'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Prioridad'
    )
    
    assigned_technician_id = forms.IntegerField(
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Técnico Asignado'
    )
    
    estimated_hours = forms.DecimalField(
        max_digits=6,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0',
            'step': '0.25'
        }),
        label='Horas Estimadas'
    )
    
    actual_hours = forms.DecimalField(
        max_digits=6,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0',
            'step': '0.25'
        }),
        label='Horas Reales'
    )
    
    estimated_cost = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0',
            'step': '0.01'
        }),
        label='Costo Estimado'
    )
    
    actual_cost = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0',
            'step': '0.01'
        }),
        label='Costo Real'
    )
    
    scheduled_date = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        }),
        label='Fecha Programada'
    )
    
    def clean_description(self):
        """Clean and validate description."""
        description = self.cleaned_data.get('description', '').strip()
        
        if not description:
            raise ValidationError("La descripción es obligatoria.")
        
        if len(description) < 10:
            raise ValidationError("La descripción debe tener al menos 10 caracteres.")
        
        return description


class WorkOrderSearchForm(forms.Form):
    """Form for work order search and filtering."""

    STATUS_CHOICES = [
        ('', 'Todos los Estados'),
        ('draft', 'Borrador'),
        ('scheduled', 'Programada'),
        ('in_progress', 'En Progreso'),
        ('waiting_parts', 'Esperando Partes'),
        ('waiting_approval', 'Esperando Aprobación'),
        ('completed', 'Completada'),
        ('invoiced', 'Facturada'),
        ('cancelled', 'Cancelada'),
    ]

    PRIORITY_CHOICES = [
        ('', 'Todas las Prioridades'),
        ('low', 'Baja'),
        ('normal', 'Normal'),
        ('high', 'Alta'),
        ('urgent', 'Urgente'),
    ]

    SORT_CHOICES = [
        ('created_at', 'Fecha de Creación'),
        ('scheduled_date', 'Fecha Programada'),
        ('priority', 'Prioridad'),
        ('status', 'Estado'),
        ('wo_number', 'Número de Orden'),
        ('client__name', 'Cliente'),
    ]

    ORDER_CHOICES = [
        ('asc', 'Ascendente'),
        ('desc', 'Descendente'),
    ]

    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control search-input',
            'placeholder': 'Buscar por número, cliente o equipo...',
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

    priority = forms.ChoiceField(
        choices=PRIORITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Prioridad'
    )

    technician = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Técnico'
    )

    client = forms.CharField(
        max_length=50,
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

    sort = forms.ChoiceField(
        choices=SORT_CHOICES,
        required=False,
        initial='created_at',
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Ordenar por'
    )

    order = forms.ChoiceField(
        choices=ORDER_CHOICES,
        required=False,
        initial='desc',
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

    def clean(self):
        """Cross-field validation."""
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')

        if date_from and date_to and date_from > date_to:
            raise ValidationError("La fecha 'Desde' no puede ser posterior a la fecha 'Hasta'.")

        return cleaned_data


def get_uom_choices():
    """
    Opciones de Unidad de Medida solo desde BD (cat.uom_codes).
    Si la tabla está vacía o no existe, devuelve un único ítem informativo (no lista fija del frontend).
    """
    empty_msg = [('', 'Sin unidades en catálogo (agregar en cat.uom_codes)')]
    try:
        from core.models import UOMCode
        rows = list(
            UOMCode.objects.all()
            .order_by('uom_code')
            .values_list('uom_code', 'name_es')
        )
        if rows:
            return [(code, label) for code, label in rows]
        return empty_msg
    except Exception as e:
        logger.warning("UOMCode ORM falló, intentando SQL directo: %s", e)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT uom_code, name_es
                FROM cat.uom_codes
                ORDER BY uom_code
                """
            )
            rows = cursor.fetchall()
        if rows:
            return [(r[0], r[1]) for r in rows]
        return empty_msg
    except Exception as e:
        logger.warning("SQL directo a cat.uom_codes falló: %s", e)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT uom_code, name_es
                FROM uom_codes
                ORDER BY uom_code
                """
            )
            rows = cursor.fetchall()
        if rows:
            return [(r[0], r[1]) for r in rows]
        return empty_msg
    except Exception as e:
        logger.warning("SQL directo a uom_codes falló: %s", e)
    return empty_msg


def get_product_category_choices():
    """Opciones de Categoría de producto desde cat.product_category (solo BD)."""
    empty_msg = [('', 'Sin categorías (agregar en cat.product_category)')]
    try:
        from core.models import ProductCategory
        rows = list(
            ProductCategory.objects.filter(is_active=True)
            .order_by('display_order', 'code')
            .values_list('code', 'name_es')
        )
        if rows:
            return [(c, l) for c, l in rows]
        return empty_msg
    except Exception as e:
        logger.warning("ProductCategory ORM falló: %s", e)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT code, name_es FROM cat.product_category
                WHERE is_active = true ORDER BY display_order, code
                """
            )
            rows = cursor.fetchall()
        if rows:
            return [(r[0], r[1]) for r in rows]
        return empty_msg
    except Exception as e:
        logger.warning("SQL cat.product_category falló: %s", e)
    return empty_msg


def get_product_type_choices():
    """Opciones de Tipo de producto desde cat.product_type (solo BD)."""
    empty_msg = [('', 'Sin tipos (agregar en cat.product_type)')]
    try:
        from core.models import ProductType
        rows = list(
            ProductType.objects.filter(is_active=True)
            .order_by('display_order', 'code')
            .values_list('code', 'name_es')
        )
        if rows:
            return [(c, l) for c, l in rows]
        return empty_msg
    except Exception as e:
        logger.warning("ProductType ORM falló: %s", e)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT code, name_es FROM cat.product_type
                WHERE is_active = true ORDER BY display_order, code
                """
            )
            rows = cursor.fetchall()
        if rows:
            return [(r[0], r[1]) for r in rows]
        return empty_msg
    except Exception as e:
        logger.warning("SQL cat.product_type falló: %s", e)
    return empty_msg


class ProductForm(forms.Form):
    """
    Form for product creation and editing with comprehensive validation.
    """

    # Product code validator (alphanumeric, hyphens, underscores)
    product_code_validator = RegexValidator(
        regex=r'^[A-Z0-9\-_]+$',
        message="El código de producto solo puede contener letras mayúsculas, números, guiones y guiones bajos."
    )

    # Name validator (letters, numbers, spaces, hyphens, apostrophes)
    name_validator = RegexValidator(
        regex=r"^[a-zA-ZÀ-ÿ\u00f1\u00d1\d\s\-'\.]+$",
        message="El nombre solo puede contener letras, números, espacios, guiones y apostrofes."
    )

    CATEGORY_CHOICES = [
        ('service', 'Servicio'),
        ('part', 'Parte/Repuesto'),
        ('material', 'Material'),
        ('tool', 'Herramienta'),
        ('consumable', 'Consumible'),
        ('accessory', 'Accesorio'),
    ]

    TYPE_CHOICES = [
        ('service', 'Servicio'),
        ('part', 'Parte'),
        ('material', 'Material'),
    ]

    UNIT_CHOICES = [
        ('unit', 'Unidad'),
        ('hour', 'Hora'),
        ('kg', 'Kilogramo'),
        ('liter', 'Litro'),
        ('meter', 'Metro'),
        ('box', 'Caja'),
        ('pack', 'Paquete'),
        ('set', 'Juego'),
    ]

    product_code = forms.CharField(
        max_length=50,
        validators=[product_code_validator],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'PROD-001',
            'maxlength': '50',
            'required': True,
            'style': 'text-transform: uppercase;'
        }),
        label='Código de Producto',
        help_text='Código único para identificar el producto (ej: SERV-001, PART-001)'
    )

    name = forms.CharField(
        max_length=200,
        validators=[name_validator],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese el nombre del producto',
            'maxlength': '200',
            'required': True
        }),
        label='Nombre del Producto',
        help_text='Nombre descriptivo del producto (máximo 200 caracteres)'
    )

    description = forms.CharField(
        max_length=1000,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Descripción detallada del producto...',
            'rows': 4,
            'maxlength': '1000'
        }),
        label='Descripción',
        help_text='Descripción detallada del producto o servicio'
    )

    category = forms.ChoiceField(
        choices=[],  # se rellena en __init__ desde cat.product_category
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        }),
        label='Categoría',
        help_text='Categoría principal del producto (catálogo cat.product_category)'
    )

    type = forms.ChoiceField(
        choices=[],  # se rellena en __init__ desde cat.product_type
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        }),
        label='Tipo',
        help_text='Tipo específico del producto (catálogo cat.product_type)'
    )

    unit_of_measure = forms.ChoiceField(
        choices=[],  # se rellena en __init__ desde uom_codes
        initial='unit',
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Unidad de Medida',
        help_text='Unidad en la que se mide o vende el producto (catálogo uom_codes)'
    )

    def __init__(self, *args, **kwargs):
        category_choices = kwargs.pop('category_choices', None)
        type_choices = kwargs.pop('type_choices', None)
        unit_choices = kwargs.pop('unit_choices', None)
        super().__init__(*args, **kwargs)
        self.fields['category'].choices = category_choices if category_choices is not None else get_product_category_choices()
        self.fields['type'].choices = type_choices if type_choices is not None else get_product_type_choices()
        self.fields['unit_of_measure'].choices = unit_choices if unit_choices is not None else get_uom_choices()

    price = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'min': '0',
            'step': '0.01'
        }),
        label='Precio Unitario',
        help_text='Precio por unidad en la moneda local'
    )

    cost = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=0,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'min': '0',
            'step': '0.01'
        }),
        label='Costo Unitario',
        help_text='Costo de adquisición por unidad (opcional)'
    )

    estimated_hours = forms.DecimalField(
        max_digits=6,
        decimal_places=2,
        min_value=0,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'min': '0',
            'step': '0.25'
        }),
        label='Horas Estimadas',
        help_text='Horas estimadas para servicios (opcional)'
    )

    minimum_stock = forms.IntegerField(
        min_value=0,
        required=False,
        initial=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0',
            'min': '0'
        }),
        label='Stock Mínimo',
        help_text='Cantidad mínima en inventario antes de generar alerta'
    )

    maximum_stock = forms.IntegerField(
        min_value=0,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0',
            'min': '0'
        }),
        label='Stock Máximo',
        help_text='Cantidad máxima recomendada en inventario'
    )

    supplier = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre del proveedor',
            'maxlength': '200'
        }),
        label='Proveedor',
        help_text='Proveedor principal del producto'
    )

    supplier_code = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Código del proveedor',
            'maxlength': '100'
        }),
        label='Código del Proveedor',
        help_text='Código o referencia del proveedor para este producto'
    )

    is_active = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Producto Activo',
        help_text='Marque si el producto está disponible para uso'
    )

    is_taxable = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Gravable',
        help_text='Marque si el producto está sujeto a impuestos'
    )

    def clean_product_code(self):
        """Clean and validate product code field."""
        product_code = self.cleaned_data.get('product_code', '').strip().upper()

        if not product_code:
            raise ValidationError("El código de producto es obligatorio.")

        if len(product_code) < 3:
            raise ValidationError("El código de producto debe tener al menos 3 caracteres.")

        return product_code

    def clean_name(self):
        """Clean and validate name field."""
        name = self.cleaned_data.get('name', '').strip()

        if not name:
            raise ValidationError("El nombre del producto es obligatorio.")

        if len(name) < 3:
            raise ValidationError("El nombre debe tener al menos 3 caracteres.")

        # Remove excessive whitespace
        name = re.sub(r'\s+', ' ', name)

        return name

    def clean_price(self):
        """Clean and validate price field."""
        price = self.cleaned_data.get('price')

        if price is None:
            raise ValidationError("El precio es obligatorio.")

        if price <= 0:
            raise ValidationError("El precio debe ser mayor que cero.")

        if price > 999999.99:
            raise ValidationError("El precio no puede exceder $999,999.99.")

        return price

    def clean_cost(self):
        """Clean and validate cost field."""
        cost = self.cleaned_data.get('cost')

        if cost is not None:
            if cost < 0:
                raise ValidationError("El costo no puede ser negativo.")

            if cost > 999999.99:
                raise ValidationError("El costo no puede exceder $999,999.99.")

        return cost

    def clean_estimated_hours(self):
        """Clean and validate estimated hours field."""
        hours = self.cleaned_data.get('estimated_hours')

        if hours is not None:
            if hours < 0:
                raise ValidationError("Las horas estimadas no pueden ser negativas.")

            if hours > 100:
                raise ValidationError("Las horas estimadas no pueden exceder 100 horas.")

        return hours

    def clean(self):
        """Perform cross-field validation."""
        cleaned_data = super().clean()

        cost = cleaned_data.get('cost')
        price = cleaned_data.get('price')
        minimum_stock = cleaned_data.get('minimum_stock')
        maximum_stock = cleaned_data.get('maximum_stock')
        category = cleaned_data.get('category')
        estimated_hours = cleaned_data.get('estimated_hours')

        # Validate cost vs price
        if cost is not None and price is not None and cost > price:
            raise ValidationError("El costo no puede ser mayor que el precio de venta.")

        # Validate stock levels
        if minimum_stock is not None and maximum_stock is not None:
            if minimum_stock > maximum_stock:
                raise ValidationError("El stock mínimo no puede ser mayor que el stock máximo.")

        # Validate estimated hours for services
        if category == 'service' and not estimated_hours:
            cleaned_data['estimated_hours'] = 1.0  # Default 1 hour for services

        return cleaned_data


class ProductSearchForm(forms.Form):
    """Form for product search and filtering."""

    CATEGORY_CHOICES = [
        ('', 'Todas las Categorías'),
        ('service', 'Servicios'),
        ('part', 'Partes/Repuestos'),
        ('material', 'Materiales'),
        ('tool', 'Herramientas'),
        ('consumable', 'Consumibles'),
        ('accessory', 'Accesorios'),
    ]

    TYPE_CHOICES = [
        ('', 'Todos los Tipos'),
        ('service', 'Servicio'),
        ('part', 'Parte'),
        ('material', 'Material'),
    ]

    STATUS_CHOICES = [
        ('', 'Todos los Estados'),
        ('active', 'Activos'),
        ('inactive', 'Inactivos'),
        ('low_stock', 'Stock Bajo'),
        ('out_of_stock', 'Sin Stock'),
    ]

    SORT_CHOICES = [
        ('name', 'Nombre'),
        ('product_code', 'Código'),
        ('category', 'Categoría'),
        ('price', 'Precio'),
        ('created_at', 'Fecha de Creación'),
        ('updated_at', 'Última Actualización'),
    ]

    ORDER_CHOICES = [
        ('asc', 'Ascendente'),
        ('desc', 'Descendente'),
    ]

    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control search-input',
            'placeholder': 'Buscar por nombre, código o descripción...',
            'autocomplete': 'off'
        }),
        label='Buscar'
    )

    category = forms.ChoiceField(
        choices=CATEGORY_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Categoría'
    )

    type = forms.ChoiceField(
        choices=TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Tipo'
    )

    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Estado'
    )

    price_min = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=0,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'min': '0',
            'step': '0.01'
        }),
        label='Precio Mínimo'
    )

    price_max = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=0,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'min': '0',
            'step': '0.01'
        }),
        label='Precio Máximo'
    )

    supplier = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Filtrar por proveedor...'
        }),
        label='Proveedor'
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

    def clean(self):
        """Cross-field validation."""
        cleaned_data = super().clean()
        price_min = cleaned_data.get('price_min')
        price_max = cleaned_data.get('price_max')

        if price_min is not None and price_max is not None and price_min > price_max:
            raise ValidationError("El precio mínimo no puede ser mayor que el precio máximo.")

        return cleaned_data


class MaintenanceForm(forms.Form):
    """
    Form for maintenance task creation and editing.
    """
    
    equipment_id = forms.IntegerField(
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        }),
        label='Equipo',
        help_text='Selecciona el equipo para el mantenimiento'
    )

    maintenance_type = forms.ChoiceField(
        choices=[
            ('preventive', 'Preventivo'),
            ('corrective', 'Correctivo'),
            ('predictive', 'Predictivo'),
            ('emergency', 'Emergencia')
        ],
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        }),
        label='Tipo de Mantenimiento'
    )

    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Título del mantenimiento',
            'maxlength': '200',
            'required': True
        }),
        label='Título'
    )

    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Descripción detallada del mantenimiento...',
            'rows': 4
        }),
        label='Descripción'
    )

    scheduled_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local',
            'required': True
        }),
        label='Fecha Programada',
        help_text='Fecha y hora programada para el mantenimiento'
    )

    estimated_duration = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '120',
            'min': '1'
        }),
        label='Duración Estimada (minutos)',
        help_text='Duración estimada en minutos'
    )

    priority = forms.ChoiceField(
        choices=[
            ('low', 'Baja'),
            ('medium', 'Media'),
            ('high', 'Alta'),
            ('critical', 'Crítica')
        ],
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        }),
        label='Prioridad'
    )

    assigned_technician = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre del técnico asignado',
            'maxlength': '100'
        }),
        label='Técnico Asignado'
    )

    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Notas adicionales...',
            'rows': 3
        }),
        label='Notas'
    )

    def clean_scheduled_date(self):
        """Validate that scheduled date is not in the past."""
        from datetime import datetime
        scheduled_date = self.cleaned_data.get('scheduled_date')
        if scheduled_date and scheduled_date < datetime.now():
            raise ValidationError("La fecha programada no puede ser en el pasado.")
        return scheduled_date


class MaintenanceSearchForm(forms.Form):
    """
    Form for searching and filtering maintenance tasks.
    """
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por título, equipo, técnico...',
            'id': 'search-input'
        }),
        label='Buscar'
    )

    equipment_id = forms.IntegerField(
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'equipment-filter'
        }),
        label='Equipo'
    )

    maintenance_type = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Todos los tipos'),
            ('preventive', 'Preventivo'),
            ('corrective', 'Correctivo'),
            ('predictive', 'Predictivo'),
            ('emergency', 'Emergencia')
        ],
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'type-filter'
        }),
        label='Tipo'
    )

    status = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Todos los estados'),
            ('scheduled', 'Programado'),
            ('in_progress', 'En Progreso'),
            ('completed', 'Completado'),
            ('cancelled', 'Cancelado'),
            ('overdue', 'Vencido')
        ],
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'status-filter'
        }),
        label='Estado'
    )

    priority = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Todas las prioridades'),
            ('low', 'Baja'),
            ('medium', 'Media'),
            ('high', 'Alta'),
            ('critical', 'Crítica')
        ],
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'priority-filter'
        }),
        label='Prioridad'
    )

    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'id': 'date-from'
        }),
        label='Desde'
    )

    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'id': 'date-to'
        }),
        label='Hasta'
    )


# Stock Management Forms

class StockMovementForm(forms.Form):
    """
    Form for recording stock movements (in/out transactions).
    """
    
    MOVEMENT_TYPES = [
        ('in', 'Entrada'),
        ('out', 'Salida'),
        ('adjustment', 'Ajuste'),
        ('transfer', 'Transferencia')
    ]
    
    MOVEMENT_REASONS = [
        ('purchase', 'Compra'),
        ('sale', 'Venta'),
        ('return', 'Devolución'),
        ('damage', 'Daño'),
        ('loss', 'Pérdida'),
        ('adjustment', 'Ajuste de Inventario'),
        ('transfer', 'Transferencia entre Almacenes'),
        ('production', 'Producción'),
        ('consumption', 'Consumo')
    ]
    
    product_id = forms.IntegerField(
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        }),
        label='Producto',
        help_text='Selecciona el producto para el movimiento'
    )
    
    warehouse_id = forms.IntegerField(
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Almacén',
        help_text='Almacén donde se realiza el movimiento'
    )
    
    movement_type = forms.ChoiceField(
        choices=MOVEMENT_TYPES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        }),
        label='Tipo de Movimiento'
    )
    
    quantity = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0.01,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0.01',
            'required': True
        }),
        label='Cantidad',
        help_text='Cantidad del movimiento'
    )
    
    unit_cost = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0'
        }),
        label='Costo Unitario',
        help_text='Costo unitario del producto (opcional)'
    )
    
    reason = forms.ChoiceField(
        choices=MOVEMENT_REASONS,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        }),
        label='Motivo del Movimiento'
    )
    
    reference_document = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Número de factura, orden, etc.',
            'maxlength': '100'
        }),
        label='Documento de Referencia',
        help_text='Número de factura, orden de compra, etc. (opcional)'
    )
    
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Notas adicionales sobre el movimiento...',
            'rows': 3
        }),
        label='Notas',
        help_text='Información adicional sobre el movimiento'
    )
    
    def clean_quantity(self):
        """Validate quantity is positive."""
        quantity = self.cleaned_data.get('quantity')
        if quantity and quantity <= 0:
            raise ValidationError("La cantidad debe ser mayor que cero.")
        return quantity


class StockSearchForm(forms.Form):
    """
    Form for searching and filtering stock levels.
    """
    
    STATUS_CHOICES = [
        ('', 'Todos los Estados'),
        ('in_stock', 'En Stock'),
        ('low_stock', 'Stock Bajo'),
        ('out_of_stock', 'Sin Stock'),
        ('overstock', 'Sobrestock')
    ]
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por producto, código...',
            'id': 'search-input'
        }),
        label='Buscar'
    )
    
    category = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Todas las Categorías'),
            ('service', 'Servicios'),
            ('part', 'Repuestos'),
            ('material', 'Materiales'),
            ('tool', 'Herramientas'),
            ('consumable', 'Consumibles'),
            ('accessory', 'Accesorios')
        ],
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'category-filter'
        }),
        label='Categoría'
    )
    
    warehouse_id = forms.IntegerField(
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'warehouse-filter'
        }),
        label='Almacén'
    )
    
    status = forms.ChoiceField(
        required=False,
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'status-filter'
        }),
        label='Estado de Stock'
    )
    
    min_quantity = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0',
            'min': '0',
            'step': '0.01'
        }),
        label='Cantidad Mínima'
    )
    
    max_quantity = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '1000',
            'min': '0',
            'step': '0.01'
        }),
        label='Cantidad Máxima'
    )


class WarehouseForm(forms.Form):
    """
    Form for warehouse creation and editing.
    """
    
    code = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'WH-001',
            'maxlength': '20',
            'required': True,
            'style': 'text-transform: uppercase;'
        }),
        label='Código de Almacén',
        help_text='Código único para identificar el almacén'
    )
    
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Almacén Principal',
            'maxlength': '100',
            'required': True
        }),
        label='Nombre del Almacén'
    )
    
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Descripción del almacén...',
            'rows': 3
        }),
        label='Descripción'
    )
    
    location = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Dirección física del almacén',
            'maxlength': '200'
        }),
        label='Ubicación',
        help_text='Dirección física del almacén'
    )
    
    manager_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre del encargado',
            'maxlength': '100'
        }),
        label='Encargado',
        help_text='Nombre del responsable del almacén'
    )
    
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Activo',
        help_text='Marcar si el almacén está activo'
    )
    
    def clean_code(self):
        """Clean and validate warehouse code."""
        code = self.cleaned_data.get('code', '').strip().upper()
        if not code:
            raise ValidationError("El código de almacén es obligatorio.")
        if len(code) < 2:
            raise ValidationError("El código debe tener al menos 2 caracteres.")
        return code


class WarehouseSearchForm(forms.Form):
    """
    Form for searching and filtering warehouses.
    """
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por código, nombre, ubicación...',
            'id': 'search-input'
        }),
        label='Buscar'
    )
    
    is_active = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Todos'),
            ('true', 'Activos'),
            ('false', 'Inactivos')
        ],
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'status-filter'
        }),
        label='Estado'
    )


class StockAdjustmentForm(forms.Form):
    """
    Form for bulk stock adjustments.
    """
    
    warehouse_id = forms.IntegerField(
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Almacén',
        help_text='Almacén donde realizar el ajuste'
    )
    
    adjustment_reason = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Motivo del ajuste de inventario',
            'maxlength': '200',
            'required': True
        }),
        label='Motivo del Ajuste',
        help_text='Razón para el ajuste de inventario'
    )
    
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Notas adicionales sobre el ajuste...',
            'rows': 3
        }),
        label='Notas'
    )

# Stock Management Forms

class StockMovementForm(forms.Form):
    """
    Form for recording stock movements (in/out).
    """
    
    MOVEMENT_TYPES = [
        ('in', 'Entrada'),
        ('out', 'Salida'),
        ('adjustment', 'Ajuste'),
        ('transfer', 'Transferencia')
    ]
    
    product_id = forms.IntegerField(
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        }),
        label='Producto',
        help_text='Selecciona el producto para el movimiento'
    )
    
    warehouse_id = forms.IntegerField(
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        }),
        label='Almacén',
        help_text='Almacén donde se realiza el movimiento'
    )
    
    movement_type = forms.ChoiceField(
        choices=MOVEMENT_TYPES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        }),
        label='Tipo de Movimiento'
    )
    
    quantity = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0.01,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0.01',
            'required': True
        }),
        label='Cantidad'
    )
    
    unit_cost = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0'
        }),
        label='Costo Unitario',
        help_text='Costo unitario del producto (opcional)'
    )
    
    reference_number = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Número de referencia',
            'maxlength': '50'
        }),
        label='Número de Referencia',
        help_text='Número de factura, orden, etc. (opcional)'
    )
    
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Notas sobre el movimiento...',
            'rows': 3
        }),
        label='Notas'
    )
    
    def clean_quantity(self):
        """Validate quantity is positive."""
        quantity = self.cleaned_data.get('quantity')
        if quantity and quantity <= 0:
            raise ValidationError("La cantidad debe ser mayor que cero.")
        return quantity


class StockSearchForm(forms.Form):
    """
    Form for searching and filtering stock items.
    """
    
    STOCK_STATUS_CHOICES = [
        ('', 'Todos los estados'),
        ('in_stock', 'En Stock'),
        ('low_stock', 'Stock Bajo'),
        ('out_of_stock', 'Sin Stock'),
        ('overstock', 'Sobrestock')
    ]
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por producto, código...',
            'id': 'search-input'
        }),
        label='Buscar'
    )
    
    warehouse_id = forms.IntegerField(
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'warehouse-filter'
        }),
        label='Almacén'
    )
    
    category = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Todas las categorías'),
            ('service', 'Servicios'),
            ('part', 'Repuestos'),
            ('material', 'Materiales'),
            ('tool', 'Herramientas'),
            ('consumable', 'Consumibles'),
            ('accessory', 'Accesorios')
        ],
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'category-filter'
        }),
        label='Categoría'
    )
    
    stock_status = forms.ChoiceField(
        required=False,
        choices=STOCK_STATUS_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'status-filter'
        }),
        label='Estado de Stock'
    )


# Warehouse Management Forms

class WarehouseForm(forms.Form):
    """
    Form for warehouse creation and editing.
    """
    
    code = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'WH-001',
            'maxlength': '20',
            'required': True,
            'style': 'text-transform: uppercase;'
        }),
        label='Código de Almacén',
        help_text='Código único para identificar el almacén'
    )
    
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre del almacén',
            'maxlength': '100',
            'required': True
        }),
        label='Nombre'
    )
    
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Descripción del almacén...',
            'rows': 3
        }),
        label='Descripción'
    )
    
    address = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Dirección del almacén...',
            'rows': 2,
            'maxlength': '500'
        }),
        label='Dirección'
    )
    
    manager_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre del encargado',
            'maxlength': '100'
        }),
        label='Encargado'
    )
    
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Teléfono de contacto',
            'maxlength': '20'
        }),
        label='Teléfono'
    )
    
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'correo@ejemplo.com'
        }),
        label='Correo Electrónico'
    )
    
    is_active = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Activo'
    )
    
    def clean_code(self):
        """Clean and validate warehouse code."""
        code = self.cleaned_data.get('code', '').strip().upper()
        if not code:
            raise ValidationError("El código de almacén es obligatorio.")
        if len(code) < 2:
            raise ValidationError("El código debe tener al menos 2 caracteres.")
        return code


class WarehouseSearchForm(forms.Form):
    """
    Form for searching and filtering warehouses.
    """
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por código, nombre...',
            'id': 'search-input'
        }),
        label='Buscar'
    )
    
    is_active = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Todos'),
            ('true', 'Activos'),
            ('false', 'Inactivos')
        ],
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'status-filter'
        }),
        label='Estado'
    )


class StockAlertForm(forms.Form):
    """
    Form for configuring stock alerts.
    """
    
    product_id = forms.IntegerField(
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        }),
        label='Producto'
    )
    
    warehouse_id = forms.IntegerField(
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        }),
        label='Almacén'
    )
    
    minimum_stock = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'required': True
        }),
        label='Stock Mínimo'
    )
    
    maximum_stock = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0'
        }),
        label='Stock Máximo',
        help_text='Stock máximo recomendado (opcional)'
    )
    
    alert_enabled = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Alertas Habilitadas'
    )
    
    def clean(self):
        """Cross-field validation."""
        cleaned_data = super().clean()
        minimum_stock = cleaned_data.get('minimum_stock')
        maximum_stock = cleaned_data.get('maximum_stock')
        
        if minimum_stock and maximum_stock and minimum_stock >= maximum_stock:
            raise ValidationError("El stock mínimo debe ser menor que el stock máximo.")
        
        return cleaned_data
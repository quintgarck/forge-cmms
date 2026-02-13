"""
Formularios para la gestión de técnicos en la aplicación frontend.
"""
from django import forms
from django.core.validators import RegexValidator, EmailValidator
from django.core.exceptions import ValidationError
import re
from datetime import date


class TechnicianForm(forms.Form):
    """
    Formulario para creación y edición de técnicos con validación completa.
    """

    # Validador de código de empleado (alfanumérico, guiones, guiones bajos)
    employee_code_validator = RegexValidator(
        regex=r'^[A-Z0-9\-_]+$',
        message="El código de empleado solo puede contener letras mayúsculas, números, guiones y guiones bajos."
    )

    # Validador de número de teléfono
    phone_validator = RegexValidator(
        regex=r'^[\d\s\-\(\)\+\.]+$',
        message="Ingrese un número de teléfono válido. Puede incluir números, espacios, guiones y paréntesis."
    )

    # Validador de nombre (letras, espacios, guiones, apóstrofes)
    name_validator = RegexValidator(
        regex=r"^[a-zA-ZÀ-ÿ\u00f1\u00d1\s\-'\.]+$",
        message="El nombre solo puede contener letras, espacios, guiones y apóstrofes."
    )

    employee_code = forms.CharField(
        max_length=20,
        validators=[employee_code_validator],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'TECH-001',
            'maxlength': '20',
            'required': True,
            'style': 'text-transform: uppercase;'
        }),
        label='Código de Empleado',
        help_text='Código único para identificar al técnico (ej: TECH-001)'
    )

    first_name = forms.CharField(
        max_length=50,
        validators=[name_validator],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese el nombre del técnico',
            'maxlength': '50',
            'required': True,
            'autocomplete': 'given-name'
        }),
        label='Nombre',
        help_text='Nombre del técnico (máximo 50 caracteres)'
    )

    last_name = forms.CharField(
        max_length=50,
        validators=[name_validator],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese el apellido del técnico',
            'maxlength': '50',
            'required': True,
            'autocomplete': 'family-name'
        }),
        label='Apellido',
        help_text='Apellido del técnico (máximo 50 caracteres)'
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
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '82363829 o (55) 1234-5678',
            'maxlength': '20',
            'autocomplete': 'tel'
        }),
        label='Teléfono',
        help_text='Número de teléfono de contacto (opcional)'
    )

    mobile = forms.CharField(
        max_length=20,
        validators=[phone_validator],
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '82363829 o (55) 1234-5678',
            'maxlength': '20',
            'autocomplete': 'tel'
        }),
        label='Móvil',
        help_text='Número de móvil de contacto (opcional)'
    )

    birth_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Fecha de Nacimiento',
        help_text='Fecha de nacimiento del técnico (debe ser mayor de 18 años)'
    )

    hire_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'required': True
        }),
        label='Fecha de Contratación',
        help_text='Fecha en que fue contratado el técnico'
    )

    hourly_rate = forms.DecimalField(
        max_digits=8,
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
        label='Tarifa por Hora',
        help_text='Tarifa por hora del técnico en la moneda local'
    )

    daily_rate = forms.DecimalField(
        max_digits=8,
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
        label='Tarifa Diaria',
        help_text='Tarifa por día completo de trabajo'
    )

    overtime_multiplier = forms.DecimalField(
        max_digits=3,
        decimal_places=2,
        min_value=1.0,
        max_value=5.0,
        required=False,
        initial=1.50,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '1.50',
            'min': '1.0',
            'max': '5.0',
            'step': '0.01'
        }),
        label='Multiplicador Horas Extra',
        help_text='Multiplicador para horas extra (ej: 1.5 = 150%)'
    )

    status = forms.ChoiceField(
        choices=[
            ('ACTIVE', 'Activo'),
            ('INACTIVE', 'Inactivo'),
            ('SUSPENDED', 'Suspendido'),
        ],
        initial='ACTIVE',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        }),
        label='Estado',
        help_text='Estado actual del técnico'
    )

    certification_level = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Junior, Senior, Master...',
            'maxlength': '50'
        }),
        label='Nivel de Certificación',
        help_text='Nivel de certificación del técnico (opcional)'
    )

    specialization = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Especializaciones del técnico, separadas por comas...',
            'rows': 3,
            'maxlength': '500'
        }),
        label='Especialización',
        help_text='Especializaciones del técnico, separadas por comas (opcional)'
    )

    certifications = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Certificaciones del técnico, separadas por comas...',
            'rows': 3,
            'maxlength': '500'
        }),
        label='Certificaciones',
        help_text='Certificaciones del técnico, separadas por comas (opcional)'
    )

    # Horario de trabajo - Campos individuales por día
    monday_schedule = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '08:00-17:00',
            'pattern': '\d{2}:\d{2}-\d{2}:\d{2}'
        }),
        label='Lunes',
        help_text='Formato: HH:MM-HH:MM (ej: 08:00-17:00) o dejar vacío si no trabaja'
    )

    tuesday_schedule = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '08:00-17:00',
            'pattern': '\d{2}:\d{2}-\d{2}:\d{2}'
        }),
        label='Martes'
    )

    wednesday_schedule = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '08:00-17:00',
            'pattern': '\d{2}:\d{2}-\d{2}:\d{2}'
        }),
        label='Miércoles'
    )

    thursday_schedule = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '08:00-17:00',
            'pattern': '\d{2}:\d{2}-\d{2}:\d{2}'
        }),
        label='Jueves'
    )

    friday_schedule = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '08:00-17:00',
            'pattern': '\d{2}:\d{2}-\d{2}:\d{2}'
        }),
        label='Viernes'
    )

    saturday_schedule = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '08:00-13:00',
            'pattern': '\d{2}:\d{2}-\d{2}:\d{2}'
        }),
        label='Sábado'
    )

    sunday_schedule = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Descanso',
            'pattern': '\d{2}:\d{2}-\d{2}:\d{2}'
        }),
        label='Domingo'
    )

    efficiency_avg = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        min_value=0,
        max_value=200,
        required=False,
        initial=100.00,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '100.00',
            'min': '0',
            'max': '200',
            'step': '0.01'
        }),
        label='Eficiencia Promedio (%)',
        help_text='Eficiencia promedio del técnico en porcentaje (100 = normal)'
    )

    quality_score = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        min_value=0,
        max_value=100,
        required=False,
        initial=100.00,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '100.00',
            'min': '0',
            'max': '100',
            'step': '0.01'
        }),
        label='Puntuación de Calidad (%)',
        help_text='Puntuación de calidad del trabajo (0-100)'
    )

    is_active = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Técnico Activo',
        help_text='Marque si el técnico está activo'
    )

    notes = forms.CharField(
        max_length=1000,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Notas adicionales sobre el técnico...',
            'rows': 4,
            'maxlength': '1000'
        }),
        label='Notas',
        help_text='Notas adicionales (opcional)'
    )

    def clean_employee_code(self):
        """Limpiar y validar campo de código de empleado."""
        employee_code = self.cleaned_data.get('employee_code', '').strip().upper()

        if not employee_code:
            raise ValidationError("El código de empleado es obligatorio.")

        if len(employee_code) < 3:
            raise ValidationError("El código de empleado debe tener al menos 3 caracteres.")

        return employee_code

    def clean_first_name(self):
        """Limpiar y validar campo de nombre."""
        first_name = self.cleaned_data.get('first_name', '').strip()

        if not first_name:
            raise ValidationError("El nombre es obligatorio.")

        if len(first_name) < 2:
            raise ValidationError("El nombre debe tener al menos 2 caracteres.")

        # Verificar espacios consecutivos
        if '  ' in first_name:
            raise ValidationError("El nombre no puede tener espacios consecutivos.")

        # Capitalizar cada palabra adecuadamente
        first_name = ' '.join(word.capitalize() for word in first_name.split())

        return first_name

    def clean_last_name(self):
        """Limpiar y validar campo de apellido."""
        last_name = self.cleaned_data.get('last_name', '').strip()

        if not last_name:
            raise ValidationError("El apellido es obligatorio.")

        if len(last_name) < 2:
            raise ValidationError("El apellido debe tener al menos 2 caracteres.")

        # Verificar espacios consecutivos
        if '  ' in last_name:
            raise ValidationError("El apellido no puede tener espacios consecutivos.")

        # Capitalizar cada palabra adecuadamente
        last_name = ' '.join(word.capitalize() for word in last_name.split())

        return last_name

    def clean_email(self):
        """Limpiar y validar campo de email."""
        email = self.cleaned_data.get('email', '').strip().lower()

        if not email:
            raise ValidationError("El correo electrónico es obligatorio.")

        # Validación adicional de email
        if email.count('@') != 1:
            raise ValidationError("El correo electrónico debe contener exactamente un símbolo @.")

        local_part, domain = email.split('@')

        if not local_part or not domain:
            raise ValidationError("El correo electrónico no tiene un formato válido.")

        if len(local_part) > 64:
            raise ValidationError("La parte local del correo es demasiado larga.")

        return email

    def clean_phone(self):
        """Limpiar y validar campo de teléfono."""
        phone = self.cleaned_data.get('phone', '').strip()

        if phone:  # Si se proporciona, validar
            # Remover todos los caracteres no dígitos para validación
            digits_only = re.sub(r'\D', '', phone)

            if len(digits_only) < 8:
                raise ValidationError("El número de teléfono debe tener al menos 8 dígitos.")

            if len(digits_only) > 15:
                raise ValidationError("El número de teléfono no puede tener más de 15 dígitos.")

        # Devolver el teléfono original formateado para visualización
        return phone

    def clean_mobile(self):
        """Limpiar y validar campo de móvil."""
        mobile = self.cleaned_data.get('mobile', '').strip()

        if mobile:  # Si se proporciona, validar
            # Remover todos los caracteres no dígitos para validación
            digits_only = re.sub(r'\D', '', mobile)

            if len(digits_only) < 8:
                raise ValidationError("El número de móvil debe tener al menos 8 dígitos.")

            if len(digits_only) > 15:
                raise ValidationError("El número de móvil no puede tener más de 15 dígitos.")

        # Devolver el móvil original formateado para visualización
        return mobile

    def clean_birth_date(self):
        """Limpiar y validar campo de fecha de nacimiento."""
        birth_date = self.cleaned_data.get('birth_date')

        if birth_date:
            if birth_date > date.today():
                raise ValidationError("La fecha de nacimiento no puede ser futura.")
            
            # Calcular edad
            age = (date.today() - birth_date).days // 365
            if age < 18:
                raise ValidationError("El técnico debe tener al menos 18 años.")
            if age > 100:
                raise ValidationError("La fecha de nacimiento no parece válida.")

        return birth_date

    def clean_hire_date(self):
        """Limpiar y validar campo de fecha de contratación."""
        hire_date = self.cleaned_data.get('hire_date')

        if not hire_date:
            raise ValidationError("La fecha de contratación es obligatoria.")

        if hire_date > date.today():
            raise ValidationError("La fecha de contratación no puede ser futura.")

        return hire_date

    def clean_hourly_rate(self):
        """Limpiar y validar campo de tarifa por hora."""
        hourly_rate = self.cleaned_data.get('hourly_rate')

        if hourly_rate is None:
            return 0.00

        if hourly_rate < 0:
            raise ValidationError("La tarifa por hora no puede ser negativa.")

        if hourly_rate > 999999.99:
            raise ValidationError("La tarifa por hora no puede exceder $999,999.99.")

        return hourly_rate

    def clean_daily_rate(self):
        """Limpiar y validar campo de tarifa diaria."""
        daily_rate = self.cleaned_data.get('daily_rate')

        if daily_rate is None:
            return 0.00

        if daily_rate < 0:
            raise ValidationError("La tarifa diaria no puede ser negativa.")

        if daily_rate > 9999.99:
            raise ValidationError("La tarifa diaria no puede exceder $9,999.99.")

        return daily_rate

    def clean_overtime_multiplier(self):
        """Limpiar y validar multiplicador de horas extra."""
        overtime_multiplier = self.cleaned_data.get('overtime_multiplier')

        if overtime_multiplier is None:
            return 1.50

        if overtime_multiplier < 1.0:
            raise ValidationError("El multiplicador debe ser al menos 1.0.")

        if overtime_multiplier > 5.0:
            raise ValidationError("El multiplicador no puede exceder 5.0.")

        return overtime_multiplier

    def clean_specialization(self):
        """Limpiar y validar campo de especializaciones."""
        specialization = self.cleaned_data.get('specialization', '').strip()

        if specialization:
            # Validar longitud de cada especialización
            specs = [spec.strip() for spec in specialization.split(',') if spec.strip()]
            for spec in specs:
                if len(spec) > 50:
                    raise ValidationError(f"La especialización '{spec}' excede los 50 caracteres.")
            # Devolver como string separado por comas (el backend lo convertirá a lista)
            return ','.join(specs)

        return specialization

    def clean_certifications(self):
        """Limpiar y validar campo de certificaciones."""
        certifications = self.cleaned_data.get('certifications', '').strip()

        if certifications:
            # Validar longitud de cada certificación
            certs = [cert.strip() for cert in certifications.split(',') if cert.strip()]
            for cert in certs:
                if len(cert) > 50:
                    raise ValidationError(f"La certificación '{cert}' excede los 50 caracteres.")
            # Devolver como string separado por comas (el backend lo convertirá a lista)
            return ','.join(certs)

        return certifications

    def clean_efficiency_avg(self):
        """Limpiar y validar eficiencia promedio."""
        efficiency_avg = self.cleaned_data.get('efficiency_avg')
        
        if efficiency_avg is None:
            return 100.00
        
        if efficiency_avg < 0:
            raise ValidationError("La eficiencia no puede ser negativa.")
        
        if efficiency_avg > 200:
            raise ValidationError("La eficiencia no puede exceder 200%.")
        
        return efficiency_avg

    def clean_quality_score(self):
        """Limpiar y validar puntuación de calidad."""
        quality_score = self.cleaned_data.get('quality_score')
        
        if quality_score is None:
            return 100.00
        
        if quality_score < 0:
            raise ValidationError("La puntuación de calidad no puede ser negativa.")
        
        if quality_score > 100:
            raise ValidationError("La puntuación de calidad no puede exceder 100.")
        
        return quality_score

    def clean(self):
        """Realizar validación entre campos y construir work_schedule JSON."""
        cleaned_data = super().clean()

        email = cleaned_data.get('email')
        phone = cleaned_data.get('phone')
        mobile = cleaned_data.get('mobile')

        # Validar que al menos uno de los métodos de contacto esté presente
        if not phone and not mobile and not email:
            raise ValidationError("Debe proporcionar al menos un método de contacto (teléfono, móvil o email).")

        # Construir work_schedule a partir de los campos individuales
        import json
        schedule = {}
        
        if cleaned_data.get('monday_schedule'):
            schedule['lunes'] = cleaned_data['monday_schedule'].strip()
        if cleaned_data.get('tuesday_schedule'):
            schedule['martes'] = cleaned_data['tuesday_schedule'].strip()
        if cleaned_data.get('wednesday_schedule'):
            schedule['miercoles'] = cleaned_data['wednesday_schedule'].strip()
        if cleaned_data.get('thursday_schedule'):
            schedule['jueves'] = cleaned_data['thursday_schedule'].strip()
        if cleaned_data.get('friday_schedule'):
            schedule['viernes'] = cleaned_data['friday_schedule'].strip()
        if cleaned_data.get('saturday_schedule'):
            schedule['sabado'] = cleaned_data['saturday_schedule'].strip()
        if cleaned_data.get('sunday_schedule'):
            schedule['domingo'] = cleaned_data['sunday_schedule'].strip()
        
        # Guardar el JSON construido como work_schedule
        cleaned_data['work_schedule'] = schedule if schedule else None

        return cleaned_data


class TechnicianSearchForm(forms.Form):
    """Formulario para búsqueda y filtrado de técnicos."""

    STATUS_CHOICES = [
        ('', 'Todos los estados'),
        ('active', 'Activos'),
        ('inactive', 'Inactivos'),
        ('suspended', 'Suspendidos'),
    ]

    SORT_CHOICES = [
        ('last_name', 'Apellido'),
        ('first_name', 'Nombre'),
        ('employee_code', 'Código de empleado'),
        ('hire_date', 'Fecha de contratación'),
        ('hourly_rate', 'Tarifa por hora'),
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
            'placeholder': 'Buscar por nombre, apellido, email o código...',
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
        initial='last_name',
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
        """Limpiar consulta de búsqueda."""
        search = self.cleaned_data.get('search', '').strip()

        if search and len(search) < 2:
            raise ValidationError("La búsqueda debe tener al menos 2 caracteres.")

        return search
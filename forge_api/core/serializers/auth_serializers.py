"""
ForgeDB API REST - Authentication Serializers
Serializers for authentication and user management
"""

from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from ..models import Technician, TechnicianUser


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login with employee code/username and password
    """
    employee_code = serializers.CharField(
        max_length=20,
        help_text="Employee code (username)",
        required=False
    )
    username = serializers.CharField(
        max_length=150,
        help_text="Username (alternative to employee_code)",
        required=False
    )
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text="User password"
    )
    
    def validate(self, attrs):
        employee_code = attrs.get('employee_code')
        username = attrs.get('username')
        password = attrs.get('password')
        
        # Use employee_code if provided, otherwise use username
        login_field = employee_code or username
        
        if login_field and password:
            user = authenticate(
                request=self.context.get('request'),
                username=login_field,
                password=password
            )
            
            if not user:
                raise serializers.ValidationError(
                    'Unable to log in with provided credentials.',
                    code='authorization'
                )
            
            if not user.is_active:
                raise serializers.ValidationError(
                    'User account is disabled.',
                    code='authorization'
                )
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError(
                'Must include ("employee_code" or "username") and "password".',
                code='authorization'
            )


class TokenResponseSerializer(serializers.Serializer):
    """
    Serializer for token response documentation
    """
    access = serializers.CharField(help_text="JWT access token")
    refresh = serializers.CharField(help_text="JWT refresh token")
    user = serializers.DictField(help_text="User information")


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile information
    """
    full_name = serializers.CharField(read_only=True)
    is_workshop_admin = serializers.SerializerMethodField()
    can_manage_inventory = serializers.SerializerMethodField()
    can_manage_clients = serializers.SerializerMethodField()
    can_view_reports = serializers.SerializerMethodField()
    technician_info = serializers.SerializerMethodField()
    
    class Meta:
        model = TechnicianUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 
            'full_name', 'is_workshop_admin', 
            'can_manage_inventory', 'can_manage_clients', 'can_view_reports',
            'technician_info', 'date_joined', 'last_login'
        ]
        read_only_fields = [
            'id', 'username', 'date_joined', 'last_login', 'full_name'
        ]
    
    def get_is_workshop_admin(self, obj):
        """Get workshop admin status"""
        return obj.is_workshop_admin
    
    def get_can_manage_inventory(self, obj):
        """Get inventory management permission"""
        return obj.can_manage_inventory
    
    def get_can_manage_clients(self, obj):
        """Get client management permission"""
        return obj.can_manage_clients
    
    def get_can_view_reports(self, obj):
        """Get report viewing permission"""
        return obj.can_view_reports
    
    def get_technician_info(self, obj):
        """Get related technician information"""
        if obj.technician:
            return {
                'technician_id': obj.technician.technician_id,
                'employee_code': obj.technician.employee_code,
                'hire_date': obj.technician.hire_date,
                'status': obj.technician.status,
                'specializations': obj.technician.specialization or [],  # Changed to specialization (singular)
                'certifications': obj.technician.certifications or [],
            }
        return None


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for changing user password
    """
    current_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text="Current password"
    )
    new_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text="New password"
    )
    confirm_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text="Confirm new password"
    )
    
    def validate(self, attrs):
        new_password = attrs.get('new_password')
        confirm_password = attrs.get('confirm_password')
        
        if new_password != confirm_password:
            raise serializers.ValidationError(
                "New password and confirmation do not match."
            )
        
        return attrs


class TechnicianSerializer(serializers.ModelSerializer):
    """
    Serializer for technician information in authentication context
    """
    full_name = serializers.CharField(read_only=True)
    has_user_account = serializers.SerializerMethodField()
    # Map specializations to specialization (ArrayField in model)
    specializations = serializers.ListField(
        child=serializers.CharField(max_length=100),
        source='specialization',
        required=False,
        allow_null=True,
        default=list
    )
    # certifications is also an ArrayField
    certifications = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        allow_null=True,
        default=list
    )
    
    class Meta:
        model = Technician
        fields = [
            'technician_id', 'employee_code', 'first_name', 'last_name',
            'full_name', 'email', 'phone', 'mobile', 'hire_date',
            'status', 'specializations', 'certifications', 'has_user_account'
        ]
        read_only_fields = ['technician_id', 'full_name', 'has_user_account']
    
    def to_internal_value(self, data):
        """Override to handle JSON string arrays properly"""
        import json
        # Handle specializations if it's a JSON string
        if 'specializations' in data:
            if isinstance(data['specializations'], str):
                try:
                    data['specializations'] = json.loads(data['specializations'])
                except (json.JSONDecodeError, ValueError):
                    pass
        # Handle certifications if it's a JSON string  
        if 'certifications' in data:
            if isinstance(data['certifications'], str):
                try:
                    data['certifications'] = json.loads(data['certifications'])
                except (json.JSONDecodeError, ValueError):
                    pass
        return super().to_internal_value(data)
    
    def create(self, validated_data):
        """Override create to ensure arrays are properly formatted"""
        import json
        # Ensure specialization is a list, not a JSON string
        if 'specialization' in validated_data:
            spec = validated_data['specialization']
            if isinstance(spec, str):
                try:
                    validated_data['specialization'] = json.loads(spec)
                except (json.JSONDecodeError, ValueError):
                    validated_data['specialization'] = []
            elif spec is None:
                validated_data['specialization'] = []
        
        # Ensure certifications is a list, not a JSON string
        if 'certifications' in validated_data:
            cert = validated_data['certifications']
            if isinstance(cert, str):
                try:
                    validated_data['certifications'] = json.loads(cert)
                except (json.JSONDecodeError, ValueError):
                    validated_data['certifications'] = []
            elif cert is None:
                validated_data['certifications'] = []
        
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Override update to ensure arrays are properly formatted"""
        import json
        # Ensure specialization is a list, not a JSON string
        if 'specialization' in validated_data:
            spec = validated_data['specialization']
            if isinstance(spec, str):
                try:
                    validated_data['specialization'] = json.loads(spec)
                except (json.JSONDecodeError, ValueError):
                    validated_data['specialization'] = []
            elif spec is None:
                validated_data['specialization'] = []
        
        # Ensure certifications is a list, not a JSON string
        if 'certifications' in validated_data:
            cert = validated_data['certifications']
            if isinstance(cert, str):
                try:
                    validated_data['certifications'] = json.loads(cert)
                except (json.JSONDecodeError, ValueError):
                    validated_data['certifications'] = []
            elif cert is None:
                validated_data['certifications'] = []
        
        return super().update(instance, validated_data)
    
    def get_has_user_account(self, obj):
        """Check if technician has a user account"""
        return hasattr(obj, 'user_account') and obj.user_account is not None


class CreateUserAccountSerializer(serializers.Serializer):
    """
    Serializer for creating user accounts for existing technicians
    """
    technician_id = serializers.IntegerField(help_text="Technician ID")
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text="Initial password for the user account",
        required=False
    )
    role = serializers.ChoiceField(
        choices=[
            ('admin', 'Administrator'),
            ('manager', 'Manager'),
            ('technician', 'Technician'),
            ('viewer', 'Viewer'),
        ],
        default='technician',
        help_text="User role"
    )
    is_workshop_admin = serializers.BooleanField(
        default=False,
        help_text="Grant workshop admin privileges"
    )
    can_manage_inventory = serializers.BooleanField(
        default=False,
        help_text="Grant inventory management privileges"
    )
    can_manage_clients = serializers.BooleanField(
        default=False,
        help_text="Grant client management privileges"
    )
    can_view_reports = serializers.BooleanField(
        default=True,
        help_text="Grant report viewing privileges"
    )
    
    def validate_technician_id(self, value):
        """Validate that technician exists and doesn't have an account"""
        try:
            technician = Technician.objects.get(technician_id=value)
            if hasattr(technician, 'user_account') and technician.user_account:
                raise serializers.ValidationError(
                    "This technician already has a user account."
                )
            return value
        except Technician.DoesNotExist:
            raise serializers.ValidationError(
                "Technician with this ID does not exist."
            )
    
    def validate_password(self, value):
        """Validate password strength"""
        if value:
            try:
                validate_password(value)
            except ValidationError as e:
                raise serializers.ValidationError(list(e.messages))
        return value


class UserPermissionsSerializer(serializers.Serializer):
    """
    Serializer for user permissions response
    """
    is_workshop_admin = serializers.BooleanField()
    can_manage_inventory = serializers.BooleanField()
    can_manage_clients = serializers.BooleanField()
    can_view_reports = serializers.BooleanField()
    role = serializers.CharField()


class PermissionCheckSerializer(serializers.Serializer):
    """
    Serializer for permission check response
    """
    permission = serializers.CharField()
    has_permission = serializers.BooleanField()
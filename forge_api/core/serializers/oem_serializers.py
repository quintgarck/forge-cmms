"""
OEM Serializers - Serializers for OEM Brand, Catalog Item, and Equivalence models.
"""
from rest_framework import serializers
from ..models import OEMBrand, OEMCatalogItem, OEMEquivalence, OEMPartImage, Technician


class TechnicianSimpleSerializer(serializers.ModelSerializer):
    """Simplified technician serializer for read-only fields"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Technician
        fields = ['technician_id', 'employee_code', 'full_name', 'email']
        read_only_fields = fields
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}" if obj else None


class OEMBrandSerializer(serializers.ModelSerializer):
    """Serializer for OEM Brand model"""
    brand_type_display = serializers.CharField(source='get_brand_type_display', read_only=True)
    is_active_display = serializers.BooleanField(source='is_active', read_only=True)
    
    class Meta:
        model = OEMBrand
        fields = [
            'brand_id', 'oem_code', 'name', 'brand_type', 'brand_type_display',
            'country', 'website', 'support_email', 'logo_url',
            'is_active', 'is_active_display', 'display_order',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class OEMBrandCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating OEM Brand"""
    
    class Meta:
        model = OEMBrand
        fields = ['oem_code', 'name', 'brand_type', 'country', 'website', 
                  'support_email', 'logo_url', 'is_active', 'display_order']


class OEMCatalogItemSerializer(serializers.ModelSerializer):
    """Serializer for OEM Catalog Item model"""
    oem_brand_name = serializers.CharField(source='oem_code.name', read_only=True)
    oem_brand_code = serializers.CharField(source='oem_code.oem_code', read_only=True)
    item_type_display = serializers.CharField(source='get_item_type_display', read_only=True)
    part_number_type_display = serializers.CharField(source='get_part_number_type_display', read_only=True)
    technical_images = serializers.SerializerMethodField()
    
    class Meta:
        model = OEMCatalogItem
        fields = [
            'catalog_id', 'oem_code', 'oem_brand_name', 'oem_brand_code',
            'item_type', 'item_type_display',
            'part_number', 'part_number_type', 'part_number_type_display',
            'description_es', 'description_en',
            'group_code',
            # Vehicle/Equipment fields
            'body_style', 'year_start', 'year_end',
            # Part fields
            'weight_kg', 'dimensions', 'material',
            # Imagen principal
            'primary_image_url',
            # Technical images (figuras isométricas, diagramas, etc.)
            'technical_images',
            # Fitment information
            'vin_patterns', 'model_codes', 'body_codes', 'engine_codes',
            'transmission_codes', 'axle_codes', 'color_codes', 'trim_codes',
            'manual_types', 'manual_refs',
            # Pricing
            'list_price', 'net_price', 'currency_code', 'oem_lead_time_days',
            # Status
            'is_discontinued', 'is_active', 'display_order',
            'valid_from', 'valid_until',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_technical_images(self, obj):
        """Obtener imágenes técnicas de la parte"""
        try:
            images = OEMPartImage.objects.filter(catalog_item=obj, is_active=True).order_by('display_order')
            return OEMPartImageSerializer(images, many=True).data
        except Exception:
            return []


class OEMCatalogItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating OEM Catalog Item"""
    
    class Meta:
        model = OEMCatalogItem
        fields = [
            'oem_code', 'item_type', 'part_number', 'part_number_type',
            'description_es', 'description_en', 'group_code',
            'body_style', 'year_start', 'year_end',
            'weight_kg', 'dimensions', 'material',
            'vin_patterns', 'model_codes', 'body_codes', 'engine_codes',
            'transmission_codes', 'axle_codes', 'color_codes', 'trim_codes',
            'manual_types', 'manual_refs',
            'list_price', 'net_price', 'currency_code', 'oem_lead_time_days',
            'is_discontinued', 'is_active', 'display_order',
            'valid_from', 'valid_until'
        ]


class OEMEquivalenceSerializer(serializers.ModelSerializer):
    """Serializer for OEM Equivalence model"""
    oem_brand_name = serializers.CharField(source='oem_code.name', read_only=True)
    oem_brand_code = serializers.CharField(source='oem_code.oem_code', read_only=True)
    equivalence_type_display = serializers.CharField(source='get_equivalence_type_display', read_only=True)
    verified_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = OEMEquivalence
        fields = [
            'equivalence_id', 'oem_part_number', 
            'oem_code', 'oem_brand_name', 'oem_brand_code',
            'aftermarket_sku', 
            'equivalence_type', 'equivalence_type_display',
            'confidence_score', 'notes',
            'verified_by', 'verified_by_name', 'verified_date',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_verified_by_name(self, obj):
        if obj.verified_by:
            return f"{obj.verified_by.first_name} {obj.verified_by.last_name}"
        return None


class OEMEquivalenceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating OEM Equivalence"""
    
    class Meta:
        model = OEMEquivalence
        fields = [
            'oem_part_number', 'oem_code', 'aftermarket_sku',
            'equivalence_type', 'confidence_score', 'notes'
        ]


class OEMEquivalenceBulkCreateSerializer(serializers.Serializer):
    """Serializer for bulk creating equivalences"""
    equivalences = OEMEquivalenceCreateSerializer(many=True)
    
    def create(self, validated_data):
        equivalences_data = validated_data.pop('equivalences')
        equivalences = []
        for eq_data in equivalences_data:
            equivalences.append(OEMEquivalence.objects.create(**eq_data))
        return equivalences


class OEMPartImageSerializer(serializers.ModelSerializer):
    """Serializer for OEM Part Technical Images"""
    image_type_display = serializers.CharField(source='get_image_type_display', read_only=True)
    
    class Meta:
        model = OEMPartImage
        fields = [
            'image_id', 'catalog_item', 'image_type', 'image_type_display',
            'image_url', 'thumbnail_url', 'title', 'description',
            'hotspot_data', 'part_position', 'page_number', 'total_pages',
            'image_width', 'image_height', 'file_size', 'mime_type',
            'reference_codes', 'display_order', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class OEMPartImageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating OEM Part Technical Images"""
    
    class Meta:
        model = OEMPartImage
        fields = [
            'catalog_item', 'image_type', 'image_url', 'thumbnail_url',
            'title', 'description', 'hotspot_data', 'part_position',
            'page_number', 'total_pages', 'image_width', 'image_height',
            'file_size', 'mime_type', 'reference_codes', 'display_order',
            'is_active'
        ]


class OEMPartImageBulkCreateSerializer(serializers.Serializer):
    """Serializer for bulk creating part images"""
    images = OEMPartImageCreateSerializer(many=True)
    
    def create(self, validated_data):
        images_data = validated_data.pop('images')
        images = []
        for img_data in images_data:
            images.append(OEMPartImage.objects.create(**img_data))
        return images


class OEMPartCompatibilitySerializer(serializers.Serializer):
    """Serializer for part compatibility information"""
    part_number = serializers.CharField()
    brand = serializers.CharField()
    description = serializers.CharField(required=False, allow_null=True)
    compatible_models = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )
    confidence_score = serializers.IntegerField()

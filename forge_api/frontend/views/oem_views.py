"""OEM and manufacturer management views.
Handles OEMManufacturer, OEMPartNumber, and OEMCrossReference interfaces.
"""
import logging
from datetime import date, timedelta
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.views import View
from django.http import JsonResponse, HttpResponse
from django.urls import reverse_lazy
from django.conf import settings
from django import forms
from django.template.loader import render_to_string
from django.utils import timezone
import io
import csv
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
try:
    import xlsxwriter
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False

from ..services.api_client import ForgeAPIClient, APIException
from ..mixins import APIClientMixin
from ..forms.oem_forms import (
    OEMBrandForm, 
    OEMCatalogItemForm,
    OEMBrandSearchForm,
    OEMCatalogItemSearchForm
)

logger = logging.getLogger(__name__)


class OEMCatalogIndexView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Índice principal del catálogo OEM con acceso a todos los módulos."""
    template_name = 'frontend/oem/oem_catalog_index.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            api_client = self.get_api_client()
            
            # Get statistics from various APIs
            stats = {
                'total_brands': 0,
                'total_parts': 0,
                'total_cross_refs': 0,
                'total_equivalences': 0,
                'imported_products': 0,
                'pending_import': 0,
            }
            
            # Get brands count
            try:
                brands_response = api_client.get_oem_brands(page_size=1)
                stats['total_brands'] = brands_response.get('count', 0)
            except Exception:
                pass
            
            # Get parts count
            try:
                parts_response = api_client.get_oem_catalog_items(page_size=1)
                stats['total_parts'] = parts_response.get('count', 0)
            except Exception:
                pass
            
            # Get equivalences count
            try:
                eq_response = api_client.get('oem/equivalences/', page_size=1)
                stats['total_equivalences'] = eq_response.get('count', 0)
            except Exception:
                pass
            
            # Mock values for cross_refs and import stats (would need specific endpoints)
            stats['total_cross_refs'] = stats['total_equivalences'] * 2  # Estimate
            stats['imported_products'] = 0  # Would come from inventory/products/ API
            stats['pending_import'] = stats['total_parts'] - stats['imported_products']
            
            context['stats'] = stats
            
        except APIException as e:
            logger.error(f"Error loading OEM catalog stats: {e}")
            context['stats'] = {
                'total_brands': 0,
                'total_parts': 0,
                'total_cross_refs': 0,
                'total_equivalences': 0,
                'imported_products': 0,
                'pending_import': 0,
            }
        except Exception as e:
            logger.error(f"Unexpected error loading OEM catalog stats: {e}")
            context['stats'] = {
                'total_brands': 0,
                'total_parts': 0,
                'total_cross_refs': 0,
                'total_equivalences': 0,
                'imported_products': 0,
                'pending_import': 0,
            }
        
        return context


class OEMManufacturerManagementView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Comprehensive OEM manufacturer management."""
    template_name = 'frontend/oem/brand_management.html'
    login_url = 'frontend:login'
    paginate_by = 20
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get filter parameters
        search = self.request.GET.get('search', '').strip()
        country_filter = self.request.GET.get('country', '')
        is_active = self.request.GET.get('is_active', '')
        page = self._get_page_number()
        
        try:
            api_client = self.get_api_client()
            
            # Build filters for API
            filters = {}
            if search:
                filters['search'] = search
            if country_filter:
                filters['country'] = country_filter
            if is_active:
                filters['is_active'] = is_active.lower() == 'true'
            
            # Get brands from API
            brands_response = api_client.get_oem_brands(
                page=page,
                page_size=self.paginate_by,
                **filters
            )
            
            brands = brands_response.get('results', [])
            total_count = brands_response.get('count', 0)
            
            # Process brands for enhanced display
            for brand in brands:
                # Add status styling
                is_active_brand = brand.get('is_active', True)
                brand['status'] = 'ACTIVE' if is_active_brand else 'INACTIVE'
                brand['status_label'] = 'Activo' if is_active_brand else 'Inactivo'
                brand['status_class'] = 'success' if is_active_brand else 'secondary'
                brand['status_icon'] = 'bi-check-circle' if is_active_brand else 'bi-pause-circle'
                
                # Mock catalog items count (will be replaced with real data later)
                brand['catalog_items_count'] = 0
            
            context['brands'] = brands
            
            # Pagination context
            total_pages = (total_count + self.paginate_by - 1) // self.paginate_by if total_count > 0 else 1
            
            context['pagination'] = {
                'count': total_count,
                'current_page': page,
                'total_pages': total_pages,
                'page_range': self._get_page_range(page, total_pages),
                'has_previous': page > 1,
                'has_next': page < total_pages,
                'start_index': (page - 1) * self.paginate_by + 1,
                'end_index': min(page * self.paginate_by, total_count),
            }
            
            # Filter context
            context['filters'] = {
                'search': search,
                'country': country_filter,
                'is_active': is_active,
            }
            
            # Get unique countries from brands for filter
            countries = sorted(set(b.get('country', '') for b in brands if b.get('country')))
            context['countries'] = countries
            
        except APIException as e:
            logger.error(f"Error loading OEM brands: {e}")
            messages.error(self.request, f"Error al cargar las marcas: {e.message}")
            context['brands'] = []
            context['pagination'] = self._get_empty_pagination()
            context['countries'] = []
            context['filters'] = {
                'search': search,
                'country': country_filter,
                'is_active': is_active,
            }
        
        return context
    
    def _get_status_class(self, status):
        """Get Bootstrap class for manufacturer status."""
        status_classes = {
            'ACTIVE': 'success',
            'INACTIVE': 'secondary',
            'PENDING': 'warning',
            'SUSPENDED': 'danger',
        }
        return status_classes.get(status, 'light')
    
    def _get_status_icon(self, status):
        """Get icon for manufacturer status."""
        status_icons = {
            'ACTIVE': 'bi-check-circle',
            'INACTIVE': 'bi-pause-circle',
            'PENDING': 'bi-clock',
            'SUSPENDED': 'bi-x-circle',
        }
        return status_icons.get(status, 'bi-circle')
    
    def _calculate_quality_score(self, manufacturer):
        """Calculate quality score based on various factors."""
        score = 50  # Base score
        
        # Status bonus
        if manufacturer.get('status') == 'ACTIVE':
            score += 20
        elif manufacturer.get('status') == 'PENDING':
            score += 10
        
        # Certification bonus
        cert_count = len(manufacturer.get('certification_list', []))
        score += min(cert_count * 10, 30)  # Max 30 points for certifications
        
        # Contact information bonus
        if manufacturer.get('contact_email'):
            score += 5
        if manufacturer.get('contact_phone'):
            score += 5
        if manufacturer.get('website'):
            score += 5
        
        return min(score, 100)  # Cap at 100
    
    def _get_quality_class(self, score):
        """Get Bootstrap class for quality score."""
        if score >= 80:
            return 'success'
        elif score >= 60:
            return 'info'
        elif score >= 40:
            return 'warning'
        else:
            return 'danger'
    
    def _calculate_dashboard_stats(self, manufacturers):
        """Calculate dashboard statistics from manufacturers."""
        total = len(manufacturers)
        if total == 0:
            return self._get_empty_stats()
        
        active_count = sum(1 for m in manufacturers if m.get('status') == 'ACTIVE')
        certified_count = sum(1 for m in manufacturers if m.get('certification_list'))
        avg_quality = sum(m.get('quality_score', 0) for m in manufacturers) / total
        total_parts = sum(m.get('parts_count', 0) for m in manufacturers)
        
        return {
            'total': total,
            'active': active_count,
            'certified': certified_count,
            'avg_quality': avg_quality,
            'total_parts': total_parts,
            'active_rate': (active_count / total * 100) if total > 0 else 0,
        }
    
    def _get_page_number(self):
        """Get and validate page number from request."""
        try:
            page = int(self.request.GET.get('page', 1))
            return max(1, page)
        except (ValueError, TypeError):
            return 1
    
    def _get_page_range(self, current_page, total_pages, window=5):
        """Generate a smart page range for pagination."""
        if total_pages <= window:
            return list(range(1, total_pages + 1))
        
        half_window = window // 2
        start = max(1, current_page - half_window)
        end = min(total_pages, current_page + half_window)
        
        if end - start < window - 1:
            if start == 1:
                end = min(total_pages, start + window - 1)
            else:
                start = max(1, end - window + 1)
        
        return list(range(start, end + 1))
    
    def _get_empty_pagination(self):
        """Get empty pagination context for error states."""
        return {
            'count': 0,
            'current_page': 1,
            'total_pages': 0,
            'page_range': [],
            'has_previous': False,
            'has_next': False,
            'start_index': 0,
            'end_index': 0,
        }
    
    def _get_empty_stats(self):
        """Get empty statistics for error states."""
        return {
            'total': 0,
            'active': 0,
            'certified': 0,
            'avg_quality': 0,
            'total_parts': 0,
            'active_rate': 0,
        }


class OEMPartCatalogView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """OEM parts catalog with cross-reference capabilities."""
    template_name = 'frontend/oem/part_catalog.html'
    login_url = 'frontend:login'
    paginate_by = 25
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get filter parameters
        search = self.request.GET.get('search', '').strip()
        manufacturer_filter = self.request.GET.get('manufacturer', '')
        category_filter = self.request.GET.get('category', '')
        page = self._get_page_number()
        
        # Get manufacturers from API for filter dropdown - OUTSIDE main try block for better error visibility
        manufacturers = []
        try:
            api_client = self.get_api_client()
            # Disable cache for manufacturers to ensure fresh data
            brands_response = api_client.get_oem_brands(page_size=100, is_active=True, use_cache=False)
            manufacturers = brands_response.get('results', [])
            
            # Process manufacturers for template safety
            for mfg in manufacturers:
                # Ensure display keys exist
                if 'oem_code' not in mfg:
                    mfg['oem_code'] = mfg.get('id') or mfg.get('brand_id') or ''
                if 'name' not in mfg:
                    mfg['name'] = mfg.get('brand_name') or mfg['oem_code'] or 'Sin nombre'
            
            logger.info(f"OEM Part Catalog: Loaded {len(manufacturers)} manufacturers from API")
            
            # If no results, try without filters
            if not manufacturers:
                logger.warning("No manufacturers found with is_active=True, trying without filter")
                brands_response = api_client.get_oem_brands(page_size=100)
                manufacturers = brands_response.get('results', [])
                # Process again
                for mfg in manufacturers:
                    if 'oem_code' not in mfg:
                        mfg['oem_code'] = mfg.get('id') or mfg.get('brand_id') or ''
                    if 'name' not in mfg:
                        mfg['name'] = mfg.get('brand_name') or mfg['oem_code'] or 'Sin nombre'
                logger.info(f"After retry: Loaded {len(manufacturers)} manufacturers")
                
        except APIException as api_err:
            logger.error(f"API Error loading manufacturers: {api_err.message}")
            manufacturers = []
        except Exception as mfg_error:
            logger.error(f"Error loading manufacturers: {type(mfg_error).__name__}: {mfg_error}")
            manufacturers = []
        
        context['manufacturers'] = manufacturers
        
        # Now process the main parts data
        try:
            # Build filters dictionary
            filters = {}
            if search:
                filters['search'] = search
            if manufacturer_filter:
                filters['oem_code'] = manufacturer_filter
            if category_filter:
                filters['group_code'] = category_filter
            # Note: availability filter is not supported by the API
            # The catalog items don't have an availability_status field
            # Removing this filter to prevent API errors
            
            # Get real parts data from API
            # Disable cache to ensure fresh data
            items_response = api_client.get_oem_catalog_items(
                page=page,
                page_size=self.paginate_by,
                use_cache=False,
                **filters
            )
            parts = items_response.get('results', [])
            
            # Process parts for enhanced display
            for part in parts:
                # Ensure catalog_id exists for template safety
                if 'catalog_id' not in part:
                    part['catalog_id'] = part.get('id') or 0
                
                # Ensure display keys exist
                if 'oem_code' not in part:
                    part['oem_code'] = part.get('oem_brand') or part.get('brand') or 'N/A'
                if 'description_es' not in part:
                    part['description_es'] = part.get('description') or part.get('name') or 'Sin descripción'
                if 'part_number' not in part:
                    part['part_number'] = part.get('number') or 'N/A'
                
                # Add availability styling
                availability = part.get('availability_status', '').upper()
                part['availability_class'] = self._get_availability_class(availability)
                part['availability_icon'] = self._get_availability_icon(availability)
                
                # Get cross_ref_count safely
                cross_ref_count = part.get('cross_ref_count', 0)
                part['cross_ref_count'] = cross_ref_count
                
                # Mock cross-references
                part['cross_references'] = [
                    {
                        'aftermarket_sku': f'AM-{part.get("catalog_id", 0):04d}',
                        'equivalence_type': 'DIRECT',
                        'confidence_score': 85 + (part.get('catalog_id', 0) % 15),
                        'confidence_class': 'success'
                    }
                ] if cross_ref_count > 0 else []
                
                # Ensure oem_code is displayed as name
                if part.get('oem_code') and not part.get('oem_code_name'):
                    part['oem_code_name'] = part.get('oem_code')
                
                # Calculate compatibility score
                part['compatibility_score'] = self._calculate_compatibility_score(part)
                part['compatibility_class'] = self._get_compatibility_class(part.get('compatibility_score', 0))
            
            context['parts'] = parts
            
            # Pagination context - use API count, not len(parts)
            total_count = items_response.get('count', len(parts))
            total_pages = (total_count + self.paginate_by - 1) // self.paginate_by if total_count > 0 else 1
            
            context['pagination'] = {
                'count': total_count,
                'current_page': page,
                'total_pages': total_pages,
                'page_range': self._get_page_range(page, total_pages),
                'has_previous': page > 1,
                'has_next': page < total_pages,
                'start_index': (page - 1) * self.paginate_by + 1,
                'end_index': min(page * self.paginate_by, total_count),
            }
            
            # Filter context
            context['filters'] = {
                'search': search,
                'manufacturer': manufacturer_filter,
                'category': category_filter,
            }
            
            # Also add oem_code for compatibility
            context['oem_code_filter'] = manufacturer_filter
            
            # Get category options from taxonomy groups
            from ...models import TaxonomyGroup
            try:
                categories = TaxonomyGroup.objects.filter(is_active=True).values('group_code', 'name_es')
                context['category_options'] = [
                    {'value': '', 'label': 'Todas las categorías'}
                ] + [
                    {'value': c['group_code'], 'label': c['name_es']} 
                    for c in categories
                ]
            except Exception:
                context['category_options'] = [
                    {'value': '', 'label': 'Todas las categorías'}
                ]
            
            # Calculate catalog statistics
            context['catalog_stats'] = self._calculate_catalog_stats(parts)
            
        except Exception as e:
            logger.error(f"Error loading OEM parts catalog: {type(e).__name__}: {e}")
            context['parts'] = []
            context['pagination'] = self._get_empty_pagination()
            context['catalog_stats'] = self._get_empty_catalog_stats()
            # Note: manufacturers is already set outside this try block
        
        return context
    
    def _get_availability_class(self, availability):
        """Get Bootstrap class for availability status."""
        availability_classes = {
            'IN_STOCK': 'success',
            'LOW_STOCK': 'warning',
            'OUT_OF_STOCK': 'danger',
            'DISCONTINUED': 'secondary',
            'ON_ORDER': 'info',
        }
        return availability_classes.get(availability, 'light')
    
    def _get_availability_icon(self, availability):
        """Get icon for availability status."""
        availability_icons = {
            'IN_STOCK': 'bi-check-circle',
            'LOW_STOCK': 'bi-exclamation-triangle',
            'OUT_OF_STOCK': 'bi-x-circle',
            'DISCONTINUED': 'bi-archive',
            'ON_ORDER': 'bi-clock',
        }
        return availability_icons.get(availability, 'bi-circle')
    
    def _calculate_compatibility_score(self, part):
        """Calculate compatibility score based on cross-references and specifications."""
        score = 50  # Base score
        
        # Cross-reference bonus
        cross_ref_count = part.get('cross_ref_count', 0)
        score += min(cross_ref_count * 5, 25)  # Max 25 points for cross-refs
        
        # Availability bonus
        if part.get('availability_status') == 'IN_STOCK':
            score += 15
        elif part.get('availability_status') == 'LOW_STOCK':
            score += 10
        
        # Specification completeness bonus
        if part.get('weight_kg'):
            score += 5
        if part.get('dimensions'):
            score += 5
        
        return min(score, 100)  # Cap at 100
    
    def _get_compatibility_class(self, score):
        """Get Bootstrap class for compatibility score."""
        if score >= 80:
            return 'success'
        elif score >= 60:
            return 'info'
        elif score >= 40:
            return 'warning'
        else:
            return 'danger'
    
    def _calculate_catalog_stats(self, parts):
        """Calculate catalog statistics from parts."""
        total = len(parts)
        if total == 0:
            return self._get_empty_catalog_stats()
        
        in_stock = sum(1 for p in parts if p.get('availability_status') == 'IN_STOCK')
        with_cross_refs = sum(1 for p in parts if p.get('cross_ref_count', 0) > 0)
        avg_compatibility = sum(p.get('compatibility_score', 0) for p in parts) / total
        total_cross_refs = sum(p.get('cross_ref_count', 0) for p in parts)
        
        return {
            'total': total,
            'in_stock': in_stock,
            'with_cross_refs': with_cross_refs,
            'avg_compatibility': avg_compatibility,
            'total_cross_refs': total_cross_refs,
            'availability_rate': (in_stock / total * 100) if total > 0 else 0,
        }
    
    def _get_page_number(self):
        """Get and validate page number from request."""
        try:
            page = int(self.request.GET.get('page', 1))
            return max(1, page)
        except (ValueError, TypeError):
            return 1
    
    def _get_page_range(self, current_page, total_pages, window=5):
        """Generate a smart page range for pagination."""
        if total_pages <= window:
            return list(range(1, total_pages + 1))
        
        half_window = window // 2
        start = max(1, current_page - half_window)
        end = min(total_pages, current_page + half_window)
        
        if end - start < window - 1:
            if start == 1:
                end = min(total_pages, start + window - 1)
            else:
                start = max(1, end - window + 1)
        
        return list(range(start, end + 1))
    
    def _get_empty_pagination(self):
        """Get empty pagination context for error states."""
        return {
            'count': 0,
            'current_page': 1,
            'total_pages': 0,
            'page_range': [],
            'has_previous': False,
            'has_next': False,
            'start_index': 0,
            'end_index': 0,
        }
    
    def _get_empty_catalog_stats(self):
        """Get empty catalog statistics for error states."""
        return {
            'total': 0,
            'in_stock': 0,
            'with_cross_refs': 0,
            'avg_compatibility': 0,
            'total_cross_refs': 0,
            'availability_rate': 0,
        }


class CrossReferenceToolView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """Interactive cross-reference tool for parts lookup.
    Integrates with OEMEquivalence API for real cross-reference data.
    """
    template_name = 'frontend/oem/cross_reference_tool.html'
    login_url = 'frontend:login'
    
    EQUIVALENCE_API_URL = 'http://localhost:8000/api/oem/equivalences/'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get search parameters
        part_number = self.request.GET.get('part_number', '').strip()
        search_type = self.request.GET.get('search_type', 'oem')  # oem or aftermarket
        
        context['search_params'] = {
            'part_number': part_number,
            'search_type': search_type,
        }
        
        if part_number:
            try:
                # Get real search results from API
                if search_type == 'oem':
                    # Search OEM catalog items
                    items_response = self._search_oem_parts(part_number)
                    oem_parts = items_response.get('results', [])
                    
                    # Search cross-references (using equivalence endpoint)
                    cross_references = self._search_equivalences(part_number, 'oem')
                    
                    context['search_results'] = {
                        'oem_parts': oem_parts,
                        'cross_references': cross_references,
                        'total_matches': len(oem_parts) + len(cross_references)
                    }
                
                else:  # aftermarket search
                    # Search by aftermarket SKU (using equivalence endpoint)
                    cross_references = self._search_equivalences(part_number, 'aftermarket')
                    
                    # Also search OEM parts
                    oem_parts = []
                    if cross_references:
                        oem_parts = self._search_oem_parts_by_equivalences(cross_references)
                    
                    context['search_results'] = {
                        'oem_parts': oem_parts,
                        'cross_references': cross_references,
                        'total_matches': len(cross_references)
                    }
                
                # Process results for enhanced display
                self._process_search_results(context['search_results'])
                
            except Exception as e:
                logger.error(f"Error in cross-reference search: {e}")
                context['search_results'] = {
                    'oem_parts': [],
                    'cross_references': [],
                    'total_matches': 0
                }
                context['error'] = str(e)
        else:
            context['search_results'] = None
        
        # Get popular parts from API
        try:
            popular_response = self._search_oem_parts('', limit=10)
            context['popular_parts'] = popular_response.get('results', [])[:5]
        except Exception as e:
            logger.warning(f"Could not load popular parts: {e}")
            context['popular_parts'] = []
        
        return context
    
    def _search_oem_parts(self, part_number, limit=20):
        """Search OEM parts from catalog."""
        try:
            api_client = self.get_api_client()
            return api_client.get_oem_catalog_items(
                search=part_number,
                page_size=limit
            )
        except Exception as e:
            logger.warning(f"Could not search OEM parts: {e}")
            return {'results': []}
    
    def _search_equivalences(self, part_number, search_type):
        """Search equivalences from OEMEquivalence API."""
        try:
            import requests
            
            params = {}
            if search_type == 'oem':
                params['oem_part'] = part_number
            else:
                params['aftermarket'] = part_number
            
            response = requests.get(
                self.EQUIVALENCE_API_URL,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('results', [])
            return []
        except Exception as e:
            logger.warning(f"Could not search equivalences: {e}")
            return []
    
    def _search_oem_parts_by_equivalences(self, equivalences):
        """Get OEM parts from equivalence data."""
        oem_parts = []
        for eq in equivalences:
            if eq.get('oem_part_number'):
                oem_parts.append({
                    'part_number': eq.get('oem_part_number'),
                    'oem_code': {'name': eq.get('oem_brand_name', 'N/A')},
                    'description_es': eq.get('notes', ''),
                    'availability_status': 'UNKNOWN',
                    'formatted_price': 'Consultar'
                })
        return oem_parts
    
    def _process_search_results(self, results):
        """Process search results for enhanced display."""
        # Process OEM parts
        for part in results.get('oem_parts', []):
            availability = part.get('availability_status', '').upper()
            part['availability_class'] = self._get_availability_class(availability)
            part['availability_icon'] = self._get_availability_icon(availability)
            
            if part.get('list_price'):
                part['formatted_price'] = f"${part['list_price']:.2f}"
            else:
                part['formatted_price'] = 'Consultar'
        
        # Process cross-references
        for cross_ref in results.get('cross_references', []):
            confidence = cross_ref.get('confidence_score', 0)
            cross_ref['confidence_class'] = self._get_confidence_class(confidence)
            cross_ref['confidence_icon'] = self._get_confidence_icon(confidence)
            cross_ref['confidence_percent'] = f"{confidence}%"
    
    def _get_availability_class(self, availability):
        """Get Bootstrap class for availability status."""
        availability_classes = {
            'IN_STOCK': 'success',
            'LOW_STOCK': 'warning',
            'OUT_OF_STOCK': 'danger',
            'DISCONTINUED': 'secondary',
            'ON_ORDER': 'info',
        }
        return availability_classes.get(availability, 'light')
    
    def _get_availability_icon(self, availability):
        """Get icon for availability status."""
        availability_icons = {
            'IN_STOCK': 'bi-check-circle',
            'LOW_STOCK': 'bi-exclamation-triangle',
            'OUT_OF_STOCK': 'bi-x-circle',
            'DISCONTINUED': 'bi-archive',
            'ON_ORDER': 'bi-clock',
        }
        return availability_icons.get(availability, 'bi-circle')
    
    def _get_confidence_class(self, confidence):
        """Get Bootstrap class for confidence level."""
        if confidence >= 90:
            return 'success'
        elif confidence >= 70:
            return 'info'
        elif confidence >= 50:
            return 'warning'
        else:
            return 'danger'
    
    def _get_confidence_icon(self, confidence):
        """Get icon for confidence level."""
        if confidence >= 90:
            return 'bi-shield-check'
        elif confidence >= 70:
            return 'bi-shield'
        elif confidence >= 50:
            return 'bi-shield-exclamation'
        else:
            return 'bi-shield-x'


# Legacy views for compatibility - ELIMINADAS VISTAS REDUNDANTES
# Las siguientes vistas legacy fueron consolidadas:
# - OEMCatalogSearchView -> Usar CrossReferenceToolView
# - OEMBrandManagementView -> Usar OEMManufacturerManagementView
# - OEMEquivalenceView -> Usar views de oem_ui_views.py
# - OEMPartComparatorView -> Consolidado en equivalencias

class OEMModelListAPIView(LoginRequiredMixin, APIClientMixin, View):
    """
    API interna para obtener modelos OEM (OEMCatalogItem) filtrados por marca.
    Usada por el formulario de equipos para el combo Modelo.
    """
    login_url = 'frontend:login'

    def get(self, request, *args, **kwargs):
        oem_code = request.GET.get('oem_code') or ''
        item_type = request.GET.get('item_type') or 'VEHICLE_MODEL'
        page_size = request.GET.get('page_size') or '1000'

        if not oem_code:
            return JsonResponse(
                {'detail': 'Parámetro oem_code es requerido'},
                status=400
            )

        try:
            api_client = self.get_api_client()
            data = api_client.get_oem_catalog_items(
                page_size=int(page_size),
                oem_code=oem_code,
                item_type=item_type,
                is_active=True,
                is_discontinued=False,
            )
            return JsonResponse(data, safe=False)
        except APIException as e:
            logger.error(f"Error loading OEM models from API: {e}")
            status = e.status_code or 500
            return JsonResponse(
                {'detail': e.message or 'Error al cargar modelos OEM'},
                status=status
            )
        except Exception as e:
            logger.error(f"Unexpected error loading OEM models: {e}")
            return JsonResponse(
                {'detail': 'Error inesperado al cargar modelos OEM'},
                status=500
            )
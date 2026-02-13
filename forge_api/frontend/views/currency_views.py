"""
Currency Views - Frontend CRUD Operations
ForgeDB Frontend Web Application

This module implements complete CRUD operations for Currencies
with Django Class-Based Views, form validation, and API integration.

Performance Optimizations:
- Django cache framework with intelligent invalidation
- Concurrent.futures for parallel data loading
- Optimized AJAX search with debouncing support
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView, TemplateView, View
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, Http404
from django.core.paginator import Paginator
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import logging
import time

from ..services.api_client import ForgeAPIClient, APIException
from ..forms.currency_forms import CurrencyForm, CurrencySearchForm
from ..mixins import APIClientMixin

logger = logging.getLogger(__name__)


class CurrencyListView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """
    Lista de monedas con búsqueda y filtros
    
    Performance: Uses Django cache for faster repeated loads
    """
    template_name = 'frontend/catalog/currency_list.html'
    context_object_name = 'currencies'
    
    def get_context_data(self, **kwargs):
        """Agregar contexto adicional para la vista"""
        context = super().get_context_data(**kwargs)
        
        # Parámetros de búsqueda y filtrado
        search = self.request.GET.get('search', '').strip()
        is_active = self.request.GET.get('is_active', '').strip()
        
        try:
            api_client = self.get_api_client()
            
            # Parámetros para la API
            params = {}
            if search:
                params['search'] = search
            if is_active:
                params['is_active'] = is_active
            
            # Generar clave de caché
            cache_key = self._get_currencies_cache_key(params)
            currencies = cache.get(cache_key)
            
            if currencies is None:
                # Cache miss - fetch from API
                start_time = time.time()
                response = api_client.get_currencies(**params)
                fetch_time = time.time() - start_time
                logger.debug(f"Currencies API fetch: {fetch_time:.3f}s")
                
                if response and 'results' in response:
                    currencies = response['results']
                else:
                    currencies = []
                
                # Cache por 5 minutos (300 segundos)
                cache.set(cache_key, currencies, 300)
            else:
                logger.debug(f"Currencies cache hit: {cache_key}")
            
            # Procesar monedas para display
            for currency in currencies:
                # Formatear tipo de cambio (convertir a float si viene como string)
                exchange_rate_raw = currency.get('exchange_rate', '1.0')
                try:
                    exchange_rate = float(exchange_rate_raw)
                except (ValueError, TypeError):
                    exchange_rate = 1.0
                currency['exchange_rate_formatted'] = f"{exchange_rate:.4f}"
                
                # Determinar si es moneda base (exchange_rate == 1.0)
                currency['is_base_currency'] = (exchange_rate == 1.0)
                
                # Estado
                if currency.get('is_active'):
                    currency['status_class'] = 'success'
                    currency['status_label'] = 'Activa'
                else:
                    currency['status_class'] = 'secondary'
                    currency['status_label'] = 'Inactiva'
            
            context['currencies'] = currencies
            context['total_count'] = len(currencies)
            
            # Moneda base
            base_currency = next((c for c in currencies if c.get('is_base_currency')), None)
            context['base_currency'] = base_currency
            
            # Cache metadata
            context['cache_hit'] = currencies is not None
            
        except APIException as e:
            logger.error(f"API error loading currencies: {str(e)}")
            self.handle_api_error(e, "Error al cargar las monedas.")
            context['currencies'] = []
            context['total_count'] = 0
            context['base_currency'] = None
            context['cache_hit'] = False
        except Exception as e:
            logger.error(f"Unexpected error loading currencies: {str(e)}")
            messages.error(self.request, "Error de conexión con el servidor.")
            context['currencies'] = []
            context['total_count'] = 0
            context['base_currency'] = None
            context['cache_hit'] = False
        
        # Formulario de búsqueda
        context['search_form'] = CurrencySearchForm(self.request.GET)
        context['current_search'] = search
        context['current_is_active'] = is_active
        
        return context
    
    def _get_currencies_cache_key(self, params: dict) -> str:
        """Generate cache key for currencies list."""
        key_parts = ['forge_api', 'currencies', 'list']
        if params:
            sorted_params = sorted(params.items())
            params_str = '_'.join([f"{k}_{v}" for k, v in sorted_params])
            key_parts.append(params_str)
        return ':'.join(key_parts)
    
    @staticmethod
    def invalidate_currencies_cache():
        """Invalidate all currencies cache entries."""
        try:
            # Eliminar claves de caché relacionadas con monedas
            cache.delete('forge_api:currencies:list')
            cache.delete('forge_api:currencies:list_')
            logger.info("Currencies cache invalidated")
        except Exception as e:
            logger.warning(f"Failed to invalidate currencies cache: {e}")


class CurrencyCreateView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """
    Vista para crear nuevas monedas
    """
    template_name = 'frontend/catalog/currency_form.html'
    
    def get_context_data(self, **kwargs):
        """Agregar contexto para la vista de creación"""
        context = super().get_context_data(**kwargs)
        context['title'] = 'Crear Moneda'
        context['submit_text'] = 'Crear Moneda'
        context['cancel_url'] = reverse('frontend:currency_list')
        context['is_edit'] = False
        
        # Agregar formulario al contexto
        if self.request.method == 'POST':
            context['form'] = CurrencyForm(self.request.POST)
        else:
            context['form'] = CurrencyForm()
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Manejar solicitud POST para crear moneda"""
        form = CurrencyForm(request.POST)
        
        if form.is_valid():
            try:
                api_client = self.get_api_client()
                
                # Preparar datos para la API
                data = {
                    'currency_code': form.cleaned_data['currency_code'].upper(),
                    'name': form.cleaned_data['name'],
                    'symbol': form.cleaned_data.get('symbol', ''),
                    'exchange_rate': float(form.cleaned_data['exchange_rate']),
                    'decimals': int(form.cleaned_data['decimals']),
                    'is_active': form.cleaned_data.get('is_active', True)
                }
                
                # Enviar a la API
                response = api_client.create_currency(data)
                
                if response:
                    # Invalidar caché de monedas
                    CurrencyListView.invalidate_currencies_cache()
                    
                    messages.success(
                        request, 
                        f"Moneda '{data['name']}' ({data['currency_code']}) creada exitosamente."
                    )
                    return redirect('frontend:currency_list')
                else:
                    messages.error(
                        request, 
                        "Error al crear la moneda. Verifica los datos ingresados."
                    )
                    
            except APIException as e:
                logger.error(f"API error creating currency: {str(e)}")
                self.handle_api_error(e, "Error al crear la moneda.")
            except Exception as e:
                logger.error(f"Unexpected error creating currency: {str(e)}")
                messages.error(
                    request, 
                    "Error de conexión con el servidor. Intenta nuevamente."
                )
        else:
            messages.error(
                request, 
                "Por favor corrige los errores en el formulario."
            )
        
        # Si hay errores, volver a mostrar el formulario con los datos
        context = self.get_context_data(**kwargs)
        context['form'] = form
        return self.render_to_response(context)


class CurrencyUpdateView(LoginRequiredMixin, APIClientMixin, TemplateView):
    """
    Vista para editar monedas existentes
    """
    template_name = 'frontend/catalog/currency_form.html'
    
    def get_currency(self):
        """Obtener el objeto desde la API"""
        try:
            api_client = self.get_api_client()
            currency_code = self.kwargs.get('pk')
            
            response = api_client.get_currency(currency_code)
            
            if response:
                return response
            else:
                raise Http404("Moneda no encontrada")
                
        except APIException as e:
            logger.error(f"API error loading currency {self.kwargs.get('pk')}: {str(e)}")
            if e.status_code == 404:
                raise Http404("Moneda no encontrada")
            raise Http404("Error al cargar la moneda")
        except Exception as e:
            logger.error(f"Unexpected error loading currency {self.kwargs.get('pk')}: {str(e)}")
            raise Http404("Error al cargar la moneda")
    
    def get_context_data(self, **kwargs):
        """Agregar contexto para la vista de edición"""
        context = super().get_context_data(**kwargs)
        obj = self.get_currency()
        context['title'] = f'Editar Moneda: {obj.get("name", "")} ({obj.get("currency_code", "")})'
        context['submit_text'] = 'Actualizar Moneda'
        context['cancel_url'] = reverse('frontend:currency_list')
        context['object'] = obj
        context['is_edit'] = True
        
        # Agregar formulario al contexto
        if self.request.method == 'POST':
            context['form'] = CurrencyForm(self.request.POST, instance_code=obj.get('currency_code'))
        else:
            # Pre-poblar formulario con datos existentes
            initial_data = {
                'currency_code': obj.get('currency_code', ''),
                'name': obj.get('name', ''),
                'symbol': obj.get('symbol', ''),
                'exchange_rate': obj.get('exchange_rate', 1.0),
                'decimals': obj.get('decimals', 2),
                'is_active': obj.get('is_active', True)
            }
            context['form'] = CurrencyForm(initial=initial_data, instance_code=obj.get('currency_code'))
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Manejar solicitud POST para actualizar moneda"""
        obj = self.get_currency()
        form = CurrencyForm(request.POST, instance_code=obj.get('currency_code'))
        
        if form.is_valid():
            try:
                api_client = self.get_api_client()
                original_code = self.kwargs.get('pk')
                
                # Si el código viene vacío del formulario, usar el código original
                new_code_from_form = form.cleaned_data.get('currency_code', '').strip().upper()
                if not new_code_from_form:
                    new_code_from_form = original_code.upper()
                
                # Log para depuración
                logger.debug(f"Updating currency: original_code={original_code}, new_code={new_code_from_form}")
                
                # Invalidar caché de monedas antes de la actualización
                # Esto asegura que no estamos usando datos obsoletos
                CurrencyListView.invalidate_currencies_cache()
                
                # Preparar datos para la API
                # Si el código no cambió, usar el código original
                currency_code_for_url = original_code
                if new_code_from_form != original_code.upper():
                    # El código cambió, incluir el nuevo código en los datos
                    currency_code_for_url = new_code_from_form
                
                data = {
                    'currency_code': new_code_from_form,
                    'name': form.cleaned_data['name'],
                    'symbol': form.cleaned_data.get('symbol', ''),
                    'exchange_rate': float(form.cleaned_data['exchange_rate']),
                    'decimals': int(form.cleaned_data['decimals']),
                    'is_active': form.cleaned_data.get('is_active', True)
                }
                
                # Log para depuración
                logger.debug(f"Sending PUT to: currencies/{currency_code_for_url}/ with data: {data}")
                
                # Enviar actualización a la API
                # Usar el código original para la URL, el nuevo código va en los datos
                response = api_client.update_currency(original_code, data)
                
                logger.debug(f"API response: {response}")
                
                if response:
                    # Invalidar caché de monedas después de la actualización
                    CurrencyListView.invalidate_currencies_cache()
                    
                    # Forzar obtención de datos actualizados sin caché
                    # Esto asegura que los datos más recientes se muestren
                    try:
                        # Obtener la moneda actualizada directamente de la API sin caché
                        api_client_with_no_cache = ForgeAPIClient(request=request)
                        updated_currency = api_client_with_no_cache.get_currency(original_code, use_cache=False)
                        if updated_currency:
                            logger.debug(f"Updated currency data fetched: {updated_currency}")
                    except Exception as cache_err:
                        logger.debug(f"Could not fetch updated currency data: {cache_err}")
                    
                    # Verificar si el código cambió
                    final_new_code = data['currency_code'].upper()
                    if final_new_code != original_code.upper():
                        messages.success(
                            request, 
                            f"Moneda '{data['name']}' actualizada exitosamente. Código cambiado de '{original_code}' a '{final_new_code}'."
                        )
                    else:
                        messages.success(
                            request, 
                            f"Moneda '{data['name']}' actualizada exitosamente."
                        )
                    
                    # Si el código cambió, redirigir a la página de edición del nuevo código
                    if final_new_code != original_code.upper():
                        return redirect('frontend:currency_edit', pk=final_new_code)
                    else:
                        return redirect('frontend:currency_list')
                else:
                    logger.error(f"Empty response from API when updating currency {original_code}")
                    messages.error(
                        request, 
                        "Error al actualizar la moneda. La API no devolvió una respuesta válida."
                    )
                    
            except APIException as e:
                logger.error(f"API error updating currency {self.kwargs.get('pk')}: {str(e)}")
                # Mostrar mensaje de error específico
                error_msg = str(e.message) if hasattr(e, 'message') else str(e)
                if hasattr(e, 'response_data') and e.response_data:
                    # Si es un error de validación, mostrar los detalles
                    if isinstance(e.response_data, dict):
                        detail_msgs = []
                        for field, errors in e.response_data.items():
                            if isinstance(errors, list):
                                for err in errors:
                                    detail_msgs.append(f"{field}: {err}")
                            else:
                                detail_msgs.append(f"{field}: {errors}")
                        if detail_msgs:
                            error_msg = "; ".join(detail_msgs)
                messages.error(request, f"Error al actualizar la moneda: {error_msg}")
            except Exception as e:
                logger.error(f"Unexpected error updating currency {self.kwargs.get('pk')}: {str(e)}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                messages.error(
                    request, 
                    f"Error de conexión con el servidor: {str(e)}"
                )
        else:
            # Mostrar errores del formulario
            logger.debug(f"Form errors: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
        
        # Si hay errores, volver a mostrar el formulario con los datos
        context = self.get_context_data(**kwargs)
        context['form'] = form
        return self.render_to_response(context)


class CurrencyDetailView(LoginRequiredMixin, APIClientMixin, DetailView):
    """
    Vista detallada de una moneda
    """
    template_name = 'frontend/catalog/currency_detail.html'
    context_object_name = 'currency'
    
    def get_object(self, queryset=None):
        """Obtener el objeto desde la API"""
        try:
            api_client = self.get_api_client()
            currency_code = self.kwargs.get('pk')
            
            response = api_client.get_currency(currency_code)
            
            if response:
                return response
            else:
                raise Http404("Moneda no encontrada")
                
        except APIException as e:
            logger.error(f"API error loading currency {self.kwargs.get('pk')}: {str(e)}")
            if e.status_code == 404:
                raise Http404("Moneda no encontrada")
            raise Http404("Error al cargar la moneda")
        except Exception as e:
            logger.error(f"Unexpected error loading currency {self.kwargs.get('pk')}: {str(e)}")
            raise Http404("Error al cargar la moneda")
    
    def get_context_data(self, **kwargs):
        """Agregar contexto adicional"""
        context = super().get_context_data(**kwargs)
        obj = self.get_object()
        
        context['title'] = f'Detalle: {obj.get("name", "")} ({obj.get("currency_code", "")})'
        context['can_edit'] = True
        context['can_delete'] = True
        
        # Formatear datos para display
        exchange_rate_raw = obj.get('exchange_rate', 1.0)
        try:
            exchange_rate = float(exchange_rate_raw)
        except (ValueError, TypeError):
            exchange_rate = 1.0
        context['exchange_rate_formatted'] = f"{exchange_rate:.4f}"
        context['is_base_currency'] = (exchange_rate == 1.0)
        
        # URLs para acciones
        context['edit_url'] = reverse('frontend:currency_edit', kwargs={'pk': obj.get('currency_code')})
        context['delete_url'] = reverse('frontend:currency_delete', kwargs={'pk': obj.get('currency_code')})
        context['list_url'] = reverse('frontend:currency_list')
        
        return context


class CurrencyDeleteView(LoginRequiredMixin, APIClientMixin, DeleteView):
    """
    Vista para eliminar monedas con verificación de dependencias
    """
    template_name = 'frontend/catalog/currency_confirm_delete.html'
    success_url = reverse_lazy('frontend:currency_list')
    
    def get_object(self, queryset=None):
        """Obtener el objeto desde la API"""
        try:
            api_client = self.get_api_client()
            currency_code = self.kwargs.get('pk')
            
            response = api_client.get_currency(currency_code)
            
            if response:
                return response
            else:
                raise Http404("Moneda no encontrada")
                
        except APIException as e:
            logger.error(f"API error loading currency {self.kwargs.get('pk')}: {str(e)}")
            if e.status_code == 404:
                raise Http404("Moneda no encontrada")
            raise Http404("Error al cargar la moneda")
        except Exception as e:
            logger.error(f"Unexpected error loading currency {self.kwargs.get('pk')}: {str(e)}")
            raise Http404("Error al cargar la moneda")
    
    def get_context_data(self, **kwargs):
        """Agregar contexto para confirmación de eliminación"""
        context = super().get_context_data(**kwargs)
        obj = self.get_object()
        
        context['title'] = f'Eliminar Moneda: {obj.get("name", "")} ({obj.get("currency_code", "")})'
        context['object'] = obj
        context['cancel_url'] = reverse('frontend:currency_list')
        
        # Verificar dependencias (esto se puede expandir según las relaciones)
        context['has_dependencies'] = False
        context['dependencies'] = []
        
        # Aquí se pueden agregar verificaciones de dependencias
        # Por ejemplo, verificar si hay productos o facturas usando esta moneda
        
        return context
    
    def delete(self, request, *args, **kwargs):
        """Procesar eliminación"""
        try:
            api_client = self.get_api_client()
            currency_code = self.kwargs.get('pk')
            obj = self.get_object()
            
            # Verificar dependencias antes de eliminar
            # (Esto se puede implementar con llamadas adicionales a la API)
            
            # Intentar eliminar
            response = api_client.delete_currency(currency_code)
            
            if response is not False:  # La API puede retornar None para DELETE exitoso
                # Invalidar caché de monedas
                CurrencyListView.invalidate_currencies_cache()
                
                messages.success(
                    request, 
                    f"Moneda '{obj.get('name', '')}' ({obj.get('currency_code', '')}) eliminada exitosamente."
                )
                return redirect(self.success_url)
            else:
                messages.error(
                    request, 
                    "No se puede eliminar la moneda. Puede estar en uso."
                )
                return redirect('frontend:currency_detail', pk=currency_code)
                
        except APIException as e:
            logger.error(f"API error deleting currency {self.kwargs.get('pk')}: {str(e)}")
            self.handle_api_error(e, "Error al eliminar la moneda.")
            return redirect('frontend:currency_detail', pk=self.kwargs.get('pk'))
        except Exception as e:
            logger.error(f"Unexpected error deleting currency {self.kwargs.get('pk')}: {str(e)}")
            messages.error(
                request, 
                "Error al eliminar la moneda. Intenta nuevamente."
            )
            return redirect('frontend:currency_detail', pk=self.kwargs.get('pk'))


# =============================================================================
# AJAX Views para funcionalidad dinámica
# =============================================================================

@method_decorator(csrf_exempt, name='dispatch')
class CurrencyAjaxSearchView(LoginRequiredMixin, APIClientMixin, View):
    """
    Vista AJAX para búsqueda dinámica de monedas
    
    Performance: Optimized with caching and reduced payload
    """
    
    def get(self, request):
        """Búsqueda AJAX con caché"""
        try:
            api_client = self.get_api_client()
            
            # Parámetros de búsqueda
            search = request.GET.get('q', '').strip()
            limit = int(request.GET.get('limit', 10))
            
            # Generar clave de caché para búsqueda
            cache_key = f"forge_api:currencies:search:{search}:{limit}"
            cached_result = cache.get(cache_key)
            
            if cached_result is not None:
                logger.debug(f"Currency search cache hit: {search}")
                return JsonResponse(cached_result)
            
            params = {
                'search': search,
                'page_size': limit
            }
            
            # Llamada a la API
            response = api_client.get_currencies(**params)
            
            if response and 'results' in response:
                results = []
                for item in response['results']:
                    results.append({
                        'id': item['currency_code'],
                        'text': f"{item['name']} ({item['currency_code']})",
                        'code': item['currency_code'],
                        'symbol': item.get('symbol', ''),
                        'is_active': item.get('is_active', True),
                        'exchange_rate': item.get('exchange_rate', 1.0)
                    })
                
                result_data = {
                    'success': True,
                    'results': results,
                    'total': response.get('count', 0),
                    'cache_hit': False
                }
                
                # Cache por 2 minutos para búsquedas
                cache.set(cache_key, result_data, 120)
                
                return JsonResponse(result_data)
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Error al buscar monedas'
                })
                
        except APIException as e:
            logger.error(f"API error in AJAX search: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Error de conexión con el servidor'
            })
        except Exception as e:
            logger.error(f"Unexpected error in AJAX search: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Error de conexión con el servidor'
            })


def currency_check_code(request):
    """
    Vista AJAX para verificar unicidad de código
    
    Performance: Added timeout para evitar bloqueos
    """
    if request.method == 'GET':
        try:
            api_client = ForgeAPIClient(request=request)
            code = request.GET.get('code', '').strip().upper()
            exclude_code = request.GET.get('exclude_code', '')
            
            if not code:
                return JsonResponse({'available': True})
            
            if len(code) != 3:
                return JsonResponse({
                    'available': False,
                    'message': 'El código debe tener exactamente 3 caracteres'
                })
            
            # Buscar código existente con timeout
            try:
                # Usar timeout de 5 segundos para la verificación
                import signal
                
                def timeout_handler(signum, frame):
                    raise TimeoutError("Timeout verificando código")
                
                # Configurar timeout solo en Unix
                if hasattr(signal, 'SIGALRM'):
                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(5)  # 5 segundos timeout
                
                existing = api_client.get_currency(code)
                
                # Cancelar timeout
                if hasattr(signal, 'SIGALRM'):
                    signal.alarm(0)
                
                # Si estamos editando, excluir el código actual
                if exclude_code and code == exclude_code:
                    return JsonResponse({'available': True})
                return JsonResponse({
                    'available': False,
                    'message': f'El código {code} ya está en uso'
                })
            except APIException as e:
                if e.status_code == 404:
                    return JsonResponse({'available': True})
                # Error de API, permitir continuar
                logger.warning(f"API error checking code {code}: {e.message}")
                return JsonResponse({'available': True, 'error': None})
            except TimeoutError:
                logger.warning(f"Timeout checking code {code}")
                return JsonResponse({'available': True, 'error': None})
            except Exception as e:
                logger.warning(f"Error checking code {code}: {str(e)}")
                return JsonResponse({'available': True, 'error': None})
                
        except Exception as e:
            logger.error(f"Error checking code availability: {str(e)}")
            return JsonResponse({
                'available': True,  # En caso de error, permitir continuar
                'error': 'Error al verificar disponibilidad'
            })
    
    return JsonResponse({'available': True})

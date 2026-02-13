"""
Exchange Rate Service
ForgeDB Frontend Web Application

Servicio para gestión de tasas de cambio, actualización automática
y validaciones avanzadas.
"""

import requests
import logging
from decimal import Decimal
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class ExchangeRateService:
    """
    Servicio para gestión de tasas de cambio
    """
    
    # APIs externas disponibles
    EXTERNAL_APIS = {
        'exchangerate-api': {
            'url': 'https://api.exchangerate-api.com/v4/latest/{base}',
            'free': True,
            'requires_key': False
        },
        'fixer': {
            'url': 'http://data.fixer.io/api/latest',
            'free': False,
            'requires_key': True
        }
    }
    
    # Rangos razonables por moneda (min, max)
    REASONABLE_RANGES = {
        'USD': (0.5, 2.0),      # Respecto a moneda base
        'EUR': (0.5, 2.0),
        'GBP': (0.5, 2.0),
        'JPY': (50.0, 200.0),
        'MXN': (10.0, 30.0),
        'CAD': (0.5, 2.0),
        'AUD': (0.5, 2.0),
        'CHF': (0.5, 2.0),
        'CNY': (3.0, 10.0),
        'DEFAULT': (0.0001, 10000.0)
    }
    
    def __init__(self, api_client=None):
        """
        Inicializar servicio
        
        Args:
            api_client: Cliente API de ForgeDB
        """
        self.api_client = api_client
    
    def get_current_rates(self):
        """
        Obtener tasas actuales de todas las monedas
        
        Returns:
            list: Lista de monedas con sus tasas
        """
        try:
            if not self.api_client:
                logger.error("API client not initialized")
                return []
            
            # Llamar a la API sin filtros (igual que CurrencyListView)
            response = self.api_client.get_currencies()
            
            if response and 'results' in response:
                currencies = response['results']
                
                # Enriquecer con información adicional
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
                    
                    # Agregar información de última actualización
                    # (esto vendría del backend en una implementación completa)
                    currency['last_updated'] = timezone.now()
                    currency['source'] = 'manual'
                    
                    # Estado
                    if currency.get('is_active'):
                        currency['status_class'] = 'success'
                        currency['status_label'] = 'Activa'
                    else:
                        currency['status_class'] = 'secondary'
                        currency['status_label'] = 'Inactiva'
                
                return currencies
            
            logger.warning(f"API response does not contain 'results': {response}")
            return []
            
        except Exception as e:
            logger.error(f"Error getting current rates: {str(e)}", exc_info=True)
            return []
    
    def update_rate_manual(self, currency_code, rate, source='manual', user=None):
        """
        Actualizar tasa manualmente
        
        Args:
            currency_code: Código de moneda
            rate: Nueva tasa
            source: Fuente de la tasa
            user: Usuario que realiza el cambio
            
        Returns:
            dict: Respuesta de la API o None si hay error
        """
        try:
            if not self.api_client:
                logger.error("API client not initialized")
                return None
            
            # Validar tasa
            if not self.validate_rate(currency_code, rate):
                logger.warning(f"Rate {rate} for {currency_code} is outside reasonable range")
                # Continuar de todos modos, pero registrar advertencia
            
            # Preparar datos
            data = {
                'exchange_rate': float(rate),
                # En una implementación completa, también se enviaría:
                # 'rate_source': source,
                # 'updated_by': user.id if user else None,
                # 'updated_at': timezone.now().isoformat()
            }
            
            # Actualizar en el backend
            response = self.api_client.update_currency(currency_code, data)
            
            if response:
                logger.info(f"Rate updated for {currency_code}: {rate} (source: {source})")
                return response
            
            return None
            
        except Exception as e:
            logger.error(f"Error updating rate for {currency_code}: {str(e)}")
            return None
    
    def update_rates_automatic(self, base_currency='USD', source='exchangerate-api'):
        """
        Actualizar todas las tasas desde fuente externa
        
        Args:
            base_currency: Moneda base para obtener tasas
            source: Fuente de tasas ('exchangerate-api', 'fixer')
            
        Returns:
            dict: Resultado de la actualización con estadísticas
        """
        try:
            # Obtener tasas desde API externa
            external_rates = self._fetch_external_rates(base_currency, source)
            
            if not external_rates:
                return {
                    'success': False,
                    'error': 'No se pudieron obtener tasas de la fuente externa',
                    'updated': 0,
                    'failed': 0
                }
            
            # Obtener monedas actuales del sistema
            current_currencies = self.get_current_rates()
            
            updated = 0
            failed = 0
            results = []
            
            # Actualizar cada moneda
            for currency in current_currencies:
                currency_code = currency.get('currency_code')
                
                # Saltar moneda base
                if currency.get('is_base_currency'):
                    continue
                
                # Buscar tasa en datos externos
                if currency_code in external_rates:
                    new_rate = external_rates[currency_code]
                    
                    # Validar tasa
                    if self.validate_rate(currency_code, new_rate):
                        # Actualizar
                        result = self.update_rate_manual(
                            currency_code, 
                            new_rate, 
                            source=f'auto:{source}'
                        )
                        
                        if result:
                            updated += 1
                            results.append({
                                'currency': currency_code,
                                'old_rate': currency.get('exchange_rate'),
                                'new_rate': new_rate,
                                'status': 'updated'
                            })
                        else:
                            failed += 1
                            results.append({
                                'currency': currency_code,
                                'status': 'failed',
                                'error': 'Error al actualizar en el backend'
                            })
                    else:
                        failed += 1
                        results.append({
                            'currency': currency_code,
                            'status': 'skipped',
                            'error': 'Tasa fuera de rango razonable'
                        })
            
            return {
                'success': True,
                'updated': updated,
                'failed': failed,
                'total': len(current_currencies),
                'source': source,
                'timestamp': timezone.now().isoformat(),
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error in automatic update: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'updated': 0,
                'failed': 0
            }
    
    def _fetch_external_rates(self, base_currency='USD', source='exchangerate-api'):
        """
        Obtener tasas desde API externa
        
        Args:
            base_currency: Moneda base
            source: Fuente de tasas
            
        Returns:
            dict: Diccionario con tasas {currency_code: rate}
        """
        try:
            if source not in self.EXTERNAL_APIS:
                logger.error(f"Unknown source: {source}")
                return None
            
            api_config = self.EXTERNAL_APIS[source]
            
            if source == 'exchangerate-api':
                # API gratuita sin key
                url = api_config['url'].format(base=base_currency)
                
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                
                if 'rates' in data:
                    return data['rates']
            
            elif source == 'fixer':
                # API que requiere key (no implementado completamente)
                api_key = getattr(settings, 'FIXER_API_KEY', None)
                
                if not api_key:
                    logger.error("Fixer API key not configured")
                    return None
                
                url = api_config['url']
                params = {
                    'access_key': api_key,
                    'base': base_currency
                }
                
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                
                if data.get('success') and 'rates' in data:
                    return data['rates']
            
            return None
            
        except requests.RequestException as e:
            logger.error(f"Error fetching external rates: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching rates: {str(e)}")
            return None
    
    def validate_rate(self, currency_code, rate):
        """
        Validar que la tasa sea razonable
        
        Args:
            currency_code: Código de moneda
            rate: Tasa a validar
            
        Returns:
            bool: True si la tasa es válida
        """
        try:
            rate = Decimal(str(rate))
            
            # Obtener rango para esta moneda
            min_rate, max_rate = self.REASONABLE_RANGES.get(
                currency_code, 
                self.REASONABLE_RANGES['DEFAULT']
            )
            
            # Validar rango
            if rate < Decimal(str(min_rate)) or rate > Decimal(str(max_rate)):
                logger.warning(
                    f"Rate {rate} for {currency_code} is outside range "
                    f"[{min_rate}, {max_rate}]"
                )
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating rate: {str(e)}")
            return False
    
    def get_rate_history(self, currency_code, days=30):
        """
        Obtener histórico de tasas
        
        Args:
            currency_code: Código de moneda
            days: Número de días de histórico
            
        Returns:
            list: Lista de registros históricos
        """
        try:
            # En una implementación completa, esto consultaría una tabla
            # de histórico en el backend
            
            # Por ahora, retornar datos de ejemplo
            history = []
            current_date = timezone.now()
            
            # Generar datos de ejemplo (en producción vendría del backend)
            for i in range(days):
                date = current_date - timedelta(days=i)
                # Simular variación de tasa
                base_rate = 1.0 + (i * 0.001)
                
                history.append({
                    'date': date.date().isoformat(),
                    'rate': round(base_rate, 4),
                    'source': 'manual' if i % 7 == 0 else 'auto:exchangerate-api',
                    'timestamp': date.isoformat()
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting rate history: {str(e)}")
            return []
    
    def calculate_rate_change(self, currency_code, period_days=7):
        """
        Calcular cambio porcentual de tasa
        
        Args:
            currency_code: Código de moneda
            period_days: Período en días
            
        Returns:
            dict: Información del cambio
        """
        try:
            history = self.get_rate_history(currency_code, period_days + 1)
            
            if len(history) < 2:
                return {
                    'change_percent': 0.0,
                    'direction': 'stable',
                    'current_rate': 0.0,
                    'previous_rate': 0.0
                }
            
            current = Decimal(str(history[0]['rate']))
            previous = Decimal(str(history[-1]['rate']))
            
            if previous == 0:
                return {
                    'change_percent': 0.0,
                    'direction': 'stable',
                    'current_rate': float(current),
                    'previous_rate': float(previous)
                }
            
            change_percent = ((current - previous) / previous) * 100
            
            if change_percent > 0.1:
                direction = 'up'
            elif change_percent < -0.1:
                direction = 'down'
            else:
                direction = 'stable'
            
            return {
                'change_percent': float(change_percent),
                'direction': direction,
                'current_rate': float(current),
                'previous_rate': float(previous),
                'period_days': period_days
            }
            
        except Exception as e:
            logger.error(f"Error calculating rate change: {str(e)}")
            return {
                'change_percent': 0.0,
                'direction': 'stable',
                'current_rate': 0.0,
                'previous_rate': 0.0
            }

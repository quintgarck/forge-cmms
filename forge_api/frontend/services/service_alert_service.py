"""
Service Alert Service - Detección y gestión de alertas para servicios
Tarea 5.3: Sistema de Alertas del Dashboard de Servicios (Mejoras avanzadas)
"""

import logging
from datetime import datetime, timedelta, date as date_type
from decimal import Decimal
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Importar modelos Django para persistencia
try:
    from core.models import Alert, ServiceAlertThreshold, ServiceAlertEscalation
    DJANGO_MODELS_AVAILABLE = True
except ImportError:
    DJANGO_MODELS_AVAILABLE = False
    logger.warning("Django models not available. Running in standalone mode.")


class ServiceAlertService:
    """
    Servicio para detectar y gestionar alertas relacionadas con servicios
    """
    
    # Umbrales por defecto (configurables)
    DEFAULT_THRESHOLDS = {
        'max_delay_percentage': 20,  # 20% de retraso sobre tiempo estimado
        'max_orders_per_technician': 5,  # Máximo 5 órdenes activas por técnico
        'time_overrun_multiplier': 2.0,  # Tiempo real > estimado * 2
        'low_stock_percentage': 20,  # Stock bajo 20% del mínimo
        'high_productivity_orders': 3,  # >3 órdenes completadas en un día
        'delayed_order_hours': 2,  # Alerta si retraso > 2 horas
        # Umbrales de escalamiento
        'escalation_time_hours': 24,  # Escalar después de 24 horas
        'escalation_time_critical_hours': 4,  # Escalar críticas después de 4 horas
    }
    
    def __init__(self, api_client, user_id=None):
        """
        Inicializar servicio de alertas
        
        Args:
            api_client: Cliente API de ForgeDB
            user_id: ID del usuario actual (para guardar alertas y umbrales)
        """
        self.api_client = api_client
        self.user_id = user_id
        self.thresholds = self.DEFAULT_THRESHOLDS.copy()
        
        # Cargar umbrales desde la base de datos si están disponibles
        if DJANGO_MODELS_AVAILABLE:
            self._load_thresholds_from_db()
    
    def _load_thresholds_from_db(self):
        """Cargar umbrales desde la base de datos."""
        try:
            thresholds_db = ServiceAlertThreshold.objects.filter(is_active=True)
            for threshold in thresholds_db:
                self.thresholds[threshold.threshold_key] = threshold.value
            logger.debug(f"Loaded {thresholds_db.count()} thresholds from database")
        except Exception as e:
            logger.warning(f"Error loading thresholds from database: {e}. Using defaults.")
    
    def update_thresholds(self, **kwargs):
        """
        Actualizar umbrales de alertas.
        Guarda en la base de datos si está disponible.
        """
        self.thresholds.update(kwargs)
        
        # Guardar en base de datos
        if DJANGO_MODELS_AVAILABLE and self.user_id:
            try:
                for key, value in kwargs.items():
                    threshold, created = ServiceAlertThreshold.objects.get_or_create(
                        threshold_key=key,
                        defaults={
                            'threshold_name': key.replace('_', ' ').title(),
                            'value': value,
                            'updated_by': self.user_id
                        }
                    )
                    if not created:
                        threshold.value = value
                        threshold.updated_by = self.user_id
                        threshold.save()
                logger.info(f"Updated {len(kwargs)} thresholds in database")
            except Exception as e:
                logger.error(f"Error saving thresholds to database: {e}")
    
    def _save_alert_to_db(self, alert_data: Dict[str, Any]) -> Optional[int]:
        """
        Guardar alerta en la base de datos.
        
        Returns:
            ID de la alerta guardada o None si no se pudo guardar
        """
        if not DJANGO_MODELS_AVAILABLE:
            return None
        
        try:
            # Mapear tipos de alertas del servicio a tipos del modelo
            alert_type_mapping = {
                'delayed_orders': 'maintenance',
                'low_stock': 'inventory',
                'overloaded_technicians': 'business',
                'anomalous_services': 'business',
                'high_productivity': 'business',
                'unassigned_orders': 'business'
            }
            
            alert_type = alert_data.get('type', 'business')
            db_alert_type = alert_type_mapping.get(alert_type, 'business')
            
            # Buscar si ya existe una alerta similar activa
            ref_id = alert_data.get('details', {}).get('wo_id') or alert_data.get('details', {}).get('technician_id')
            ref_code = alert_data.get('details', {}).get('wo_number') or alert_data.get('details', {}).get('product_code')
            
            existing_alert = None
            if ref_id or ref_code:
                query = Alert.objects.filter(
                    alert_type=db_alert_type,
                    status__in=['new', 'read', 'acknowledged'],
                    severity=alert_data.get('severity', 'medium')
                )
                if ref_id:
                    query = query.filter(ref_id=ref_id)
                if ref_code:
                    query = query.filter(ref_code=ref_code)
                
                existing_alert = query.order_by('-created_at').first()
            
            if existing_alert:
                # Actualizar alerta existente
                existing_alert.title = alert_data.get('title', existing_alert.title)
                existing_alert.message = alert_data.get('message', existing_alert.message)
                existing_alert.details = alert_data.get('details', existing_alert.details)
                existing_alert.severity = alert_data.get('severity', existing_alert.severity)
                existing_alert.save()
                return existing_alert.alert_id
            else:
                # Crear nueva alerta
                new_alert = Alert.objects.create(
                    alert_type=db_alert_type,
                    ref_entity=alert_data.get('details', {}).get('entity_type'),
                    ref_id=ref_id,
                    ref_code=ref_code,
                    title=alert_data.get('title', ''),
                    message=alert_data.get('message', ''),
                    details=alert_data.get('details', {}),
                    severity=alert_data.get('severity', 'medium'),
                    status='new',
                    created_for=self.user_id
                )
                return new_alert.alert_id
                
        except Exception as e:
            logger.error(f"Error saving alert to database: {e}")
            return None
    
    def _check_escalation(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verificar si una alerta debe escalarse basándose en el tiempo transcurrido.
        
        Returns:
            Alert data actualizado con severidad escalada si aplica
        """
        if not DJANGO_MODELS_AVAILABLE:
            return alert_data
        
        try:
            ref_id = alert_data.get('details', {}).get('wo_id') or alert_data.get('details', {}).get('technician_id')
            ref_code = alert_data.get('details', {}).get('wo_number') or alert_data.get('details', {}).get('product_code')
            
            if not ref_id and not ref_code:
                return alert_data
            
            # Buscar alerta existente en la base de datos
            existing_alert = None
            if ref_id:
                existing_alert = Alert.objects.filter(ref_id=ref_id).order_by('-created_at').first()
            elif ref_code:
                existing_alert = Alert.objects.filter(ref_code=ref_code).order_by('-created_at').first()
            
            if not existing_alert:
                return alert_data
            
            # Calcular tiempo transcurrido
            time_elapsed = datetime.now(existing_alert.created_at.tzinfo) - existing_alert.created_at
            hours_elapsed = time_elapsed.total_seconds() / 3600
            
            current_severity = alert_data.get('severity', 'medium')
            escalation_level = ServiceAlertEscalation.objects.filter(alert_id=existing_alert.alert_id).count()
            
            # Determinar si debe escalar
            should_escalate = False
            new_severity = current_severity
            
            if current_severity == 'critical':
                escalation_time = self.thresholds.get('escalation_time_critical_hours', 4)
                if hours_elapsed >= escalation_time and escalation_level == 0:
                    # Escalar de critical a... (podríamos agregar notificación a supervisor)
                    should_escalate = True
            elif current_severity == 'high':
                escalation_time = self.thresholds.get('escalation_time_hours', 24)
                if hours_elapsed >= escalation_time and escalation_level == 0:
                    new_severity = 'critical'
                    should_escalate = True
            elif current_severity == 'medium':
                escalation_time = self.thresholds.get('escalation_time_hours', 24)
                if hours_elapsed >= escalation_time * 2 and escalation_level == 0:
                    new_severity = 'high'
                    should_escalate = True
            elif current_severity == 'low':
                escalation_time = self.thresholds.get('escalation_time_hours', 24)
                if hours_elapsed >= escalation_time * 3 and escalation_level == 0:
                    new_severity = 'medium'
                    should_escalate = True
            
            if should_escalate:
                # Crear registro de escalamiento
                ServiceAlertEscalation.objects.create(
                    alert_id=existing_alert.alert_id,
                    original_severity=current_severity,
                    escalated_severity=new_severity,
                    escalation_level=escalation_level + 1,
                    escalated_by=self.user_id
                )
                
                # Actualizar severidad de la alerta en la base de datos
                existing_alert.severity = new_severity
                existing_alert.save()
                
                # Actualizar datos de la alerta
                alert_data['severity'] = new_severity
                alert_data['escalated'] = True
                alert_data['escalation_level'] = escalation_level + 1
                alert_data['original_severity'] = current_severity
                logger.info(f"Alert {existing_alert.alert_id} escalated from {current_severity} to {new_severity}")
            
        except Exception as e:
            logger.error(f"Error checking escalation: {e}")
        
        return alert_data
    
    def get_active_alerts(self, alert_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Obtener todas las alertas activas del sistema
        
        Args:
            alert_types: Lista de tipos de alertas a filtrar (None = todas)
            
        Returns:
            Lista de alertas activas
        """
        all_alerts = []
        
        # Verificar cada tipo de alerta
        if not alert_types or 'delayed_orders' in alert_types:
            all_alerts.extend(self.check_delayed_orders())
        
        if not alert_types or 'low_stock' in alert_types:
            all_alerts.extend(self.check_low_stock())
        
        if not alert_types or 'overloaded_technicians' in alert_types:
            all_alerts.extend(self.check_overloaded_technicians())
        
        if not alert_types or 'anomalous_services' in alert_types:
            all_alerts.extend(self.check_anomalous_services())
        
        if not alert_types or 'high_productivity' in alert_types:
            all_alerts.extend(self.check_high_productivity())
        
        if not alert_types or 'unassigned_orders' in alert_types:
            all_alerts.extend(self.check_unassigned_orders())
        
        # Verificar escalamiento y guardar alertas en base de datos
        processed_alerts = []
        for alert in all_alerts:
            # Verificar escalamiento
            alert = self._check_escalation(alert)
            # Guardar en base de datos
            db_alert_id = self._save_alert_to_db(alert)
            if db_alert_id:
                alert['db_alert_id'] = db_alert_id
            processed_alerts.append(alert)
        
        # Ordenar por severidad y fecha
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        processed_alerts.sort(key=lambda x: (
            severity_order.get(x.get('severity', 'medium'), 3),
            -x.get('priority', 0)
        ))
        
        return processed_alerts
    
    def check_delayed_orders(self) -> List[Dict[str, Any]]:
        """
        Verificar órdenes de trabajo retrasadas
        
        Returns:
            Lista de alertas de órdenes retrasadas
        """
        alerts = []
        
        try:
            # Obtener órdenes en progreso
            params = {
                'status': 'in_progress',
                'page_size': 1000
            }
            response = self.api_client.get('work-orders/', params=params)
            work_orders = response.get('results', [])
            
            for wo in work_orders:
                wo_id = wo.get('id')
                wo_number = wo.get('wo_number', f'WO-{wo_id}')
                
                # Verificar retraso basado en fecha estimada de completación
                estimated_completion = wo.get('estimated_completion_date')
                if not estimated_completion:
                    continue
                
                try:
                    if isinstance(estimated_completion, str):
                        estimated_date = datetime.fromisoformat(estimated_completion.replace('Z', '+00:00'))
                    else:
                        estimated_date = estimated_completion
                    
                    # Calcular horas de retraso
                    now = datetime.now(estimated_date.tzinfo) if estimated_date.tzinfo else datetime.now()
                    delay_hours = (now - estimated_date).total_seconds() / 3600
                    
                    # Si hay retraso significativo
                    if delay_hours > self.thresholds['delayed_order_hours']:
                        # Calcular porcentaje de retraso
                        estimated_hours = float(wo.get('estimated_hours', 0) or 0)
                        if estimated_hours > 0:
                            delay_percentage = (delay_hours / estimated_hours) * 100
                        else:
                            delay_percentage = 0
                        
                        # Determinar severidad
                        if delay_hours > 8 or delay_percentage > 50:
                            severity = 'critical'
                        elif delay_hours > 4 or delay_percentage > 30:
                            severity = 'high'
                        else:
                            severity = 'medium'
                        
                        alerts.append({
                            'id': f'delayed_wo_{wo_id}',
                            'type': 'delayed_orders',
                            'severity': severity,
                            'title': f'Orden Retrasada: {wo_number}',
                            'message': f'La orden {wo_number} tiene un retraso de {delay_hours:.1f} horas ({delay_percentage:.1f}% sobre tiempo estimado)',
                            'timestamp': now.isoformat(),
                            'priority': int(delay_hours * 10),
                            'action_url': f'/workorders/{wo_id}/',
                            'details': {
                                'wo_id': wo_id,
                                'wo_number': wo_number,
                                'delay_hours': round(delay_hours, 1),
                                'delay_percentage': round(delay_percentage, 1),
                                'estimated_completion': estimated_date.isoformat(),
                                'technician_id': wo.get('primary_technician_id'),
                            }
                        })
                
                except (ValueError, TypeError) as e:
                    logger.debug(f"Error parsing date for WO {wo_id}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error checking delayed orders: {e}")
        
        return alerts
    
    def check_low_stock(self) -> List[Dict[str, Any]]:
        """
        Verificar productos con stock bajo
        
        Returns:
            Lista de alertas de stock bajo
        """
        alerts = []
        
        try:
            # Obtener productos con stock bajo
            params = {
                'low_stock': True,
                'page_size': 1000
            }
            response = self.api_client.get('stock/', params=params)
            stock_items = response.get('results', [])
            
            critical_items = []
            warning_items = []
            
            for item in stock_items:
                current_qty = float(item.get('quantity', 0) or 0)
                min_qty = float(item.get('min_quantity', 0) or 0)
                product_code = item.get('product_code', 'N/A')
                product_name = item.get('product_name', 'Producto desconocido')
                
                if min_qty <= 0:
                    continue
                
                # Calcular porcentaje del stock mínimo
                stock_percentage = (current_qty / min_qty) * 100 if min_qty > 0 else 0
                
                if current_qty <= 0:
                    # Stock agotado - crítico
                    critical_items.append({
                        'product_code': product_code,
                        'product_name': product_name,
                        'current_qty': current_qty,
                        'min_qty': min_qty,
                        'warehouse': item.get('warehouse_name', 'N/A')
                    })
                elif stock_percentage < self.thresholds['low_stock_percentage']:
                    # Stock muy bajo - advertencia
                    warning_items.append({
                        'product_code': product_code,
                        'product_name': product_name,
                        'current_qty': current_qty,
                        'min_qty': min_qty,
                        'stock_percentage': stock_percentage,
                        'warehouse': item.get('warehouse_name', 'N/A')
                    })
            
            # Crear alerta por stock agotado
            if critical_items:
                items_text = ', '.join([f"{item['product_code']} ({item['product_name']})" for item in critical_items[:5]])
                if len(critical_items) > 5:
                    items_text += f" y {len(critical_items) - 5} más"
                
                alerts.append({
                    'id': 'low_stock_critical',
                    'type': 'low_stock',
                    'severity': 'critical',
                    'title': f'Stock Agotado: {len(critical_items)} productos',
                    'message': f'Los siguientes productos están agotados: {items_text}',
                    'timestamp': datetime.now().isoformat(),
                    'priority': 90,
                    'action_url': '/inventory/?filter=low_stock',
                    'details': {
                        'items': critical_items,
                        'count': len(critical_items)
                    }
                })
            
            # Crear alerta por stock bajo
            if warning_items:
                items_text = ', '.join([f"{item['product_code']}" for item in warning_items[:5]])
                if len(warning_items) > 5:
                    items_text += f" y {len(warning_items) - 5} más"
                
                alerts.append({
                    'id': 'low_stock_warning',
                    'type': 'low_stock',
                    'severity': 'medium',
                    'title': f'Stock Bajo: {len(warning_items)} productos',
                    'message': f'Los siguientes productos tienen stock bajo: {items_text}',
                    'timestamp': datetime.now().isoformat(),
                    'priority': 50,
                    'action_url': '/inventory/?filter=low_stock',
                    'details': {
                        'items': warning_items,
                        'count': len(warning_items)
                    }
                })
        
        except Exception as e:
            logger.error(f"Error checking low stock: {e}")
        
        return alerts
    
    def check_overloaded_technicians(self) -> List[Dict[str, Any]]:
        """
        Verificar técnicos con demasiadas órdenes activas
        
        Returns:
            Lista de alertas de técnicos sobrecargados
        """
        alerts = []
        
        try:
            # Obtener técnicos activos
            tech_response = self.api_client.get('technicians/', params={'is_active': True, 'page_size': 100})
            technicians = tech_response.get('results', [])
            
            # Obtener órdenes en progreso
            wo_params = {
                'status__in': ['scheduled', 'in_progress'],
                'page_size': 1000
            }
            wo_response = self.api_client.get('work-orders/', params=wo_params)
            work_orders = wo_response.get('results', [])
            
            # Contar órdenes por técnico
            tech_order_count = {}
            for wo in work_orders:
                tech_id = wo.get('primary_technician_id')
                if tech_id:
                    tech_order_count[tech_id] = tech_order_count.get(tech_id, 0) + 1
            
            max_orders = self.thresholds['max_orders_per_technician']
            
            for tech_id, order_count in tech_order_count.items():
                if order_count > max_orders:
                    # Buscar información del técnico
                    tech = next((t for t in technicians if t.get('id') == tech_id), None)
                    tech_name = tech.get('name', f'Técnico {tech_id}') if tech else f'Técnico {tech_id}'
                    
                    alerts.append({
                        'id': f'overloaded_tech_{tech_id}',
                        'type': 'overloaded_technicians',
                        'severity': 'medium',
                        'title': f'Técnico Sobrecargado: {tech_name}',
                        'message': f'{tech_name} tiene {order_count} órdenes activas (máximo recomendado: {max_orders})',
                        'timestamp': datetime.now().isoformat(),
                        'priority': order_count * 10,
                        'action_url': f'/technicians/{tech_id}/',
                        'details': {
                            'technician_id': tech_id,
                            'technician_name': tech_name,
                            'order_count': order_count,
                            'max_recommended': max_orders
                        }
                    })
        
        except Exception as e:
            logger.error(f"Error checking overloaded technicians: {e}")
        
        return alerts
    
    def check_anomalous_services(self) -> List[Dict[str, Any]]:
        """
        Verificar servicios con tiempos anómalos (muy altos)
        
        Returns:
            Lista de alertas de servicios anómalos
        """
        alerts = []
        
        try:
            multiplier = self.thresholds['time_overrun_multiplier']
            
            # Obtener órdenes completadas recientemente
            today = date_type.today()
            params = {
                'status': 'completed',
                'completed_date__gte': (today - timedelta(days=7)).isoformat(),
                'page_size': 1000
            }
            response = self.api_client.get('work-orders/', params=params)
            work_orders = response.get('results', [])
            
            anomalous_orders = []
            
            for wo in work_orders:
                estimated_hours = float(wo.get('estimated_hours', 0) or 0)
                actual_hours = float(wo.get('actual_hours', 0) or 0)
                
                if estimated_hours > 0 and actual_hours > (estimated_hours * multiplier):
                    wo_number = wo.get('wo_number', f"WO-{wo.get('id')}")
                    overrun_percentage = ((actual_hours - estimated_hours) / estimated_hours) * 100
                    
                    anomalous_orders.append({
                        'wo_id': wo.get('id'),
                        'wo_number': wo_number,
                        'estimated_hours': estimated_hours,
                        'actual_hours': actual_hours,
                        'overrun_percentage': overrun_percentage
                    })
            
            if anomalous_orders:
                orders_text = ', '.join([order['wo_number'] for order in anomalous_orders[:5]])
                if len(anomalous_orders) > 5:
                    orders_text += f" y {len(anomalous_orders) - 5} más"
                
                alerts.append({
                    'id': 'anomalous_services',
                    'type': 'anomalous_services',
                    'severity': 'low',
                    'title': f'Servicios Anómalos: {len(anomalous_orders)} órdenes',
                    'message': f'{len(anomalous_orders)} órdenes completadas excedieron el tiempo estimado en más del {int((multiplier - 1) * 100)}%: {orders_text}',
                    'timestamp': datetime.now().isoformat(),
                    'priority': len(anomalous_orders) * 5,
                    'action_url': '/workorders/?filter=anomalous',
                    'details': {
                        'orders': anomalous_orders,
                        'count': len(anomalous_orders),
                        'multiplier': multiplier
                    }
                })
        
        except Exception as e:
            logger.error(f"Error checking anomalous services: {e}")
        
        return alerts
    
    def check_high_productivity(self) -> List[Dict[str, Any]]:
        """
        Detectar técnicos con alta productividad (reconocimiento)
        
        Returns:
            Lista de alertas de alta productividad (positivas)
        """
        alerts = []
        
        try:
            today = date_type.today()
            min_orders = self.thresholds['high_productivity_orders']
            
            # Obtener órdenes completadas hoy
            params = {
                'status': 'completed',
                'completed_date__gte': today.isoformat(),
                'page_size': 1000
            }
            response = self.api_client.get('work-orders/', params=params)
            work_orders = response.get('results', [])
            
            # Contar órdenes completadas hoy por técnico
            tech_completed_count = {}
            for wo in work_orders:
                tech_id = wo.get('primary_technician_id')
                if tech_id:
                    tech_completed_count[tech_id] = tech_completed_count.get(tech_id, 0) + 1
            
            # Obtener información de técnicos
            tech_response = self.api_client.get('technicians/', params={'page_size': 100})
            technicians = tech_response.get('results', [])
            
            for tech_id, count in tech_completed_count.items():
                if count >= min_orders:
                    tech = next((t for t in technicians if t.get('id') == tech_id), None)
                    tech_name = tech.get('name', f'Técnico {tech_id}') if tech else f'Técnico {tech_id}'
                    
                    alerts.append({
                        'id': f'high_productivity_{tech_id}_{today.isoformat()}',
                        'type': 'high_productivity',
                        'severity': 'low',
                        'title': f'Alta Productividad: {tech_name}',
                        'message': f'¡Excelente trabajo! {tech_name} ha completado {count} órdenes hoy',
                        'timestamp': datetime.now().isoformat(),
                        'priority': count * 5,
                        'action_url': f'/technicians/{tech_id}/',
                        'details': {
                            'technician_id': tech_id,
                            'technician_name': tech_name,
                            'orders_completed_today': count,
                            'date': today.isoformat()
                        }
                    })
        
        except Exception as e:
            logger.error(f"Error checking high productivity: {e}")
        
        return alerts
    
    def check_unassigned_orders(self) -> List[Dict[str, Any]]:
        """
        Verificar órdenes sin técnico asignado
        
        Returns:
            Lista de alertas de órdenes sin asignar
        """
        alerts = []
        
        try:
            params = {
                'status__in': ['scheduled', 'in_progress'],
                'page_size': 1000
            }
            response = self.api_client.get('work-orders/', params=params)
            work_orders = response.get('results', [])
            
            unassigned = [wo for wo in work_orders if not wo.get('primary_technician_id')]
            
            if unassigned:
                wo_numbers = [wo.get('wo_number', f"WO-{wo.get('id')}") for wo in unassigned[:10]]
                wo_text = ', '.join(wo_numbers)
                if len(unassigned) > 10:
                    wo_text += f" y {len(unassigned) - 10} más"
                
                alerts.append({
                    'id': 'unassigned_orders',
                    'type': 'unassigned_orders',
                    'severity': 'medium',
                    'title': f'Órdenes Sin Asignar: {len(unassigned)}',
                    'message': f'Hay {len(unassigned)} órdenes activas sin técnico asignado: {wo_text}',
                    'timestamp': datetime.now().isoformat(),
                    'priority': len(unassigned) * 10,
                    'action_url': '/workorders/?filter=unassigned',
                    'details': {
                        'orders': [{'wo_id': wo.get('id'), 'wo_number': wo.get('wo_number')} for wo in unassigned],
                        'count': len(unassigned)
                    }
                })
        
        except Exception as e:
            logger.error(f"Error checking unassigned orders: {e}")
        
        return alerts

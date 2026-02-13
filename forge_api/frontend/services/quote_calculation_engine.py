"""
Quote Calculation Engine - Motor de cálculo de cotizaciones
Tarea 6.2: Implementar motor de cálculo
"""

import logging
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any, Optional
from datetime import date, timedelta

logger = logging.getLogger(__name__)


class QuoteCalculationEngine:
    """
    Motor de cálculo para cotizaciones de servicios.
    Calcula mano de obra, materiales, descuentos y recargos.
    """
    
    DEFAULT_TAX_PERCENT = Decimal('16.00')  # IVA por defecto
    DEFAULT_HOURLY_RATE = Decimal('500.00')  # Tarifa horaria por defecto
    
    def __init__(self, api_client=None):
        """
        Inicializar motor de cálculo.
        
        Args:
            api_client: Cliente API para obtener datos (precios, tarifas, etc.)
        """
        self.api_client = api_client
    
    def calculate_labor_cost(self, hours: Decimal, hourly_rate: Optional[Decimal] = None) -> Decimal:
        """
        Calcular costo de mano de obra.
        
        Args:
            hours: Horas de trabajo
            hourly_rate: Tarifa por hora (si None, usa la tarifa por defecto)
            
        Returns:
            Costo total de mano de obra
        """
        if hourly_rate is None:
            hourly_rate = self.DEFAULT_HOURLY_RATE
        
        if hours <= 0 or hourly_rate <= 0:
            return Decimal('0.00')
        
        return (hours * hourly_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def calculate_material_cost(self, items: List[Dict[str, Any]]) -> Decimal:
        """
        Calcular costo de materiales/repuestos.
        
        Args:
            items: Lista de items de material con 'quantity' y 'unit_price'
            
        Returns:
            Costo total de materiales
        """
        total = Decimal('0.00')
        
        for item in items:
            quantity = Decimal(str(item.get('quantity', 0)))
            unit_price = Decimal(str(item.get('unit_price', 0)))
            
            if quantity > 0 and unit_price > 0:
                line_total = (quantity * unit_price).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                total += line_total
        
        return total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def calculate_discount(self, subtotal: Decimal, discount_percent: Optional[Decimal] = None, 
                          discount_amount: Optional[Decimal] = None) -> Dict[str, Decimal]:
        """
        Calcular descuento aplicado.
        
        Args:
            subtotal: Subtotal antes de descuentos
            discount_percent: Porcentaje de descuento (0-100)
            discount_amount: Monto fijo de descuento
            
        Returns:
            Dict con 'discount_amount' y 'after_discount'
        """
        discount = Decimal('0.00')
        
        # Aplicar descuento por porcentaje si está definido
        if discount_percent is not None and discount_percent > 0:
            discount = (subtotal * discount_percent / 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # Aplicar descuento por monto fijo si está definido (tiene prioridad sobre porcentaje)
        if discount_amount is not None and discount_amount > 0:
            discount = discount_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # El descuento no puede ser mayor que el subtotal
        discount = min(discount, subtotal)
        
        after_discount = (subtotal - discount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        return {
            'discount_amount': discount,
            'after_discount': after_discount
        }
    
    def calculate_surcharge(self, base_amount: Decimal, surcharge_percent: Optional[Decimal] = None,
                           surcharge_amount: Optional[Decimal] = None) -> Dict[str, Decimal]:
        """
        Calcular recargo aplicado.
        
        Args:
            base_amount: Monto base para aplicar recargo
            surcharge_percent: Porcentaje de recargo
            surcharge_amount: Monto fijo de recargo
            
        Returns:
            Dict con 'surcharge_amount' y 'after_surcharge'
        """
        surcharge = Decimal('0.00')
        
        # Aplicar recargo por porcentaje
        if surcharge_percent is not None and surcharge_percent > 0:
            surcharge = (base_amount * surcharge_percent / 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # Aplicar recargo por monto fijo (tiene prioridad)
        if surcharge_amount is not None and surcharge_amount > 0:
            surcharge = surcharge_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        after_surcharge = (base_amount + surcharge).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        return {
            'surcharge_amount': surcharge,
            'after_surcharge': after_surcharge
        }
    
    def calculate_tax(self, base_amount: Decimal, tax_percent: Optional[Decimal] = None) -> Dict[str, Decimal]:
        """
        Calcular impuesto (IVA).
        
        Args:
            base_amount: Monto base para calcular impuesto
            tax_percent: Porcentaje de impuesto (si None, usa el por defecto)
            
        Returns:
            Dict con 'tax_amount' y 'after_tax'
        """
        if tax_percent is None:
            tax_percent = self.DEFAULT_TAX_PERCENT
        
        tax_amount = (base_amount * tax_percent / 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        after_tax = (base_amount + tax_amount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        return {
            'tax_amount': tax_amount,
            'tax_percent': tax_percent,
            'after_tax': after_tax
        }
    
    def calculate_quote_item_total(self, item: Dict[str, Any]) -> Dict[str, Decimal]:
        """
        Calcular total de un item de cotización.
        
        Args:
            item: Dict con 'hours', 'hourly_rate', 'quantity', y opcionalmente 'unit_price'
            
        Returns:
            Dict con cálculos del item
        """
        hours = Decimal(str(item.get('hours', 0)))
        hourly_rate = Decimal(str(item.get('hourly_rate', self.DEFAULT_HOURLY_RATE)))
        quantity = Decimal(str(item.get('quantity', 1)))
        
        # Calcular costo de mano de obra
        labor_cost = self.calculate_labor_cost(hours, hourly_rate) * quantity
        
        # Si hay costo de materiales en el item
        material_cost = Decimal('0.00')
        if 'material_cost' in item:
            material_cost = Decimal(str(item.get('material_cost', 0)))
        
        line_subtotal = (labor_cost + material_cost).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        return {
            'hours': hours,
            'hourly_rate': hourly_rate,
            'quantity': quantity,
            'labor_cost': labor_cost,
            'material_cost': material_cost,
            'line_subtotal': line_subtotal
        }
    
    def calculate_quote_totals(self, items: List[Dict[str, Any]], 
                               discount_percent: Optional[Decimal] = None,
                               discount_amount: Optional[Decimal] = None,
                               tax_percent: Optional[Decimal] = None,
                               additional_costs: Optional[Decimal] = None) -> Dict[str, Any]:
        """
        Calcular totales completos de una cotización.
        
        Args:
            items: Lista de items de la cotización
            discount_percent: Porcentaje de descuento
            discount_amount: Monto fijo de descuento
            tax_percent: Porcentaje de impuesto
            additional_costs: Costos adicionales (herramientas, transporte, etc.)
            
        Returns:
            Dict con todos los cálculos
        """
        # Calcular subtotal de items
        labor_total = Decimal('0.00')
        materials_total = Decimal('0.00')
        total_hours = Decimal('0.00')
        
        for item in items:
            item_calc = self.calculate_quote_item_total(item)
            labor_total += item_calc['labor_cost']
            materials_total += item_calc['material_cost']
            total_hours += item_calc['hours'] * item_calc['quantity']
        
        # Agregar costos adicionales
        if additional_costs:
            additional_costs = Decimal(str(additional_costs))
        else:
            additional_costs = Decimal('0.00')
        
        # Subtotal antes de descuentos
        subtotal = (labor_total + materials_total + additional_costs).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
        
        # Aplicar descuentos
        discount_calc = self.calculate_discount(subtotal, discount_percent, discount_amount)
        after_discount = discount_calc['after_discount']
        
        # Calcular impuesto
        tax_calc = self.calculate_tax(after_discount, tax_percent)
        
        # Total final
        total = tax_calc['after_tax']
        
        return {
            'labor_total': labor_total,
            'materials_total': materials_total,
            'additional_costs': additional_costs,
            'subtotal': subtotal,
            'discount_percent': discount_percent or Decimal('0.00'),
            'discount_amount': discount_calc['discount_amount'],
            'after_discount': after_discount,
            'tax_percent': tax_calc['tax_percent'],
            'tax_amount': tax_calc['tax_amount'],
            'total': total,
            'total_hours': total_hours
        }
    
    def validate_business_rules(self, quote_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validar reglas de negocio para la cotización.
        
        Args:
            quote_data: Datos de la cotización a validar
            
        Returns:
            Dict con 'valid' (bool) y 'errors' (list)
        """
        errors = []
        warnings = []
        
        # Validar que hay al menos un item
        items = quote_data.get('items', [])
        if not items or len(items) == 0:
            errors.append("La cotización debe tener al menos un item de servicio")
        
        # Validar que el total no sea negativo
        total = Decimal(str(quote_data.get('total', 0)))
        if total < 0:
            errors.append("El total de la cotización no puede ser negativo")
        
        # Validar que el descuento no sea mayor que el subtotal
        discount_amount = Decimal(str(quote_data.get('discount_amount', 0)))
        subtotal = Decimal(str(quote_data.get('subtotal', 0)))
        if discount_amount > subtotal:
            errors.append("El descuento no puede ser mayor que el subtotal")
        
        # Validar que las horas sean positivas
        total_hours = Decimal(str(quote_data.get('total_hours', 0)))
        if total_hours <= 0:
            warnings.append("La cotización tiene 0 horas de trabajo")
        
        # Validar fecha de validez
        valid_until = quote_data.get('valid_until')
        if valid_until:
            try:
                if isinstance(valid_until, str):
                    valid_date = date.fromisoformat(valid_until)
                else:
                    valid_date = valid_until
                
                if valid_date < date.today():
                    warnings.append("La fecha de validez está en el pasado")
                elif valid_date > date.today() + timedelta(days=90):
                    warnings.append("La fecha de validez es muy lejana (más de 90 días)")
            except (ValueError, TypeError):
                errors.append("La fecha de validez no es válida")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

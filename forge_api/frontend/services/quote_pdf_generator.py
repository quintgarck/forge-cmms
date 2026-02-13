"""
Quote PDF Generator - Generador de PDF para cotizaciones
Tarea 6.3: Generación de PDF
"""

import logging
from io import BytesIO
from decimal import Decimal
from datetime import datetime, date
from typing import Dict, Any, Optional

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.units import inch, cm
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logging.warning("ReportLab no está disponible. La generación de PDF estará deshabilitada.")

logger = logging.getLogger(__name__)


class QuotePDFGenerator:
    """
    Generador de PDF para cotizaciones usando ReportLab.
    """
    
    def __init__(self):
        """Inicializar generador de PDF."""
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab no está instalado. Instale con: pip install reportlab")
        
        self.page_size = A4
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Configurar estilos personalizados."""
        # Título
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e3a8a'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Subtítulo
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))
        
        # Texto normal
        self.styles.add(ParagraphStyle(
            name='CustomNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#1f2937'),
            leading=12
        ))
        
        # Texto destacado
        self.styles.add(ParagraphStyle(
            name='CustomBold',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#1f2937'),
            fontName='Helvetica-Bold'
        ))
        
        # Texto pequeño
        self.styles.add(ParagraphStyle(
            name='CustomSmall',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#6b7280'),
            leading=10
        ))
    
    def generate_pdf(self, quote_data: Dict[str, Any], company_data: Optional[Dict[str, Any]] = None) -> BytesIO:
        """
        Generar PDF de cotización.
        
        Args:
            quote_data: Datos de la cotización
            company_data: Datos de la empresa (opcional)
            
        Returns:
            BytesIO: Buffer con el PDF generado
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=self.page_size, 
                                rightMargin=2*cm, leftMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)
        
        story = []
        
        # Encabezado
        story.extend(self._build_header(quote_data, company_data))
        story.append(Spacer(1, 0.5*cm))
        
        # Información de cliente y cotización
        story.extend(self._build_info_section(quote_data))
        story.append(Spacer(1, 0.5*cm))
        
        # Items de cotización
        story.extend(self._build_items_section(quote_data))
        story.append(Spacer(1, 0.5*cm))
        
        # Resumen de totales
        story.extend(self._build_totals_section(quote_data))
        
        # Términos y condiciones
        if quote_data.get('terms_and_conditions'):
            story.append(Spacer(1, 0.5*cm))
            story.extend(self._build_terms_section(quote_data))
        
        # Notas
        if quote_data.get('notes'):
            story.append(Spacer(1, 0.5*cm))
            story.extend(self._build_notes_section(quote_data))
        
        # Pie de página
        story.append(Spacer(1, 1*cm))
        story.extend(self._build_footer(quote_data, company_data))
        
        # Construir PDF
        doc.build(story, onFirstPage=self._add_page_number, onLaterPages=self._add_page_number)
        
        buffer.seek(0)
        return buffer
    
    def _build_header(self, quote_data: Dict, company_data: Optional[Dict] = None) -> list:
        """Construir encabezado del PDF."""
        elements = []
        
        # Título
        title = f"COTIZACIÓN #{quote_data.get('quote_number', 'N/A')}"
        elements.append(Paragraph(title, self.styles['CustomTitle']))
        elements.append(Spacer(1, 0.3*cm))
        
        # Información de empresa (si está disponible)
        if company_data:
            company_name = company_data.get('name', 'MovIAx')
            company_address = company_data.get('address', '')
            company_phone = company_data.get('phone', '')
            company_email = company_data.get('email', '')
            
            company_info = f"<b>{company_name}</b><br/>"
            if company_address:
                company_info += f"{company_address}<br/>"
            if company_phone:
                company_info += f"Tel: {company_phone}<br/>"
            if company_email:
                company_info += f"Email: {company_email}"
            
            elements.append(Paragraph(company_info, self.styles['CustomNormal']))
            elements.append(Spacer(1, 0.3*cm))
        
        return elements
    
    def _build_info_section(self, quote_data: Dict) -> list:
        """Construir sección de información de cliente y cotización."""
        elements = []
        
        # Datos de cliente
        client = quote_data.get('client', {})
        client_name = client.get('name', 'N/A')
        client_address = client.get('address', '')
        client_phone = client.get('phone', '')
        client_email = client.get('email', '')
        
        # Datos de cotización
        quote_date = quote_data.get('quote_date', '')
        if isinstance(quote_date, str):
            try:
                quote_date = datetime.fromisoformat(quote_date.replace('Z', '+00:00')).date()
            except:
                quote_date = date.today()
        elif not isinstance(quote_date, date):
            quote_date = date.today()
        
        valid_until = quote_data.get('valid_until')
        if valid_until:
            if isinstance(valid_until, str):
                try:
                    valid_until = datetime.fromisoformat(valid_until.replace('Z', '+00:00')).date()
                except:
                    valid_until = None
            elif not isinstance(valid_until, date):
                valid_until = None
        else:
            valid_until = None
        
        # Crear tabla de información
        info_data = [
            ['Cliente:', client_name],
            ['Fecha:', quote_date.strftime('%d/%m/%Y')],
            ['Válida hasta:', valid_until.strftime('%d/%m/%Y') if valid_until else 'No especificada'],
        ]
        
        if client_address:
            info_data.append(['Dirección:', client_address])
        if client_phone:
            info_data.append(['Teléfono:', client_phone])
        if client_email:
            info_data.append(['Email:', client_email])
        
        info_table = Table(info_data, colWidths=[4*cm, 12*cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f4f6')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), TA_LEFT),
            ('ALIGN', (1, 0), (1, -1), TA_LEFT),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        
        elements.append(info_table)
        
        return elements
    
    def _build_items_section(self, quote_data: Dict) -> list:
        """Construir sección de items de cotización."""
        elements = []
        
        elements.append(Paragraph("ITEMS DE SERVICIO", self.styles['CustomHeading']))
        
        items = quote_data.get('items', [])
        
        if not items:
            elements.append(Paragraph("No hay items en esta cotización.", self.styles['CustomNormal']))
            return elements
        
        # Encabezados de tabla
        headers = ['#', 'Descripción', 'Cant.', 'Horas', 'Tarifa/Hora', 'Total']
        items_data = [headers]
        
        # Datos de items
        for idx, item in enumerate(items, 1):
            description = item.get('description', '')
            quantity = str(item.get('quantity', 1))
            hours = f"{float(item.get('hours', 0)):.2f}"
            hourly_rate = f"${float(item.get('hourly_rate', 0)):.2f}"
            line_total = f"${float(item.get('line_total', 0)):.2f}"
            
            items_data.append([
                str(idx),
                description[:50] + '...' if len(description) > 50 else description,
                quantity,
                hours,
                hourly_rate,
                line_total
            ])
        
        # Crear tabla
        items_table = Table(items_data, colWidths=[0.8*cm, 8*cm, 1*cm, 1.5*cm, 2*cm, 2*cm])
        items_table.setStyle(TableStyle([
            # Encabezado
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), TA_CENTER),
            ('ALIGN', (1, 0), (1, -1), TA_LEFT),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            # Filas
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
        ]))
        
        elements.append(items_table)
        
        return elements
    
    def _build_totals_section(self, quote_data: Dict) -> list:
        """Construir sección de totales."""
        elements = []
        
        elements.append(Paragraph("RESUMEN DE TOTALES", self.styles['CustomHeading']))
        
        subtotal = float(quote_data.get('subtotal', 0))
        discount_percent = float(quote_data.get('discount_percent', 0))
        discount_amount = float(quote_data.get('discount_amount', 0))
        tax_percent = float(quote_data.get('tax_percent', 0))
        tax_amount = float(quote_data.get('tax_amount', 0))
        total = float(quote_data.get('total', 0))
        total_hours = float(quote_data.get('total_hours', 0))
        currency_code = quote_data.get('currency_code', 'MXN')
        
        totals_data = [
            ['Subtotal:', f"${subtotal:.2f}"],
        ]
        
        if discount_amount > 0:
            totals_data.append([
                f'Descuento ({discount_percent:.2f}%):',
                f"-${discount_amount:.2f}"
            ])
            after_discount = subtotal - discount_amount
            totals_data.append(['Después de descuento:', f"${after_discount:.2f}"])
        
        totals_data.extend([
            [f'Impuestos ({tax_percent:.2f}%):', f"${tax_amount:.2f}"],
            ['TOTAL:', f"${total:.2f} {currency_code}"],
            ['Total de Horas:', f"{total_hours:.2f} hrs"],
        ])
        
        totals_table = Table(totals_data, colWidths=[10*cm, 6*cm])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -2), TA_LEFT),
            ('ALIGN', (1, 0), (1, -1), TA_RIGHT),
            ('ALIGN', (0, -1), (0, -1), TA_LEFT),
            ('FONTNAME', (0, 0), (0, -2), 'Helvetica'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTNAME', (0, -2), (-1, -2), 'Helvetica-Bold'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -2), 10),
            ('FONTSIZE', (0, -2), (-1, -1), 12),
            ('TEXTCOLOR', (0, -2), (-1, -2), colors.HexColor('#1e3a8a')),
            ('LINEABOVE', (0, -2), (-1, -2), 1, colors.grey),
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor('#1e3a8a')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(totals_table)
        
        return elements
    
    def _build_terms_section(self, quote_data: Dict) -> list:
        """Construir sección de términos y condiciones."""
        elements = []
        
        elements.append(Paragraph("TÉRMINOS Y CONDICIONES", self.styles['CustomHeading']))
        terms = quote_data.get('terms_and_conditions', '')
        elements.append(Paragraph(terms.replace('\n', '<br/>'), self.styles['CustomNormal']))
        
        return elements
    
    def _build_notes_section(self, quote_data: Dict) -> list:
        """Construir sección de notas."""
        elements = []
        
        elements.append(Paragraph("NOTAS", self.styles['CustomHeading']))
        notes = quote_data.get('notes', '')
        elements.append(Paragraph(notes.replace('\n', '<br/>'), self.styles['CustomSmall']))
        
        return elements
    
    def _build_footer(self, quote_data: Dict, company_data: Optional[Dict] = None) -> list:
        """Construir pie de página."""
        elements = []
        
        footer_text = f"Este documento fue generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        elements.append(Paragraph(footer_text, self.styles['CustomSmall']))
        
        return elements
    
    def _add_page_number(self, canvas_obj, doc):
        """Agregar número de página."""
        page_num = canvas_obj.getPageNumber()
        text = f"Página {page_num}"
        canvas_obj.saveState()
        canvas_obj.setFont('Helvetica', 8)
        canvas_obj.drawCentredString(self.page_size[0] / 2.0, 1*cm, text)
        canvas_obj.restoreState()

# Generador de reportes PDF para análisis
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
from pathlib import Path
import base64
import io

# WeasyPrint para HTML -> PDF (requiere: pip install weasyprint)
# Alternativa: reportlab para PDF nativo
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm, mm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


class ReportGenerator:
    """Generador de reportes PDF para análisis forrajero."""
    
    def __init__(self, output_dir: str = "/data/reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Estilos de colores
        self.colors = {
            "primary": HexColor("#16a34a"),      # verde
            "secondary": HexColor("#15803d"),    # verde oscuro
            "accent": HexColor("#22c55e"),       # verde claro
            "text": HexColor("#1f2937"),         # gris oscuro
            "muted": HexColor("#6b7280"),        # gris medio
            "error": HexColor("#dc2626"),        # rojo
            "warning": HexColor("#d97706"),      # ámbar
            "background": HexColor("#f0fdf4"),   # verde muy claro
            "white": HexColor("#ffffff"),
        }
    
    def generate_analysis_report(
        self,
        analysis_data: Dict[str, Any],
        lot_data: Dict[str, Any],
        user_data: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Genera reporte PDF del análisis.
        
        Retorna: path del archivo PDF generado
        """
        if not REPORTLAB_AVAILABLE:
            raise RuntimeError("ReportLab no está instalado. Instalar con: pip install reportlab")
        
        # Configuración por defecto
        default_config = {
            "include_logo": True,
            "include_metadata": True,
            "include_legend": True,
            "include_analysis_date": True,
            "include_parameters": True,
            "logo_path": None,
            "title": "Reporte de Análisis Forrajero",
        }
        if config:
            default_config.update(config)
        cfg = default_config
        
        # Generar nombre de archivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"analysis_{analysis_data['id']}_{timestamp}.pdf"
        filepath = self.output_dir / filename
        
        # Crear documento
        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm,
        )
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=self.colors["primary"],
            spaceAfter=6,
            alignment=TA_CENTER,
        )
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=self.colors["secondary"],
            spaceAfter=12,
            alignment=TA_CENTER,
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=self.colors["primary"],
            spaceBefore=12,
            spaceAfter=6,
        )
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=10,
            textColor=self.colors["text"],
            spaceAfter=4,
        )
        label_style = ParagraphStyle(
            'LabelStyle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=self.colors["muted"],
            spaceAfter=2,
        )
        value_style = ParagraphStyle(
            'ValueStyle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=self.colors["text"],
            spaceAfter=8,
        )
        
        # Contenido del PDF
        story = []
        
        # === PORTADA ===
        if cfg.get("include_logo", True):
            if cfg.get("logo_path"):
                try:
                    logo = Image(cfg["logo_path"], width=4*cm, height=4*cm)
                    logo.hAlign = 'CENTER'
                    story.append(logo)
                    story.append(Spacer(1, 12))
                except:
                    pass
        
        story.append(Paragraph(cfg.get("title", "Reporte de Análisis Forrajero"), title_style))
        story.append(Spacer(1, 6))
        story.append(Paragraph("GeoForraje 1.0 - Plataforma de Análisis Forrajero Geoespacial", subtitle_style))
        story.append(Spacer(1, 24))
        
        # === METADATOS ===
        if cfg.get("include_metadata", True):
            story.append(Paragraph("Información General", heading_style))
            
            meta_data = [
                ["Análisis ID:", str(analysis_data.get("id", "N/A"))],
                ["Lote:", lot_data.get("name", "N/A")],
                ["Usuario:", user_data.get("full_name", user_data.get("email", "N/A"))],
                ["Fecha análisis:", self._format_datetime(analysis_data.get("analyzed_at"))],
                ["Fecha reporte:", self._format_datetime(datetime.now())],
                ["Estado:", self._status_label(analysis_data.get("status"))],
            ]
            
            meta_table = Table(meta_data, colWidths=[5*cm, 12*cm])
            meta_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('TEXTCOLOR', (0, 0), (0, -1), self.colors["muted"]),
                ('TEXTCOLOR', (1, 0), (1, -1), self.colors["text"]),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ])
            story.append(meta_table)
            story.append(Spacer(1, 18))
        
        # === PARÁMETROS DE ANÁLISIS ===
        if cfg.get("include_parameters", True):
            story.append(Paragraph("Parámetros de Análisis", heading_style))
            
            resource_labels = {
                "resource_1": "Biomasa verde (kg/ha)",
                "resource_2": "Cobertura suelo (%)",
                "resource_3": "Índice vegetación (NDVI)",
                "resource_4": "Humedad suelo (%)",
            }
            
            param_data = [
                ["Recurso analizado:", resource_labels.get(analysis_data.get("resource_type"), analysis_data.get("resource_type"))],
                ["Raster origen:", analysis_data.get("raster_file_reference", "N/A")],
                ["Versión raster:", analysis_data.get("raster_version", "N/A")],
                ["Fecha raster:", self._format_datetime(analysis_data.get("raster_date"))],
                ["Geometría lote hash:", analysis_data.get("lot_geometry_hash", "N/A")[:16] + "..."],
                ["Raster recortado guardado:", "Sí" if analysis_data.get("store_clipped_raster") else "No"],
            ]
            
            if analysis_data.get("clipped_raster_path"):
                param_data.append(["Raster recortado:", analysis_data.get("clipped_raster_path")])
            
            param_table = Table(param_data, colWidths=[5*cm, 12*cm])
            param_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('TEXTCOLOR', (0, 0), (0, -1), self.colors["muted"]),
                ('TEXTCOLOR', (1, 0), (1, -1), self.colors["text"]),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ])
            story.append(param_table)
            story.append(Spacer(1, 18))
        
        # === RESULTADOS ESTADÍSTICOS ===
        story.append(Paragraph("Resultados Estadísticos", heading_style))
        
        stats_data = [
            ["Métrica", "Valor", "Unidad"],
            ["Tasa promedio", f"{analysis_data.get('average_rate', 0):.4f}", self._get_unit(analysis_data.get('resource_type'))],
            ["Valor mínimo", f"{analysis_data.get('min_value', 0):.4f}" if analysis_data.get('min_value') is not None else "N/A", self._get_unit(analysis_data.get('resource_type'))],
            ["Valor máximo", f"{analysis_data.get('max_value', 0):.4f}" if analysis_data.get('max_value') is not None else "N/A", self._get_unit(analysis_data.get('resource_type'))],
            ["Desviación estándar", f"{analysis_data.get('std_dev', 0):.4f}" if analysis_data.get('std_dev') is not None else "N/A", self._get_unit(analysis_data.get('resource_type'))],
            ["Píxeles válidos", f"{analysis_data.get('percentiles', {}).get('count', 'N/A')}", "píxeles"],
        ]
        
        # Percentiles
        percentiles = analysis_data.get("percentiles", {})
        for p_name, p_label in [("p25", "Percentil 25"), ("p50", "Mediana (P50)"), ("p75", "Percentil 75"), ("p90", "Percentil 90"), ("p95", "Percentil 95")]:
            if p_name in percentiles:
                stats_data.append([p_label, f"{percentiles[p_name]:.4f}", self._get_unit(analysis_data.get('resource_type'))])
        
        stats_table = Table(stats_data, colWidths=[5*cm, 5*cm, 4*cm])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.colors["primary"]),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.colors["white"]),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('TEXTCOLOR', (0, 1), (-1, -1), self.colors["text"]),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, self.colors["muted"]),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [self.colors["white"], self.colors["background"]]),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ])
        story.append(stats_table)
        story.append(Spacer(1, 18))
        
        # === LEYENDA ===
        if cfg.get("include_legend", True):
            story.append(Paragraph("Leyenda de Valores", heading_style))
            
            resource_type = analysis_data.get("resource_type")
            legend_text = self._get_legend_text(resource_type)
            story.append(Paragraph(legend_text, body_style))
            story.append(Spacer(1, 18))
        
        # === MAPA (placeholder) ===
        if lot_data.get("geometry"):
            story.append(PageBreak())
            story.append(Paragraph("Mapa del Lote Analizado", heading_style))
            story.append(Paragraph(
                f"El lote <b>{lot_data.get('name')}</b> tiene una superficie de <b>{lot_data.get('area_ha', 0):.2f} ha</b>. "
                f"La geometría analizada corresponde al polígono dibujado sobre el mapa interactivo.",
                body_style
            ))
            story.append(Spacer(1, 12))
            story.append(Paragraph(
                "<i>[Mapa del lote - en implementación completa se incrustaría imagen del mapa con el polígono superpuesto]</i>",
                ParagraphStyle('Italic', parent=body_style, textColor=self.colors["muted"], fontSize=9)
            ))
        
        # === PIE DE PÁGINA ===
        story.append(Spacer(1, 36))
        footer_text = (
            f"Reporte generado automáticamente por GeoForraje 1.0 el {self._format_datetime(datetime.now())}. "
            f"Este documento es generado automáticamente y no requiere firma."
        )
        story.append(Paragraph(footer_text, ParagraphStyle('Footer', parent=body_style, textColor=self.colors["muted"], fontSize=8, alignment=TA_CENTER)))
        
        # Generar PDF
        doc.build(story)
        
        return str(filepath)
    
    def _format_datetime(self, dt: Any) -> str:
        """Formatea datetime para mostrar en reporte."""
        if dt is None:
            return "N/A"
        if isinstance(dt, str):
            try:
                dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
            except:
                return dt
        if isinstance(dt, datetime):
            return dt.strftime("%d/%m/%Y %H:%M")
        return str(dt)
    
    def _status_label(self, status: str) -> str:
        labels = {
            "pending": "Pendiente",
            "processing": "Procesando",
            "completed": "Completado",
            "failed": "Fallido",
        }
        return labels.get(status, status)
    
    def _get_unit(self, resource_type: str) -> str:
        units = {
            "resource_1": "kg/ha",
            "resource_2": "%",
            "resource_3": "índice",
            "resource_4": "%",
        }
        return units.get(resource_type, "")
    
    def _get_legend_text(self, resource_type: str) -> str:
        legends = {
            "resource_1": "Biomasa verde: Cantidad de materia verde por hectárea (kg/ha). Valores altos indican mayor disponibilidad forrajera.",
            "resource_2": "Cobertura suelo: Porcentaje de suelo cubierto por vegetación. 100% = suelo completamente cubierto.",
            "resource_3": "Índice de vegetación (NDVI): Índice normalizado de vegetación. Rango -1 a 1. Valores >0.3 indican vegetación activa.",
            "resource_4": "Humedad suelo: Porcentaje de humedad en el suelo. Valores óptimos dependen del tipo de suelo y cultivo.",
        }
        return legends.get(resource_type, "Leyenda no disponible para este recurso.")


def generate_analysis_report_pdf(
    analysis_data: Dict[str, Any],
    lot_data: Dict[str, Any],
    user_data: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None,
    output_dir: str = "/data/reports",
) -> str:
    """
    Función de conveniencia para generar reporte PDF.
    
    Retorna: path del archivo PDF generado
    """
    generator = ReportGenerator(output_dir)
    return generator.generate_analysis_report(analysis_data, lot_data, user_data, config)
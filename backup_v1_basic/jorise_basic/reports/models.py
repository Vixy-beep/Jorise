from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from core.models import FileUpload
import uuid

class Report(models.Model):
    """Modelo para reportes generados"""
    
    REPORT_TYPES = [
        ('scan_summary', 'Resumen de Escaneo'),
        ('threat_analysis', 'Análisis de Amenazas'),
        ('detailed_report', 'Reporte Detallado'),
        ('executive_summary', 'Resumen Ejecutivo'),
    ]
    
    FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('html', 'HTML'),
        ('json', 'JSON'),
        ('csv', 'CSV'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('generating', 'Generando'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='pdf')
    
    # Relaciones
    file_upload = models.ForeignKey(FileUpload, on_delete=models.CASCADE, related_name='reports')
    generated_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Metadatos del reporte
    created_at = models.DateTimeField(default=timezone.now)
    generated_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Archivos y contenido
    file_path = models.FileField(upload_to='reports/%Y/%m/%d/', null=True, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    content = models.TextField(blank=True)  # Para reportes HTML/JSON
    
    # Configuración del reporte
    include_screenshots = models.BooleanField(default=False)
    include_technical_details = models.BooleanField(default=True)
    include_recommendations = models.BooleanField(default=True)
    
    # Metadatos adicionales
    report_data = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Reporte'
        verbose_name_plural = 'Reportes'
    
    def __str__(self):
        return f"{self.title} - {self.get_format_display()}"
    
    def get_download_filename(self):
        """Genera el nombre del archivo para descarga"""
        timestamp = self.created_at.strftime('%Y%m%d_%H%M%S')
        filename = f"jorise_report_{timestamp}.{self.format}"
        return filename

class ReportTemplate(models.Model):
    """Plantillas para generar reportes"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    report_type = models.CharField(max_length=20, choices=Report.REPORT_TYPES)
    format = models.CharField(max_length=10, choices=Report.FORMAT_CHOICES)
    
    # Contenido de la plantilla
    template_content = models.TextField()
    css_styles = models.TextField(blank=True)  # Para reportes HTML/PDF
    
    # Configuración
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Plantilla de Reporte'
        verbose_name_plural = 'Plantillas de Reportes'
        unique_together = ['report_type', 'format', 'is_default']
    
    def __str__(self):
        return f"{self.name} ({self.get_format_display()})"

class ReportSchedule(models.Model):
    """Programación automática de reportes"""
    
    FREQUENCY_CHOICES = [
        ('daily', 'Diario'),
        ('weekly', 'Semanal'),
        ('monthly', 'Mensual'),
        ('on_detection', 'Al Detectar Amenaza'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Configuración de programación
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE)
    
    # Destinatarios
    email_recipients = models.TextField(help_text="Emails separados por comas")
    
    # Estado
    is_active = models.BooleanField(default=True)
    last_executed = models.DateTimeField(null=True, blank=True)
    next_execution = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        verbose_name = 'Programación de Reporte'
        verbose_name_plural = 'Programaciones de Reportes'
    
    def __str__(self):
        return f"{self.name} ({self.get_frequency_display()})"

class ReportMetric(models.Model):
    """Métricas y estadísticas para reportes"""
    
    METRIC_TYPES = [
        ('total_scans', 'Total de Escaneos'),
        ('threats_detected', 'Amenazas Detectadas'),
        ('clean_files', 'Archivos Limpios'),
        ('scan_duration', 'Duración de Escaneos'),
        ('detection_rate', 'Tasa de Detección'),
    ]
    
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='metrics')
    metric_type = models.CharField(max_length=30, choices=METRIC_TYPES)
    metric_value = models.FloatField()
    metric_unit = models.CharField(max_length=20, blank=True)  # %, segundos, cantidad, etc.
    
    # Periodo de la métrica
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    
    additional_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = 'Métrica de Reporte'
        verbose_name_plural = 'Métricas de Reportes'
    
    def __str__(self):
        return f"{self.get_metric_type_display()}: {self.metric_value} {self.metric_unit}"

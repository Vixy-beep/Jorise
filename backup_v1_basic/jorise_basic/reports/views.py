from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, DetailView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.urls import reverse_lazy
from core.models import FileUpload
from .models import Report, ReportTemplate, ReportSchedule, ReportMetric

class ReportListView(LoginRequiredMixin, ListView):
    """Lista de reportes"""
    model = Report
    template_name = 'reports/report_list.html'
    context_object_name = 'reports'
    paginate_by = 20
    
    def get_queryset(self):
        return Report.objects.filter(generated_by=self.request.user)

class ReportCreateView(LoginRequiredMixin, TemplateView):
    """Crear nuevo reporte"""
    template_name = 'reports/create_report.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['templates'] = ReportTemplate.objects.filter(is_active=True)
        context['files'] = FileUpload.objects.filter(uploaded_by=self.request.user)
        return context

class ReportDetailView(LoginRequiredMixin, DetailView):
    """Detalle de reporte"""
    model = Report
    template_name = 'reports/report_detail.html'
    context_object_name = 'report'
    pk_url_kwarg = 'report_id'
    
    def get_queryset(self):
        return Report.objects.filter(generated_by=self.request.user)

class ReportDownloadView(LoginRequiredMixin, TemplateView):
    """Descargar reporte"""
    
    def get(self, request, report_id):
        report = get_object_or_404(Report, id=report_id, generated_by=request.user)
        
        if report.file_path:
            # Simulación de descarga de archivo
            response = HttpResponse(
                f"Contenido del reporte: {report.title}",
                content_type='application/pdf'
            )
            response['Content-Disposition'] = f'attachment; filename="{report.get_download_filename()}"'
            return response
        else:
            messages.error(request, 'El archivo del reporte no está disponible')
            return redirect('reports:report_detail', report_id=report_id)

class ReportDeleteView(LoginRequiredMixin, DeleteView):
    """Eliminar reporte"""
    model = Report
    template_name = 'reports/report_delete.html'
    pk_url_kwarg = 'report_id'
    success_url = reverse_lazy('reports:report_list')
    
    def get_queryset(self):
        return Report.objects.filter(generated_by=self.request.user)

class GenerateReportView(LoginRequiredMixin, TemplateView):
    """Generar reporte para archivo"""
    template_name = 'reports/generate_report.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        file_id = kwargs.get('file_id')
        context['file'] = get_object_or_404(FileUpload, id=file_id, uploaded_by=self.request.user)
        context['templates'] = ReportTemplate.objects.filter(is_active=True)
        return context

class ReportPreviewView(LoginRequiredMixin, TemplateView):
    """Vista previa de reporte"""
    template_name = 'reports/report_preview.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        report_id = kwargs.get('report_id')
        context['report'] = get_object_or_404(Report, id=report_id, generated_by=self.request.user)
        return context

class TemplateListView(LoginRequiredMixin, ListView):
    """Lista de plantillas"""
    model = ReportTemplate
    template_name = 'reports/template_list.html'
    context_object_name = 'templates'

class TemplateDetailView(LoginRequiredMixin, DetailView):
    """Detalle de plantilla"""
    model = ReportTemplate
    template_name = 'reports/template_detail.html'
    context_object_name = 'template'
    pk_url_kwarg = 'template_id'

class TemplateCreateView(LoginRequiredMixin, TemplateView):
    """Crear plantilla"""
    template_name = 'reports/create_template.html'

class ReportScheduleListView(LoginRequiredMixin, ListView):
    """Lista de reportes programados"""
    model = ReportSchedule
    template_name = 'reports/schedule_list.html'
    context_object_name = 'schedules'
    
    def get_queryset(self):
        return ReportSchedule.objects.filter(created_by=self.request.user)

class ReportScheduleCreateView(LoginRequiredMixin, TemplateView):
    """Crear programación de reporte"""
    template_name = 'reports/create_schedule.html'

class ReportScheduleDetailView(LoginRequiredMixin, DetailView):
    """Detalle de programación"""
    model = ReportSchedule
    template_name = 'reports/schedule_detail.html'
    context_object_name = 'schedule'
    pk_url_kwarg = 'schedule_id'
    
    def get_queryset(self):
        return ReportSchedule.objects.filter(created_by=self.request.user)

# API Views

class GenerateReportAPIView(LoginRequiredMixin, TemplateView):
    """API para generar reporte"""
    
    def post(self, request):
        # Simulación de generación de reporte
        data = {
            'report_id': 'report_123',
            'status': 'generating',
            'message': 'Reporte en proceso de generación'
        }
        return JsonResponse(data)

class ReportStatusAPIView(LoginRequiredMixin, TemplateView):
    """API para estado de reporte"""
    
    def get(self, request, report_id):
        try:
            report = Report.objects.get(id=report_id, generated_by=request.user)
            data = {
                'status': report.status,
                'progress': 100 if report.status == 'completed' else 50,
                'file_size': report.file_size,
                'generated_at': report.generated_at.isoformat() if report.generated_at else None
            }
            return JsonResponse(data)
        except Report.DoesNotExist:
            return JsonResponse({'error': 'Report not found'}, status=404)

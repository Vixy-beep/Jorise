from django.shortcuts import render
from django.http import JsonResponse
from django.views.generic import TemplateView
import os


class DashboardView(TemplateView):
    template_name = 'frontend/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Jorise v1 - Dashboard Básico',
            'version': '1.0 Basic',
            'modules': [
                {'name': 'Core', 'status': 'Activo', 'icon': 'fas fa-cog'},
                {'name': 'Scan', 'status': 'Listo', 'icon': 'fas fa-search'},
                {'name': 'Reports', 'status': 'Disponible', 'icon': 'fas fa-file-alt'},
                {'name': 'Frontend', 'status': 'Online', 'icon': 'fas fa-desktop'},
            ]
        })
        return context


def upload_file(request):
    """Vista simple para upload de archivos"""
    if request.method == 'POST':
        return JsonResponse({
            'status': 'success',
            'message': 'Archivo cargado correctamente (demo v1)',
            'redirect': '/scan/'
        })
    return render(request, 'frontend/upload.html')


def scan_file(request):
    """Vista demo para scan de archivos"""
    return render(request, 'frontend/scan.html', {
        'page_title': 'Escáner de Archivos - Jorise v1',
        'demo_results': {
            'file_name': 'ejemplo_archivo.exe',
            'scan_status': 'Completado',
            'threat_level': 'Medio',
            'detections': 3,
        }
    })


def view_reports(request):
    """Vista demo para reportes"""
    return render(request, 'frontend/reports.html', {
        'page_title': 'Reportes - Jorise v1',
        'recent_scans': [
            {'file': 'documento.pdf', 'status': 'Limpio', 'date': '2025-10-09'},
            {'file': 'aplicacion.exe', 'status': 'Sospechoso', 'date': '2025-10-09'},
            {'file': 'imagen.jpg', 'status': 'Limpio', 'date': '2025-10-08'},
        ]
    })

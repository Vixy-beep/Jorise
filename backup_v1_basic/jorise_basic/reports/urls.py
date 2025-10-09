# Reports app URLs
from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # Report management
    path('', views.ReportListView.as_view(), name='report_list'),
    path('create/', views.ReportCreateView.as_view(), name='create_report'),
    path('<uuid:report_id>/', views.ReportDetailView.as_view(), name='report_detail'),
    path('<uuid:report_id>/download/', views.ReportDownloadView.as_view(), name='download_report'),
    path('<uuid:report_id>/delete/', views.ReportDeleteView.as_view(), name='delete_report'),
    
    # Report generation
    path('generate/<uuid:file_id>/', views.GenerateReportView.as_view(), name='generate_report'),
    path('preview/<uuid:report_id>/', views.ReportPreviewView.as_view(), name='preview_report'),
    
    # Templates
    path('templates/', views.TemplateListView.as_view(), name='template_list'),
    path('templates/<int:template_id>/', views.TemplateDetailView.as_view(), name='template_detail'),
    path('templates/create/', views.TemplateCreateView.as_view(), name='create_template'),
    
    # Scheduled reports
    path('schedule/', views.ReportScheduleListView.as_view(), name='schedule_list'),
    path('schedule/create/', views.ReportScheduleCreateView.as_view(), name='create_schedule'),
    path('schedule/<int:schedule_id>/', views.ReportScheduleDetailView.as_view(), name='schedule_detail'),
    
    # API endpoints
    path('api/generate/', views.GenerateReportAPIView.as_view(), name='api_generate_report'),
    path('api/status/<uuid:report_id>/', views.ReportStatusAPIView.as_view(), name='api_report_status'),
]
from django.urls import path
from . import views

app_name = 'frontend'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('upload/', views.upload_file, name='upload'),
    path('scan/', views.scan_file, name='scan'),
    path('reports/', views.view_reports, name='reports'),
]
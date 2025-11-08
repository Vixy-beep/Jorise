"""
URL Configuration for Jorise v2 - Enterprise SOC
FULL PRODUCTION ROUTES
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.auth_views import login_view, register_view, logout_view
from core.dashboard_views import dashboard_view, subscription_management, settings_view

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Authentication
    path('', login_view, name='login'),
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),
    
    # Dashboard
    path('dashboard/', dashboard_view, name='dashboard'),
    path('subscription/', subscription_management, name='subscription_management'),
    path('settings/', settings_view, name='settings'),
    
    # Module dashboards
    path('siem/', include('siem.urls')),
    path('edr/', include('edr.urls')),
    path('waf/', include('waf.urls')),
    path('sandbox/', include('sandbox.urls')),
    
    # API endpoints
    path('api/soc/<uuid:org_id>/', include('soc.urls')),
    
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

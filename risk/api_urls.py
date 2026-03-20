from django.urls import path
from . import views

urlpatterns = [
    path('case', views.risk_case_api, name='risk_case_api'),
    path('governance-summary', views.risk_governance_summary_api, name='risk_governance_summary_api'),
    path('engine-versions', views.risk_engine_versions_api, name='risk_engine_versions_api'),
    path('engine-versions/register', views.risk_engine_version_register_api, name='risk_engine_version_register_api'),
    path('engine-versions/activate', views.risk_engine_version_activate_api, name='risk_engine_version_activate_api'),
]

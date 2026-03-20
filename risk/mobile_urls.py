from django.urls import path
from . import views

urlpatterns = [
    path('analyze', views.mobile_analyze, name='mobile_analyze'),
]

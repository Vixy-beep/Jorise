from django.urls import path
from . import views

urlpatterns = [
    path("stats/",  views.knowledge_stats,  name="knowledge-stats"),
    path("search/", views.knowledge_search, name="knowledge-search"),
    path("build/",  views.knowledge_build,  name="knowledge-build"),
]

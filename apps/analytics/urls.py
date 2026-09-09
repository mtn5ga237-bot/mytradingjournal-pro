from django.urls import path

from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.stats_view, name='stats'),
    path('ia-coach/', views.ai_coach_view, name='ai_coach'),
]

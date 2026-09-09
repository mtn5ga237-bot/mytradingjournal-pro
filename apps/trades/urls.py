from django.urls import path

from . import views

app_name = 'trades'

urlpatterns = [
    path('', views.TradeListView.as_view(), name='list'),
    path('ajouter/', views.TradeCreateView.as_view(), name='create'),
    path('<int:pk>/modifier/', views.TradeUpdateView.as_view(), name='update'),
    path('<int:pk>/supprimer/', views.TradeDeleteView.as_view(), name='delete'),
    path('export/csv/', views.export_csv_view, name='export_csv'),
]

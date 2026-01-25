from django.urls import path

from . import views

app_name = 'assets'

urlpatterns = [
    path('', views.AssetListView.as_view(), name='list'),
    path('add/', views.AssetCreateView.as_view(), name='create'),
    path('<int:pk>/', views.AssetDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.AssetUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.AssetDeleteView.as_view(), name='delete'),
    # Maintenance schedules
    path('<int:asset_pk>/schedule/add/', views.MaintenanceScheduleCreateView.as_view(), name='schedule_create'),
    path('schedule/<int:pk>/edit/', views.MaintenanceScheduleUpdateView.as_view(), name='schedule_update'),
    path('schedule/<int:pk>/delete/', views.MaintenanceScheduleDeleteView.as_view(), name='schedule_delete'),
    path('schedule/<int:pk>/perform/', views.perform_maintenance, name='perform_maintenance'),
]

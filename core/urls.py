from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('help/', views.HelpView.as_view(), name='help'),
    path('locations/', views.LocationListView.as_view(), name='location_list'),
    path('locations/add/', views.LocationCreateView.as_view(), name='location_create'),
    path('locations/add-ajax/', views.location_create_ajax, name='location_create_ajax'),
    path('locations/<int:pk>/', views.LocationDetailView.as_view(), name='location_detail'),
    path('locations/<int:pk>/edit/', views.LocationUpdateView.as_view(), name='location_update'),
    path('locations/<int:pk>/delete/', views.LocationDeleteView.as_view(), name='location_delete'),
    path('api/assets/', views.asset_search, name='asset_search'),
]

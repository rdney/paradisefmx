from django.urls import path

from . import views

app_name = 'requests'

urlpatterns = [
    path('', views.RequestListView.as_view(), name='list'),
    path('new/', views.CreateRequestView.as_view(), name='create'),
    path('<int:pk>/', views.RequestDetailView.as_view(), name='detail'),
    path('<int:pk>/confirmation/', views.RequestConfirmationView.as_view(), name='confirmation'),
    path('<int:pk>/worklog/', views.add_worklog, name='add_worklog'),
    path('<int:pk>/attachment/', views.add_attachment, name='add_attachment'),
    path('<int:pk>/update/', views.update_request, name='update'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('kosten/', views.CostOverviewView.as_view(), name='costs'),
]

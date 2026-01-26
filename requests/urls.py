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
    path('<int:pk>/update-description/', views.update_description, name='update_description'),
    path('<int:pk>/update-resolution/', views.update_resolution, name='update_resolution'),
    path('<int:pk>/delete/', views.RequestDeleteView.as_view(), name='delete'),
    path('<int:pk>/duplicate/', views.duplicate_request, name='duplicate'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('planner/', views.PlannerView.as_view(), name='planner'),
    path('kosten/', views.CostOverviewView.as_view(), name='costs'),
    path('api/users/', views.user_search, name='user_search'),
    path('notifications/', views.NotificationListView.as_view(), name='notifications'),
    path('notifications/<int:pk>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/read-all/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
]

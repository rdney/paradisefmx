from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('password/change/', views.PasswordChangeView.as_view(), name='password_change'),
    path('password/change/required/', views.PasswordChangeRequiredView.as_view(), name='password_change_required'),

    # Invitations
    path('invitations/', views.InvitationListView.as_view(), name='invitations'),
    path('invitations/new/', views.InvitationCreateView.as_view(), name='invitation_create'),
    path('invitations/<str:token>/', views.InvitationDetailView.as_view(), name='invitation_detail'),
    path('invitations/<str:token>/cancel/', views.CancelInvitationView.as_view(), name='invitation_cancel'),
    path('invite/<str:token>/', views.AcceptInvitationView.as_view(), name='accept_invitation'),
]

from django.contrib.auth import views as auth_views
from django.utils.translation import gettext_lazy as _


class LoginView(auth_views.LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True


class LogoutView(auth_views.LogoutView):
    pass

from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from .models import UserProfile


class LoginView(auth_views.LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        # Check if user must change password
        user = form.get_user()
        try:
            if user.profile.must_change_password:
                return redirect('accounts:password_change_required')
        except UserProfile.DoesNotExist:
            pass
        return response


class LogoutView(auth_views.LogoutView):
    pass


class PasswordChangeRequiredView(LoginRequiredMixin, auth_views.PasswordChangeView):
    """Force password change for new users."""
    template_name = 'accounts/password_change_required.html'
    success_url = reverse_lazy('core:home')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Clear the must_change_password flag
        try:
            profile = self.request.user.profile
            profile.must_change_password = False
            profile.save()
        except UserProfile.DoesNotExist:
            pass
        messages.success(self.request, _('Wachtwoord succesvol gewijzigd.'))
        return response


class PasswordChangeView(LoginRequiredMixin, auth_views.PasswordChangeView):
    """Normal password change."""
    template_name = 'accounts/password_change.html'
    success_url = reverse_lazy('core:home')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('Wachtwoord succesvol gewijzigd.'))
        return response

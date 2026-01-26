from django import forms
from django.contrib import messages
from django.contrib.auth import login, views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import Group, User
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, FormView, ListView, View

from .models import Invitation, UserProfile


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser


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


# Invitation views

class InvitationListView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    """List all invitations."""
    model = Invitation
    template_name = 'accounts/invitation_list.html'
    context_object_name = 'invitations'

    def get_queryset(self):
        return Invitation.objects.select_related('invited_by', 'group', 'accepted_user')


class InvitationForm(forms.ModelForm):
    class Meta:
        model = Invitation
        fields = ['email', 'group', 'message']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control form-control-lg'}),
            'group': forms.Select(attrs={'class': 'form-select form-select-lg'}),
            'message': forms.Textarea(attrs={'class': 'form-control form-control-lg', 'rows': 3}),
        }


class InvitationCreateView(LoginRequiredMixin, StaffRequiredMixin, CreateView):
    """Create a new invitation."""
    model = Invitation
    form_class = InvitationForm
    template_name = 'accounts/invitation_form.html'

    def form_valid(self, form):
        form.instance.invited_by = self.request.user
        self.object = form.save()
        messages.success(self.request, _('Uitnodiging aangemaakt.'))
        return redirect('accounts:invitation_detail', token=self.object.token)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['groups'] = Group.objects.all()
        return ctx


class InvitationDetailView(LoginRequiredMixin, StaffRequiredMixin, View):
    """Show invitation with copyable link."""
    template_name = 'accounts/invitation_detail.html'

    def get(self, request, token):
        invitation = get_object_or_404(Invitation, token=token)
        invite_url = request.build_absolute_uri(
            reverse('accounts:accept_invitation', kwargs={'token': token})
        )
        from django.shortcuts import render
        return render(request, self.template_name, {
            'invitation': invitation,
            'invite_url': invite_url,
        })


class CancelInvitationView(LoginRequiredMixin, StaffRequiredMixin, View):
    """Cancel an invitation."""
    def post(self, request, token):
        invitation = get_object_or_404(Invitation, token=token)
        if invitation.status == Invitation.Status.PENDING:
            invitation.status = Invitation.Status.CANCELLED
            invitation.save()
            messages.success(request, _('Uitnodiging geannuleerd.'))
        return redirect('accounts:invitations')


class AcceptInvitationForm(forms.Form):
    """Form to accept an invitation and create account."""
    username = forms.CharField(
        label=_('Gebruikersnaam'),
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control form-control-lg'})
    )
    first_name = forms.CharField(
        label=_('Voornaam'),
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control form-control-lg'})
    )
    last_name = forms.CharField(
        label=_('Achternaam'),
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control form-control-lg'})
    )
    password1 = forms.CharField(
        label=_('Wachtwoord'),
        widget=forms.PasswordInput(attrs={'class': 'form-control form-control-lg'})
    )
    password2 = forms.CharField(
        label=_('Wachtwoord bevestigen'),
        widget=forms.PasswordInput(attrs={'class': 'form-control form-control-lg'})
    )

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(_('Deze gebruikersnaam is al in gebruik.'))
        return username

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError(_('Wachtwoorden komen niet overeen.'))
        return cleaned_data


class AcceptInvitationView(FormView):
    """Accept an invitation and create a user account."""
    template_name = 'accounts/accept_invitation.html'
    form_class = AcceptInvitationForm
    success_url = reverse_lazy('core:home')

    def dispatch(self, request, *args, **kwargs):
        self.invitation = get_object_or_404(Invitation, token=kwargs['token'])
        if not self.invitation.is_valid:
            messages.error(request, _('Deze uitnodiging is niet meer geldig.'))
            return redirect('accounts:login')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['invitation'] = self.invitation
        return ctx

    def get_initial(self):
        initial = super().get_initial()
        # Pre-fill email as username suggestion
        email = self.invitation.email
        initial['username'] = email.split('@')[0]
        return initial

    def form_valid(self, form):
        # Create user
        user = User.objects.create_user(
            username=form.cleaned_data['username'],
            email=self.invitation.email,
            password=form.cleaned_data['password1'],
            first_name=form.cleaned_data['first_name'],
            last_name=form.cleaned_data.get('last_name', ''),
        )

        # Add to group if specified
        if self.invitation.group:
            user.groups.add(self.invitation.group)

        # Mark invitation as accepted
        self.invitation.status = Invitation.Status.ACCEPTED
        self.invitation.accepted_at = timezone.now()
        self.invitation.accepted_user = user
        self.invitation.save()

        # Log them in
        login(self.request, user)
        messages.success(self.request, _('Welkom! Uw account is aangemaakt.'))
        return super().form_valid(form)

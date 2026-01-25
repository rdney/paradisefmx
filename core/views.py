from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count, Q
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from .forms import AssetForm, LocationForm
from .models import Asset, Location


class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser


class HomeView(TemplateView):
    """Landing page with main actions."""
    template_name = 'core/home.html'


class HelpView(TemplateView):
    """Help page / user manual."""
    template_name = 'core/help.html'


class AssetListView(LoginRequiredMixin, ListView):
    """List all assets with filters."""
    model = Asset
    template_name = 'core/asset_list.html'
    context_object_name = 'assets'
    paginate_by = 25

    def get_queryset(self):
        qs = Asset.objects.select_related('location')

        # Filters
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)

        category = self.request.GET.get('category')
        if category:
            qs = qs.filter(category=category)

        criticality = self.request.GET.get('criticality')
        if criticality:
            qs = qs.filter(criticality=criticality)

        location = self.request.GET.get('location')
        if location:
            qs = qs.filter(location_id=location)

        search = self.request.GET.get('q')
        if search:
            qs = qs.filter(
                Q(asset_tag__icontains=search) |
                Q(name__icontains=search) |
                Q(manufacturer__icontains=search) |
                Q(model__icontains=search)
            )

        monument = self.request.GET.get('monument')
        if monument == '1':
            qs = qs.filter(is_monument=True)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['locations'] = Location.objects.all()
        ctx['status_choices'] = Asset.Status.choices
        ctx['category_choices'] = Asset.Category.choices
        ctx['criticality_choices'] = Asset.Criticality.choices
        ctx['current_filters'] = {
            'status': self.request.GET.get('status', ''),
            'category': self.request.GET.get('category', ''),
            'criticality': self.request.GET.get('criticality', ''),
            'location': self.request.GET.get('location', ''),
            'q': self.request.GET.get('q', ''),
            'monument': self.request.GET.get('monument', ''),
        }
        return ctx


class AssetDetailView(LoginRequiredMixin, DetailView):
    """Asset detail with related repair requests."""
    model = Asset
    template_name = 'core/asset_detail.html'
    context_object_name = 'asset'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['repair_requests'] = self.object.repair_requests.select_related(
            'location', 'assigned_to'
        ).order_by('-created_at')[:10]
        return ctx


# Location Management
class LocationListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = Location
    template_name = 'core/location_list.html'
    context_object_name = 'locations'

    def get_queryset(self):
        return Location.objects.select_related('parent').order_by('name')


class LocationCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Location
    form_class = LocationForm
    template_name = 'core/location_form.html'
    success_url = reverse_lazy('core:location_list')

    def form_valid(self, form):
        messages.success(self.request, _('Locatie toegevoegd.'))
        return super().form_valid(form)


class LocationUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Location
    form_class = LocationForm
    template_name = 'core/location_form.html'
    success_url = reverse_lazy('core:location_list')

    def form_valid(self, form):
        messages.success(self.request, _('Locatie bijgewerkt.'))
        return super().form_valid(form)


class LocationDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = Location
    template_name = 'core/location_confirm_delete.html'
    success_url = reverse_lazy('core:location_list')

    def form_valid(self, form):
        messages.success(self.request, _('Locatie verwijderd.'))
        return super().form_valid(form)


# Asset Management
class AssetCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Asset
    form_class = AssetForm
    template_name = 'core/asset_form.html'
    success_url = reverse_lazy('assets:list')

    def form_valid(self, form):
        messages.success(self.request, _('Object toegevoegd.'))
        return super().form_valid(form)


class AssetUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Asset
    form_class = AssetForm
    template_name = 'core/asset_form.html'
    success_url = reverse_lazy('assets:list')

    def form_valid(self, form):
        messages.success(self.request, _('Object bijgewerkt.'))
        return super().form_valid(form)


class AssetDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = Asset
    template_name = 'core/asset_confirm_delete.html'
    success_url = reverse_lazy('assets:list')

    def form_valid(self, form):
        messages.success(self.request, _('Object verwijderd.'))
        return super().form_valid(form)

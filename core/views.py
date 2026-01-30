import json
from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from .forms import AssetForm, LocationForm, MaintenanceScheduleForm
from .models import Asset, Category, Location, MaintenanceSchedule


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
        qs = Asset.objects.select_related('location', 'category')

        # Filters
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)

        category = self.request.GET.get('category')
        if category:
            qs = qs.filter(category_id=category)

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
        ctx['categories'] = Category.objects.all()
        ctx['criticality_choices'] = Asset.Criticality.choices
        ctx['current_filters'] = {
            'status': self.request.GET.get('status', ''),
            'category': self.request.GET.get('category', ''),
            'criticality': self.request.GET.get('criticality', ''),
            'location': self.request.GET.get('location', ''),
            'q': self.request.GET.get('q', ''),
            'monument': self.request.GET.get('monument', ''),
            'view': self.request.GET.get('view', ''),
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
        ctx['maintenance_schedules'] = self.object.maintenance_schedules.all()
        return ctx


# Location Management
class LocationListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = Location
    template_name = 'core/location_list.html'
    context_object_name = 'locations'

    def get_queryset(self):
        return Location.objects.select_related('parent').order_by('name')


class LocationDetailView(LoginRequiredMixin, DetailView):
    """Location detail with related assets and requests."""
    model = Location
    template_name = 'core/location_detail.html'
    context_object_name = 'location'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['assets'] = self.object.assets.all()
        ctx['repair_requests'] = self.object.repair_requests.select_related(
            'assigned_to'
        ).order_by('-created_at')[:20]
        ctx['children'] = self.object.children.all()
        return ctx


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

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        location = self.object
        ctx['asset_count'] = location.assets.count()
        ctx['request_count'] = location.repair_requests.count()
        ctx['child_count'] = location.children.count()
        ctx['can_delete'] = (ctx['asset_count'] == 0 and ctx['request_count'] == 0 and ctx['child_count'] == 0)
        return ctx

    def form_valid(self, form):
        location = self.object
        # Check for related objects
        if location.assets.exists():
            messages.error(self.request, _('Kan niet verwijderen: er zijn objecten gekoppeld aan deze locatie.'))
            return redirect('core:location_list')
        if location.repair_requests.exists():
            messages.error(self.request, _('Kan niet verwijderen: er zijn verzoeken gekoppeld aan deze locatie.'))
            return redirect('core:location_list')
        if location.children.exists():
            messages.error(self.request, _('Kan niet verwijderen: deze locatie heeft sublocaties.'))
            return redirect('core:location_list')

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


@login_required
def record_maintenance(request, pk):
    """Record that maintenance was performed on an asset."""
    asset = get_object_or_404(Asset, pk=pk)

    if request.method == 'POST':
        asset.last_maintenance_date = date.today()
        asset.save(update_fields=['last_maintenance_date'])
        messages.success(request, _('Onderhoud geregistreerd.'))

    return redirect('assets:detail', pk=pk)


@login_required
@require_POST
def location_create_ajax(request):
    """Create a location via AJAX."""
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        parent_id = data.get('parent')

        if not name:
            return JsonResponse({'error': 'Name is required'}, status=400)

        parent = None
        if parent_id:
            parent = Location.objects.filter(pk=parent_id).first()

        location = Location.objects.create(name=name, parent=parent)

        # Return full path name for display
        display_name = str(location)

        return JsonResponse({
            'id': location.pk,
            'name': display_name,
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# Maintenance Schedule views
class MaintenanceScheduleCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = MaintenanceSchedule
    form_class = MaintenanceScheduleForm
    template_name = 'core/maintenance_schedule_form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['asset'] = get_object_or_404(Asset, pk=self.kwargs['asset_pk'])
        return ctx

    def form_valid(self, form):
        form.instance.asset = get_object_or_404(Asset, pk=self.kwargs['asset_pk'])
        messages.success(self.request, _('Onderhoudsschema toegevoegd.'))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('assets:detail', kwargs={'pk': self.kwargs['asset_pk']})


class MaintenanceScheduleUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = MaintenanceSchedule
    form_class = MaintenanceScheduleForm
    template_name = 'core/maintenance_schedule_form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['asset'] = self.object.asset
        return ctx

    def form_valid(self, form):
        messages.success(self.request, _('Onderhoudsschema bijgewerkt.'))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('assets:detail', kwargs={'pk': self.object.asset.pk})


class MaintenanceScheduleDeleteView(LoginRequiredMixin, AdminRequiredMixin, DeleteView):
    model = MaintenanceSchedule
    template_name = 'core/maintenance_schedule_confirm_delete.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['asset'] = self.object.asset
        return ctx

    def form_valid(self, form):
        asset_pk = self.object.asset.pk
        messages.success(self.request, _('Onderhoudsschema verwijderd.'))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('assets:detail', kwargs={'pk': self.object.asset.pk})


@login_required
@require_POST
def perform_maintenance(request, pk):
    """Record that a scheduled maintenance was performed."""
    schedule = get_object_or_404(MaintenanceSchedule, pk=pk)
    schedule.last_performed = date.today()
    schedule.save(update_fields=['last_performed'])
    messages.success(request, _('Onderhoud geregistreerd voor: %(name)s') % {'name': schedule.name})
    return redirect('assets:detail', pk=schedule.asset.pk)


def asset_search(request):
    """API endpoint to search assets for autocomplete."""
    q = request.GET.get('q', '').strip()
    location_id = request.GET.get('location')

    if len(q) < 1:
        return JsonResponse({'assets': []})

    assets = Asset.objects.filter(
        Q(asset_tag__icontains=q) |
        Q(name__icontains=q) |
        Q(manufacturer__icontains=q) |
        Q(model__icontains=q)
    ).select_related('location')

    # Filter by location if provided
    if location_id:
        assets = assets.filter(location_id=location_id)

    assets = assets[:15]

    return JsonResponse({
        'assets': [
            {
                'id': a.pk,
                'name': a.name,
                'asset_tag': a.asset_tag,
                'location': str(a.location) if a.location else '',
                'display': f"{a.asset_tag} - {a.name}" if a.asset_tag else a.name,
            }
            for a in assets
        ]
    })

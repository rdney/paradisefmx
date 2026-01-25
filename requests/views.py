import calendar
from datetime import date

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.mail import send_mail
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.generic import CreateView, DetailView, ListView, TemplateView, UpdateView

from .forms import AttachmentForm, RepairRequestForm, TriageForm, WorkLogForm
from .models import Attachment, RepairRequest, WorkLog

User = get_user_model()


class CreateRequestView(CreateView):
    """Public form to submit a repair request."""
    model = RepairRequest
    form_class = RepairRequestForm
    template_name = 'requests/create.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user if self.request.user.is_authenticated else None
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)

        # Handle uploaded photos
        files = self.request.FILES.getlist('photos')
        for f in files:
            # Validate file size
            if f.size <= 10 * 1024 * 1024:  # 10MB
                Attachment.objects.create(
                    repair_request=self.object,
                    file=f,
                    uploaded_by=self.request.user if self.request.user.is_authenticated else None,
                )

        # Create initial work log
        WorkLog.objects.create(
            repair_request=self.object,
            entry_type=WorkLog.EntryType.NOTE,
            note=_('Reparatieverzoek ingediend'),
            author=self.request.user if self.request.user.is_authenticated else None,
        )

        # Send notification email
        self.send_notification_email()

        messages.success(
            self.request,
            _('Uw verzoek is ingediend. Het werkbonnummer is #%(id)s.') % {'id': self.object.id}
        )
        return response

    def get_success_url(self):
        return reverse('requests:confirmation', kwargs={'pk': self.object.pk})

    def send_notification_email(self):
        """Send email notification to facilities inbox."""
        try:
            subject = _('Nieuw reparatieverzoek #%(id)s: %(title)s') % {
                'id': self.object.id,
                'title': self.object.title,
            }
            message = _(
                'Er is een nieuw reparatieverzoek ingediend.\n\n'
                'Werkbonnummer: #%(id)s\n'
                'Titel: %(title)s\n'
                'Locatie: %(location)s\n'
                'Prioriteit: %(priority)s\n'
                'Melder: %(requester)s\n\n'
                '%(description)s'
            ) % {
                'id': self.object.id,
                'title': self.object.title,
                'location': self.object.location,
                'priority': self.object.get_priority_display(),
                'requester': self.object.requester_name,
                'description': self.object.description,
            }
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [settings.FACILITIES_INBOX_EMAIL],
                fail_silently=True,
            )
        except Exception:
            pass  # Don't fail the request if email fails


class RequestConfirmationView(DetailView):
    """Confirmation page after submitting a request."""
    model = RepairRequest
    template_name = 'requests/confirmation.html'
    context_object_name = 'request'


class RequestListView(LoginRequiredMixin, ListView):
    """List repair requests (all for staff, own for requesters)."""
    model = RepairRequest
    template_name = 'requests/list.html'
    context_object_name = 'requests'
    paginate_by = 25

    def get_queryset(self):
        user = self.request.user
        qs = RepairRequest.objects.select_related('location', 'asset', 'assigned_to')

        # Non-staff users only see their own requests
        if not user.is_staff and not user.groups.filter(name='Facilitair').exists():
            qs = qs.filter(
                Q(requester_user=user) |
                Q(requester_email=user.email)
            )

        # Filters
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)

        priority = self.request.GET.get('priority')
        if priority:
            qs = qs.filter(priority=priority)

        location = self.request.GET.get('location')
        if location:
            qs = qs.filter(location_id=location)

        assigned = self.request.GET.get('assigned')
        if assigned == 'me':
            qs = qs.filter(assigned_to=user)
        elif assigned == 'unassigned':
            qs = qs.filter(assigned_to__isnull=True)

        search = self.request.GET.get('q')
        if search:
            qs = qs.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(requester_name__icontains=search)
            )

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from core.models import Location
        ctx['locations'] = Location.objects.all()
        ctx['status_choices'] = RepairRequest.Status.choices
        ctx['priority_choices'] = RepairRequest.Priority.choices
        ctx['current_filters'] = {
            'status': self.request.GET.get('status', ''),
            'priority': self.request.GET.get('priority', ''),
            'location': self.request.GET.get('location', ''),
            'assigned': self.request.GET.get('assigned', ''),
            'q': self.request.GET.get('q', ''),
        }
        return ctx


class DashboardView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Facilities dashboard / triage inbox."""
    model = RepairRequest
    template_name = 'requests/dashboard.html'
    context_object_name = 'requests'

    def test_func(self):
        return (
            self.request.user.is_staff or
            self.request.user.groups.filter(name__in=['Facilitair', 'Beheerders']).exists()
        )

    def get_queryset(self):
        return RepairRequest.objects.select_related(
            'location', 'asset', 'assigned_to'
        ).exclude(
            status__in=[RepairRequest.Status.COMPLETED, RepairRequest.Status.CLOSED]
        ).order_by(
            # Urgent first, then by created date
            '-priority', 'created_at'
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = RepairRequest.objects.all()

        ctx['counts'] = {
            'new': qs.filter(status=RepairRequest.Status.NEW).count(),
            'triaged': qs.filter(status=RepairRequest.Status.TRIAGED).count(),
            'in_progress': qs.filter(status=RepairRequest.Status.IN_PROGRESS).count(),
            'waiting': qs.filter(status=RepairRequest.Status.WAITING).count(),
            'overdue': qs.filter(
                due_date__lt=timezone.now().date()
            ).exclude(
                status__in=[RepairRequest.Status.COMPLETED, RepairRequest.Status.CLOSED]
            ).count(),
        }
        ctx['staff_users'] = User.objects.filter(
            Q(is_staff=True) | Q(groups__name='Facilitair')
        ).distinct()
        return ctx


class RequestDetailView(LoginRequiredMixin, DetailView):
    """Detail view for a repair request."""
    model = RepairRequest
    template_name = 'requests/detail.html'
    context_object_name = 'request'

    def get_queryset(self):
        user = self.request.user
        qs = RepairRequest.objects.select_related('location', 'asset', 'assigned_to', 'triaged_by')

        # Non-staff users only see their own requests
        if not user.is_staff and not user.groups.filter(name='Facilitair').exists():
            qs = qs.filter(
                Q(requester_user=user) |
                Q(requester_email=user.email)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['work_logs'] = self.object.work_logs.select_related('author').order_by('-created_at')
        ctx['attachments'] = self.object.attachments.all()
        ctx['worklog_form'] = WorkLogForm()
        ctx['attachment_form'] = AttachmentForm()

        # Triage form for staff
        if self.request.user.is_staff or self.request.user.groups.filter(name='Facilitair').exists():
            ctx['triage_form'] = TriageForm(instance=self.object)
            ctx['staff_users'] = User.objects.filter(
                Q(is_staff=True) | Q(groups__name='Facilitair')
            ).distinct()

        return ctx


@login_required
def add_worklog(request, pk):
    """Add a work log entry to a request."""
    repair_request = get_object_or_404(RepairRequest, pk=pk)

    # Permission check
    user = request.user
    is_staff = user.is_staff or user.groups.filter(name='Facilitair').exists()
    is_owner = (
        repair_request.requester_user == user or
        repair_request.requester_email == user.email
    )

    if not is_staff and not is_owner:
        messages.error(request, _('U heeft geen toegang tot dit verzoek.'))
        return redirect('requests:list')

    if request.method == 'POST':
        form = WorkLogForm(request.POST)
        if form.is_valid():
            worklog = form.save(commit=False)
            worklog.repair_request = repair_request
            worklog.author = user
            worklog.entry_type = WorkLog.EntryType.NOTE
            if worklog.minutes_spent:
                worklog.entry_type = WorkLog.EntryType.TIME_SPENT
            worklog.save()
            messages.success(request, _('Notitie toegevoegd.'))

    return redirect('requests:detail', pk=pk)


@login_required
def add_attachment(request, pk):
    """Add an attachment to a request."""
    repair_request = get_object_or_404(RepairRequest, pk=pk)

    # Permission check
    user = request.user
    is_staff = user.is_staff or user.groups.filter(name='Facilitair').exists()
    is_owner = (
        repair_request.requester_user == user or
        repair_request.requester_email == user.email
    )

    if not is_staff and not is_owner:
        messages.error(request, _('U heeft geen toegang tot dit verzoek.'))
        return redirect('requests:list')

    if request.method == 'POST':
        form = AttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            attachment = form.save(commit=False)
            attachment.repair_request = repair_request
            attachment.uploaded_by = user
            attachment.save()
            messages.success(request, _('Bijlage geüpload.'))

    return redirect('requests:detail', pk=pk)


@login_required
def update_request(request, pk):
    """Update request status/assignment (staff only)."""
    repair_request = get_object_or_404(RepairRequest, pk=pk)

    # Permission check
    user = request.user
    if not user.is_staff and not user.groups.filter(name='Facilitair').exists():
        messages.error(request, _('U heeft geen toegang tot deze actie.'))
        return redirect('requests:detail', pk=pk)

    if request.method == 'POST':
        old_status = repair_request.status
        old_assigned = repair_request.assigned_to

        form = TriageForm(request.POST, instance=repair_request)
        if form.is_valid():
            repair_request = form.save(commit=False)

            # Track changes
            changes = []

            if old_status != repair_request.status:
                changes.append(
                    _('Status gewijzigd van %(old)s naar %(new)s') % {
                        'old': dict(RepairRequest.Status.choices).get(old_status),
                        'new': repair_request.get_status_display(),
                    }
                )
                # Set triaged_by on first triage
                if repair_request.status == RepairRequest.Status.TRIAGED and not repair_request.triaged_by:
                    repair_request.triaged_by = user

            if old_assigned != repair_request.assigned_to:
                if repair_request.assigned_to:
                    changes.append(
                        _('Toegewezen aan %(user)s') % {'user': repair_request.assigned_to.get_full_name() or repair_request.assigned_to.username}
                    )
                else:
                    changes.append(_('Toewijzing verwijderd'))

            repair_request.save()

            # Create work log entries for changes
            for change in changes:
                WorkLog.objects.create(
                    repair_request=repair_request,
                    author=user,
                    entry_type=WorkLog.EntryType.STATUS_CHANGE if 'Status' in change else WorkLog.EntryType.ASSIGNMENT,
                    note=change,
                )

            messages.success(request, _('Verzoek bijgewerkt.'))

    return redirect('requests:detail', pk=pk)


class PlannerView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Monthly planner view showing scheduled repairs."""
    template_name = 'requests/planner.html'

    def test_func(self):
        return (
            self.request.user.is_staff or
            self.request.user.groups.filter(name__in=['Facilitair', 'Beheerders']).exists()
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # Get year and month from query params or use current
        today = timezone.now().date()
        try:
            year = int(self.request.GET.get('year', today.year))
            month = int(self.request.GET.get('month', today.month))
        except (ValueError, TypeError):
            year, month = today.year, today.month

        # Clamp values
        if month < 1:
            month = 12
            year -= 1
        elif month > 12:
            month = 1
            year += 1

        # Get calendar data
        cal = calendar.Calendar(firstweekday=0)  # Monday first
        month_days = cal.monthdayscalendar(year, month)

        # Get requests with due_date in this month
        first_day = date(year, month, 1)
        last_day = date(year, month, calendar.monthrange(year, month)[1])

        requests_by_day = {}
        requests = RepairRequest.objects.filter(
            due_date__gte=first_day,
            due_date__lte=last_day
        ).exclude(
            status__in=[RepairRequest.Status.CLOSED]
        ).select_related('location', 'assigned_to').order_by('due_date', 'priority')

        for req in requests:
            day = req.due_date.day
            if day not in requests_by_day:
                requests_by_day[day] = []
            requests_by_day[day].append(req)

        # Build calendar weeks
        weeks = []
        for week in month_days:
            week_data = []
            for day in week:
                if day == 0:
                    week_data.append({'day': 0, 'requests': []})
                else:
                    week_data.append({
                        'day': day,
                        'requests': requests_by_day.get(day, []),
                        'is_today': day == today.day and month == today.month and year == today.year,
                    })
            weeks.append(week_data)

        # Navigation
        prev_month = month - 1
        prev_year = year
        if prev_month < 1:
            prev_month = 12
            prev_year -= 1

        next_month = month + 1
        next_year = year
        if next_month > 12:
            next_month = 1
            next_year += 1

        ctx['year'] = year
        ctx['month'] = month
        ctx['month_name'] = calendar.month_name[month]
        ctx['weeks'] = weeks
        ctx['weekdays'] = ['Ma', 'Di', 'Wo', 'Do', 'Vr', 'Za', 'Zo']
        ctx['prev_year'] = prev_year
        ctx['prev_month'] = prev_month
        ctx['next_year'] = next_year
        ctx['next_month'] = next_month
        ctx['today'] = today

        return ctx

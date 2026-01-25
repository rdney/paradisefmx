from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from core.models import Location

from .models import RepairRequest, WorkLog

User = get_user_model()


class RepairRequestModelTest(TestCase):
    def setUp(self):
        self.location = Location.objects.create(name='Kerkzaal')

    def test_create_request(self):
        req = RepairRequest.objects.create(
            title='Lamp kapot',
            description='De lamp in de kerkzaal doet het niet meer.',
            location=self.location,
            requester_name='Jan Jansen',
            requester_email='jan@example.com'
        )
        self.assertEqual(req.status, RepairRequest.Status.NEW)
        self.assertEqual(req.priority, RepairRequest.Priority.NORMAL)
        self.assertIn('Lamp kapot', str(req))

    def test_status_change_sets_closed_at(self):
        req = RepairRequest.objects.create(
            title='Test',
            description='Test',
            location=self.location,
            requester_name='Test'
        )
        self.assertIsNone(req.closed_at)

        req.status = RepairRequest.Status.CLOSED
        req.save()
        req.refresh_from_db()

        self.assertIsNotNone(req.closed_at)


class RepairRequestViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.location = Location.objects.create(name='Kerkzaal')

    def test_create_request_anonymous(self):
        """Anonymous users can submit requests."""
        response = self.client.post(reverse('requests:create'), {
            'title': 'Lamp kapot',
            'description': 'De lamp doet het niet.',
            'location': self.location.pk,
            'priority': 'normal',
            'requester_name': 'Jan Jansen',
        })
        self.assertEqual(response.status_code, 302)  # Redirect to confirmation

        req = RepairRequest.objects.first()
        self.assertIsNotNone(req)
        self.assertEqual(req.title, 'Lamp kapot')
        self.assertEqual(req.status, RepairRequest.Status.NEW)

        # Work log should be created
        self.assertEqual(req.work_logs.count(), 1)

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('requests:dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirect to login


class PermissionTest(TestCase):
    def setUp(self):
        self.location = Location.objects.create(name='Kerkzaal')
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.staff_user = User.objects.create_user(
            username='staffuser',
            password='testpass123',
            is_staff=True
        )

    def test_regular_user_sees_own_requests(self):
        # Create request by user
        req = RepairRequest.objects.create(
            title='My request',
            description='Test',
            location=self.location,
            requester_name='Test',
            requester_user=self.user
        )

        # Create request by someone else
        other_req = RepairRequest.objects.create(
            title='Other request',
            description='Test',
            location=self.location,
            requester_name='Other Person',
            requester_email='other@example.com'
        )

        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('requests:list'))

        self.assertContains(response, 'My request')
        self.assertNotContains(response, 'Other request')

    def test_staff_sees_all_requests(self):
        RepairRequest.objects.create(
            title='Request 1',
            description='Test',
            location=self.location,
            requester_name='Person 1'
        )
        RepairRequest.objects.create(
            title='Request 2',
            description='Test',
            location=self.location,
            requester_name='Person 2'
        )

        self.client.login(username='staffuser', password='testpass123')
        response = self.client.get(reverse('requests:list'))

        self.assertContains(response, 'Request 1')
        self.assertContains(response, 'Request 2')


class WorkLogTest(TestCase):
    def setUp(self):
        self.location = Location.objects.create(name='Kerkzaal')
        self.staff_user = User.objects.create_user(
            username='staffuser',
            password='testpass123',
            is_staff=True
        )
        self.request = RepairRequest.objects.create(
            title='Test',
            description='Test',
            location=self.location,
            requester_name='Test'
        )

    def test_status_change_creates_worklog(self):
        self.client.login(username='staffuser', password='testpass123')

        initial_count = self.request.work_logs.count()

        response = self.client.post(
            reverse('requests:update', kwargs={'pk': self.request.pk}),
            {
                'status': RepairRequest.Status.TRIAGED,
                'priority': self.request.priority,
            }
        )

        self.request.refresh_from_db()
        self.assertEqual(self.request.status, RepairRequest.Status.TRIAGED)
        self.assertEqual(self.request.work_logs.count(), initial_count + 1)


class LanguageSwitchTest(TestCase):
    def test_language_switch(self):
        # Default is Dutch
        response = self.client.get('/')
        self.assertContains(response, 'Facilitair beheer')

        # Switch to English - check we can access English URL
        response = self.client.get('/en/')
        self.assertEqual(response.status_code, 200)
        # Language switcher should show EN is active
        self.assertContains(response, 'EN')

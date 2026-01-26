from django.core.management.base import BaseCommand

from requests.models import WorkLog


class Command(BaseCommand):
    help = 'Delete all work log entries'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm deletion without prompt',
        )

    def handle(self, *args, **options):
        count = WorkLog.objects.count()

        if count == 0:
            self.stdout.write('No work logs to delete.')
            return

        if not options['confirm']:
            self.stdout.write(f'This will delete {count} work log entries.')
            self.stdout.write('Run with --confirm to proceed.')
            return

        WorkLog.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'Deleted {count} work log entries.'))

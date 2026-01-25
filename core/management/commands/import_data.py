"""
Management command to import bulk data from YAML files.

Usage:
    python manage.py import_data --locations locations.yaml
    python manage.py import_data --assets assets.yaml
    python manage.py import_data --requests requests.yaml
    python manage.py import_data --all data/

Example YAML formats:

locations.yaml:
---
- name: Kerkzaal
  notes: Hoofdzaal voor diensten
- name: Consistorie
  parent: Kerkzaal
  notes: Vergaderruimte

assets.yaml:
---
- name: CV-ketel
  category: hvac
  location: Kelder
  status: operational
  criticality: high
  manufacturer: Remeha
  model: Calenta 40c

requests.yaml:
---
- title: Lamp kapot
  description: Lamp in consistorie doet het niet meer
  location: Consistorie
  priority: normal
  requester_name: Jan de Vries
  requester_email: jan@example.com

accounts.yaml:
---
- username: arjen
  email: arjen@example.com
  first_name: Arjen
  last_name: Oosterlee
  password: Welcome123!
  is_staff: true
"""
import os
from pathlib import Path

import yaml
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from accounts.models import UserProfile
from core.models import Asset, Location
from requests.models import RepairRequest

User = get_user_model()


class Command(BaseCommand):
    help = 'Import bulk data from YAML files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--locations',
            type=str,
            help='Path to locations YAML file'
        )
        parser.add_argument(
            '--assets',
            type=str,
            help='Path to assets YAML file'
        )
        parser.add_argument(
            '--requests',
            type=str,
            help='Path to repair requests YAML file'
        )
        parser.add_argument(
            '--accounts',
            type=str,
            help='Path to accounts YAML file'
        )
        parser.add_argument(
            '--all',
            type=str,
            help='Path to directory containing locations.yaml, assets.yaml, requests.yaml, accounts.yaml'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Parse and validate without saving'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if options['all']:
            base_path = Path(options['all'])
            if not base_path.is_dir():
                raise CommandError(f"Directory not found: {base_path}")

            locations_file = base_path / 'locations.yaml'
            assets_file = base_path / 'assets.yaml'
            requests_file = base_path / 'requests.yaml'
            accounts_file = base_path / 'accounts.yaml'

            if accounts_file.exists():
                self.import_accounts(accounts_file, dry_run)
            if locations_file.exists():
                self.import_locations(locations_file, dry_run)
            if assets_file.exists():
                self.import_assets(assets_file, dry_run)
            if requests_file.exists():
                self.import_requests(requests_file, dry_run)
        else:
            if options['accounts']:
                self.import_accounts(Path(options['accounts']), dry_run)
            if options['locations']:
                self.import_locations(Path(options['locations']), dry_run)
            if options['assets']:
                self.import_assets(Path(options['assets']), dry_run)
            if options['requests']:
                self.import_requests(Path(options['requests']), dry_run)

    def load_yaml(self, path):
        if not path.exists():
            raise CommandError(f"File not found: {path}")
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or []

    @transaction.atomic
    def import_locations(self, path, dry_run=False):
        data = self.load_yaml(path)
        self.stdout.write(f"Importing {len(data)} locations from {path}")

        # Two-pass: first create all, then set parents
        created = {}
        for item in data:
            name = item.get('name')
            if not name:
                self.stderr.write(f"  Skipping location without name: {item}")
                continue

            if dry_run:
                self.stdout.write(f"  [DRY-RUN] Would create location: {name}")
                continue

            loc, was_created = Location.objects.get_or_create(
                name=name,
                defaults={'notes': item.get('notes', '')}
            )
            created[name] = loc
            status = "Created" if was_created else "Exists"
            self.stdout.write(f"  {status}: {name}")

        # Second pass: set parents
        if not dry_run:
            for item in data:
                parent_name = item.get('parent')
                if parent_name and item.get('name') in created:
                    parent = Location.objects.filter(name=parent_name).first()
                    if parent:
                        loc = created[item['name']]
                        loc.parent = parent
                        loc.save()
                        self.stdout.write(f"  Set parent {parent_name} for {item['name']}")

        self.stdout.write(self.style.SUCCESS(f"Locations import complete"))

    @transaction.atomic
    def import_assets(self, path, dry_run=False):
        data = self.load_yaml(path)
        self.stdout.write(f"Importing {len(data)} assets from {path}")

        for item in data:
            name = item.get('name')
            if not name:
                self.stderr.write(f"  Skipping asset without name: {item}")
                continue

            if dry_run:
                self.stdout.write(f"  [DRY-RUN] Would create asset: {name}")
                continue

            # Find location
            location = None
            if item.get('location'):
                location = Location.objects.filter(name=item['location']).first()
                if not location:
                    self.stderr.write(f"  Location not found: {item['location']}")

            defaults = {
                'category': item.get('category', 'other'),
                'location': location,
                'status': item.get('status', 'operational'),
                'criticality': item.get('criticality', 'medium'),
                'manufacturer': item.get('manufacturer', ''),
                'model': item.get('model', ''),
                'serial_number': item.get('serial_number', ''),
                'description': item.get('description', ''),
            }

            asset, was_created = Asset.objects.get_or_create(
                name=name,
                defaults=defaults
            )
            status = "Created" if was_created else "Exists"
            self.stdout.write(f"  {status}: {name} ({asset.asset_tag})")

        self.stdout.write(self.style.SUCCESS(f"Assets import complete"))

    @transaction.atomic
    def import_requests(self, path, dry_run=False):
        data = self.load_yaml(path)
        self.stdout.write(f"Importing {len(data)} requests from {path}")

        for item in data:
            title = item.get('title')
            if not title:
                self.stderr.write(f"  Skipping request without title: {item}")
                continue

            if dry_run:
                self.stdout.write(f"  [DRY-RUN] Would create request: {title}")
                continue

            # Find location
            location = None
            if item.get('location'):
                location = Location.objects.filter(name=item['location']).first()
                if not location:
                    self.stderr.write(f"  Location not found: {item['location']}")

            # Find asset
            asset = None
            if item.get('asset'):
                asset = Asset.objects.filter(name=item['asset']).first()
                if not asset:
                    self.stderr.write(f"  Asset not found: {item['asset']}")

            defaults = {
                'description': item.get('description', ''),
                'location': location,
                'asset': asset,
                'priority': item.get('priority', 'normal'),
                'status': item.get('status', 'new'),
                'requester_name': item.get('requester_name', 'Import'),
                'requester_email': item.get('requester_email', ''),
                'requester_phone': item.get('requester_phone', ''),
            }

            request, was_created = RepairRequest.objects.get_or_create(
                title=title,
                defaults=defaults
            )
            status = "Created" if was_created else "Exists"
            self.stdout.write(f"  {status}: #{request.id} {title}")

        self.stdout.write(self.style.SUCCESS(f"Requests import complete"))

    @transaction.atomic
    def import_accounts(self, path, dry_run=False):
        data = self.load_yaml(path)
        self.stdout.write(f"Importing {len(data)} accounts from {path}")

        for item in data:
            username = item.get('username')
            email = item.get('email')
            if not username or not email:
                self.stderr.write(f"  Skipping account without username/email: {item}")
                continue

            if dry_run:
                self.stdout.write(f"  [DRY-RUN] Would create account: {username}")
                continue

            if User.objects.filter(username=username).exists():
                self.stdout.write(f"  Exists: {username}")
                continue

            if User.objects.filter(email=email).exists():
                self.stdout.write(f"  Email exists: {email}")
                continue

            user = User.objects.create_user(
                username=username,
                email=email,
                password=item.get('password', 'Welcome123!'),
            )
            user.first_name = item.get('first_name', '')
            user.last_name = item.get('last_name', '')
            user.is_staff = item.get('is_staff', False)
            user.is_superuser = item.get('is_superuser', False)
            user.save()

            # Set must_change_password flag
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.must_change_password = True
            profile.save()

            self.stdout.write(f"  Created: {username} ({email})")

        self.stdout.write(self.style.SUCCESS(f"Accounts import complete"))

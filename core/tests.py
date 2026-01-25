from django.test import TestCase

from .models import Asset, Location


class LocationModelTest(TestCase):
    def test_create_location(self):
        loc = Location.objects.create(name='Kerkzaal')
        self.assertEqual(str(loc), 'Kerkzaal')

    def test_location_with_parent(self):
        parent = Location.objects.create(name='Hoofdgebouw')
        child = Location.objects.create(name='Keuken', parent=parent)
        self.assertEqual(str(child), 'Hoofdgebouw > Keuken')
        self.assertEqual(child.get_full_path(), 'Hoofdgebouw > Keuken')


class AssetModelTest(TestCase):
    def test_create_asset(self):
        loc = Location.objects.create(name='Kerkzaal')
        asset = Asset.objects.create(
            asset_tag='HVAC-01',
            name='Airconditioning',
            category=Asset.Category.HVAC,
            location=loc,
            status=Asset.Status.OPERATIONAL,
            criticality=Asset.Criticality.HIGH
        )
        self.assertEqual(str(asset), 'HVAC-01 - Airconditioning')
        self.assertEqual(asset.get_absolute_url(), f'/assets/{asset.pk}/')

    def test_asset_status_choices(self):
        self.assertEqual(Asset.Status.OPERATIONAL, 'operational')
        self.assertEqual(Asset.Status.OUT_OF_SERVICE, 'out_of_service')

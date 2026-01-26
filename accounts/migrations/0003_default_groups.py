from django.db import migrations


def create_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    groups = ['Koster', 'Verhuur', 'Onderhoud', 'Schoonmaak', 'Inkoop']
    for name in groups:
        Group.objects.get_or_create(name=name)


def remove_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name__in=['Koster', 'Verhuur', 'Onderhoud', 'Schoonmaak', 'Inkoop']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_invitation'),
    ]

    operations = [
        migrations.RunPython(create_groups, remove_groups),
    ]

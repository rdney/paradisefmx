from django.db import migrations, models
import django.db.models.deletion


# Map old category values to new category names
CATEGORY_MAP = {
    'hvac': 'HVAC / Klimaat',
    'electrical': 'Elektrisch',
    'plumbing': 'Sanitair',
    'safety': 'Veiligheid',
    'av': 'Audio/Video',
    'furniture': 'Meubilair',
    'building': 'Gebouw',
    'bells': 'Luidklokken',
    'other': 'Overig',
}


def create_categories_and_migrate(apps, schema_editor):
    Category = apps.get_model('core', 'Category')
    Asset = apps.get_model('core', 'Asset')

    # Create categories
    categories = [
        ('HVAC / Klimaat', 'bi-thermometer-half', 1),
        ('Elektrisch', 'bi-lightning', 2),
        ('Sanitair', 'bi-droplet', 3),
        ('Veiligheid', 'bi-shield-check', 4),
        ('Audio/Video', 'bi-speaker', 5),
        ('Meubilair', 'bi-lamp', 6),
        ('Gebouw', 'bi-building', 7),
        ('Luidklokken', 'bi-bell', 8),
        ('Overig', 'bi-three-dots', 99),
    ]

    category_objects = {}
    for name, icon, order in categories:
        cat, _ = Category.objects.get_or_create(name=name, defaults={'icon': icon, 'order': order})
        category_objects[name] = cat

    # Migrate existing assets
    for asset in Asset.objects.all():
        if asset.category_old:
            new_cat_name = CATEGORY_MAP.get(asset.category_old, 'Overig')
            asset.category = category_objects.get(new_cat_name)
            asset.save()


def reverse_migration(apps, schema_editor):
    Category = apps.get_model('core', 'Category')
    Asset = apps.get_model('core', 'Asset')

    # Reverse map
    reverse_map = {v: k for k, v in CATEGORY_MAP.items()}

    for asset in Asset.objects.select_related('category').all():
        if asset.category:
            asset.category_old = reverse_map.get(asset.category.name, 'other')
            asset.save()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_add_replacement_fields'),
    ]

    operations = [
        # Create Category model
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='naam')),
                ('icon', models.CharField(blank=True, help_text='Bootstrap icon class, bijv. bi-gear', max_length=50, verbose_name='icoon')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='volgorde')),
            ],
            options={
                'verbose_name': 'categorie',
                'verbose_name_plural': 'categorieën',
                'ordering': ['order', 'name'],
            },
        ),
        # Rename old category field
        migrations.RenameField(
            model_name='asset',
            old_name='category',
            new_name='category_old',
        ),
        # Add new category FK field
        migrations.AddField(
            model_name='asset',
            name='category',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='assets',
                to='core.category',
                verbose_name='categorie'
            ),
        ),
        # Migrate data
        migrations.RunPython(create_categories_and_migrate, reverse_migration),
        # Remove old category field
        migrations.RemoveField(
            model_name='asset',
            name='category_old',
        ),
    ]

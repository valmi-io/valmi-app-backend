# Generated by Django 3.1.5 on 2024-05-08 08:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0028_sourceaccessinfo'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sourceaccessinfo',
            name='id',
        ),
        migrations.AlterField(
            model_name='sourceaccessinfo',
            name='source',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='source_access_info', serialize=False, to='core.source'),
        ),
    ]

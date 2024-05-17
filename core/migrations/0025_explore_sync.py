# Generated by Django 3.1.5 on 2024-05-03 05:12

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0024_auto_20240422_1138'),
    ]

    operations = [
        migrations.AddField(
            model_name='explore',
            name='sync',
            field=models.ForeignKey(default=uuid.UUID('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'), on_delete=django.db.models.deletion.CASCADE, related_name='explore_sync', to='core.sync'),
        ),
    ]
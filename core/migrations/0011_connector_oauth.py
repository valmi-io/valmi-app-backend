# Generated by Django 3.1.5 on 2024-01-21 17:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_valmiuseridjitsuapitoken'),
    ]

    operations = [
        migrations.AddField(
            model_name='connector',
            name='oauth',
            field=models.BooleanField(default=False),
        ),
    ]
# Generated by Django 3.1.5 on 2023-03-08 17:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_connector_display_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='connector',
            name='type',
            field=models.CharField(default='DUMMY_CONNECTOR', max_length=64, primary_key=True, serialize=False),
        ),
    ]

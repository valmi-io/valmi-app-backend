# Generated by Django 3.1.5 on 2023-03-08 15:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='connector',
            name='image_name',
            field=models.CharField(default='DUMMY_CONNECTOR_IMAGE_NAME', max_length=128),
        ),
        migrations.AddField(
            model_name='connector',
            name='image_tag',
            field=models.CharField(default='DUMMY_CONNECTOR_TAG', max_length=64),
        ),
    ]

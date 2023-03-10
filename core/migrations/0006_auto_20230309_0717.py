# Generated by Django 3.1.5 on 2023-03-09 07:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_auto_20230308_1716'),
    ]

    operations = [
        migrations.AddField(
            model_name='connector',
            name='status',
            field=models.CharField(default='active', max_length=256),
        ),
        migrations.AddField(
            model_name='credential',
            name='status',
            field=models.CharField(default='active', max_length=256),
        ),
        migrations.AddField(
            model_name='destination',
            name='status',
            field=models.CharField(default='active', max_length=256),
        ),
        migrations.AddField(
            model_name='organization',
            name='status',
            field=models.CharField(default='active', max_length=256),
        ),
        migrations.AddField(
            model_name='source',
            name='status',
            field=models.CharField(default='active', max_length=256),
        ),
        migrations.AddField(
            model_name='sync',
            name='status',
            field=models.CharField(default='active', max_length=256),
        ),
        migrations.AddField(
            model_name='workspace',
            name='status',
            field=models.CharField(default='active', max_length=256),
        ),
    ]
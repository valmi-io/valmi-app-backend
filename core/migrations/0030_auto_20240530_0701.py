# Generated by Django 3.1.5 on 2024-05-30 07:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0029_auto_20240508_0844'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='prompt',
            name='table',
        ),
        migrations.AddField(
            model_name='prompt',
            name='query',
            field=models.CharField(default='query', max_length=1000),
        ),
    ]

# Generated by Django 3.1.5 on 2024-06-07 11:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0030_auto_20240530_0701'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='prompt',
            name='spec',
        ),
    ]

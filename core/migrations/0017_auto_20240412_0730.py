# Generated by Django 3.1.5 on 2024-04-12 07:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_auto_20240412_0723'),
    ]

    operations = [
        migrations.AlterField(
            model_name='prompt',
            name='name',
            field=models.CharField(max_length=256, unique=True),
        ),
    ]

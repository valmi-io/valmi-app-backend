# Generated by Django 3.1.5 on 2024-07-18 12:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0035_auto_20240718_1017'),
    ]

    operations = [
        migrations.AlterField(
            model_name='workspacestorefront',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]

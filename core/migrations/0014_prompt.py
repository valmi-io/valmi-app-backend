# Generated by Django 3.1.5 on 2024-04-11 15:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_storagecredentials'),
    ]

    operations = [
        migrations.CreateModel(
            name='Prompt',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]

# Generated by Django 3.1.5 on 2023-02-27 20:26

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='credential',
            name='id',
            field=models.UUIDField(auto_created=True, default=uuid.UUID('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'), editable=False, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='destination',
            name='id',
            field=models.UUIDField(auto_created=True, default=uuid.UUID('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'), editable=False, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='organization',
            name='id',
            field=models.UUIDField(auto_created=True, default=uuid.UUID('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'), editable=False, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='source',
            name='id',
            field=models.UUIDField(auto_created=True, default=uuid.UUID('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'), editable=False, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='sync',
            name='id',
            field=models.UUIDField(auto_created=True, default=uuid.UUID('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'), editable=False, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='workspace',
            name='id',
            field=models.UUIDField(auto_created=True, default=uuid.UUID('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'), editable=False, primary_key=True, serialize=False),
        ),
    ]

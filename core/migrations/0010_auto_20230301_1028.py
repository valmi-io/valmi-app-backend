# Generated by Django 3.1.5 on 2023-03-01 10:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_auto_20230301_0952'),
    ]

    operations = [
        migrations.RenameField(
            model_name='credential',
            old_name='connector',
            new_name='connector_id',
        ),
        migrations.RenameField(
            model_name='credential',
            old_name='workspace',
            new_name='workspace_id',
        ),
        migrations.RenameField(
            model_name='destination',
            old_name='credential',
            new_name='credential_id',
        ),
        migrations.RenameField(
            model_name='destination',
            old_name='workspace',
            new_name='workspace_id',
        ),
        migrations.RenameField(
            model_name='source',
            old_name='credential',
            new_name='credential_id',
        ),
        migrations.RenameField(
            model_name='source',
            old_name='workspace',
            new_name='workspace_id',
        ),
        migrations.RenameField(
            model_name='sync',
            old_name='destination',
            new_name='destination_id',
        ),
        migrations.RenameField(
            model_name='sync',
            old_name='source',
            new_name='source_id',
        ),
        migrations.RenameField(
            model_name='sync',
            old_name='workspace',
            new_name='workspace_id',
        ),
        migrations.RenameField(
            model_name='workspace',
            old_name='organization',
            new_name='organization_id',
        ),
    ]

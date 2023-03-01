# Generated by Django 3.1.5 on 2023-03-01 11:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_credential_name'),
    ]

    operations = [
        migrations.RenameField(
            model_name='sync',
            old_name='source_id',
            new_name='source',
        ),
        migrations.AlterField(
            model_name='credential',
            name='name',
            field=models.CharField(default='DUMMY_CREDENTIAL_NAME', max_length=256),
        ),
    ]

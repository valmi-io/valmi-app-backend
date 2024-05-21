# Generated by Django 3.1.5 on 2024-05-08 06:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0027_auto_20240508_0539'),
    ]

    operations = [
        migrations.CreateModel(
            name='SourceAccessInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='source_access_info', to='core.source')),
                ('storage_credentials', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='source_access_info', to='core.storagecredentials')),
            ],
        ),
    ]

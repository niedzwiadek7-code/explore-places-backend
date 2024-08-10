# Generated by Django 5.0.6 on 2024-08-10 10:53

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('activities', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='entity',
            name='address',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='activities.address'),
        ),
        migrations.AlterField(
            model_name='entity',
            name='coordinates',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='activities.coordinates'),
        ),
        migrations.AlterField(
            model_name='entity',
            name='external_links',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='activities.externallinks'),
        ),
    ]
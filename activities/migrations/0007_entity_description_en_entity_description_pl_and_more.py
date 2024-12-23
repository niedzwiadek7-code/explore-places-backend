# Generated by Django 5.0.6 on 2024-08-24 10:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('activities', '0006_remove_entity_coordinates_delete_coordinates'),
    ]

    operations = [
        migrations.AddField(
            model_name='entity',
            name='description_en',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='entity',
            name='description_pl',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='entity',
            name='name_en',
            field=models.CharField(max_length=250, null=True),
        ),
        migrations.AddField(
            model_name='entity',
            name='name_pl',
            field=models.CharField(max_length=250, null=True),
        ),
    ]

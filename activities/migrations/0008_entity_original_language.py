# Generated by Django 5.0.6 on 2024-08-27 15:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('activities', '0007_entity_description_en_entity_description_pl_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='entity',
            name='original_language',
            field=models.CharField(default='pl', max_length=250),
        ),
    ]
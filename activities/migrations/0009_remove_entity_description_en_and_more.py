# Generated by Django 5.0.6 on 2024-08-31 07:41

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('activities', '0008_entity_original_language'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='entity',
            name='description_en',
        ),
        migrations.RemoveField(
            model_name='entity',
            name='description_pl',
        ),
        migrations.RemoveField(
            model_name='entity',
            name='name_en',
        ),
        migrations.RemoveField(
            model_name='entity',
            name='name_pl',
        ),
        migrations.CreateModel(
            name='Translation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('language', models.CharField(max_length=250)),
                ('name', models.CharField(max_length=250)),
                ('description', models.TextField(null=True)),
                ('activity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='activities.entity')),
            ],
        ),
    ]

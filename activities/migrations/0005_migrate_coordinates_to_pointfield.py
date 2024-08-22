from django.contrib.gis.geos import Point
from django.db import migrations


def migrate_coordinates_to_pointfield(apps, schema_editor):
    Entity = apps.get_model('activities', 'Entity')
    Coordinates = apps.get_model('activities', 'Coordinates')

    for entity in Entity.objects.all():
        if entity.coordinates_id:
            coords = Coordinates.objects.get(id=entity.coordinates_id)
            if coords.latitude is not None and coords.longitude is not None:
                entity.point_field = Point(coords.longitude, coords.latitude, srid=4326)
                entity.save()


class Migration(migrations.Migration):

    dependencies = [
        ('activities', '0004_entity_point_field'),
    ]

    operations = [
        migrations.RunPython(migrate_coordinates_to_pointfield),
    ]

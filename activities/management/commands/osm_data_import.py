# activities/management/commands/osm_data_import.py

import requests
from django.core.management.base import BaseCommand
from activities.models import Activity, User

class Command(BaseCommand):
    help = 'Imports OSM data and saves it to the database'

    def handle(self, *args, **kwargs):
        bbox = "11.54,48.14,11.543,48.145"  # example bbox
        user = User.objects.first()  # Assuming you want to assign activities to the first user
        osm_data = self.fetch_osm_data(bbox)
        self.save_activities(osm_data, user.id)

    def fetch_osm_data(self, bbox):
        url = f"https://api.openstreetmap.org/api/0.6/map?bbox={bbox}"
        response = requests.get(url)
        response.raise_for_status()
        return response.content

    def parse_osm_data(self, osm_data):
        from xml.etree import ElementTree as ET
        root = ET.fromstring(osm_data)

        nodes = {}
        for node in root.findall('node'):
            osm_id = node.get('id')
            latitude = float(node.get('lat'))
            longitude = float(node.get('lon'))
            nodes[osm_id] = {
                'latitude': latitude,
                'longitude': longitude,
                'tags': {}
            }

        for way in root.findall('way'):
            osm_id = way.get('id')
            nodes_in_way = []
            for nd in way.findall('nd'):
                ref = nd.get('ref')
                if ref in nodes:
                    nodes_in_way.append(nodes[ref])

            name = None
            place_type = None
            for tag in way.findall('tag'):
                if tag.get('k') == 'name':
                    name = tag.get('v')
                if tag.get('k') == 'highway':
                    place_type = tag.get('v')

            if name and place_type:
                yield {
                    'osm_id': osm_id,
                    'name': name,
                    'place_type': place_type,
                    'nodes': nodes_in_way
                }

    def save_activities(self, osm_data, user_id):
        for place in self.parse_osm_data(osm_data):
            name = place['name']
            place_type = place['place_type']
            latitude = place['nodes'][0]['latitude'] if place['nodes'] else None
            longitude = place['nodes'][0]['longitude'] if place['nodes'] else None

            Activity.objects.get_or_create(
                osm_id=place['osm_id'],
                defaults={
                    'owner_id': user_id,
                    'name': name,
                    'latitude': latitude,
                    'longitude': longitude,
                    'place_type': place_type,
                    'description': 'Imported from OSM'
                }
            )

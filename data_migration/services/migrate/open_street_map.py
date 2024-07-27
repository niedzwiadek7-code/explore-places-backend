from activities.models import Activity
from data_migration.models import OpenTripMapServiceData, DataMigrationResource
from data_migration.services.migrate.base import DataMigrationService
import requests
import json


class OpenStreetMapMigrationService(DataMigrationService):
    def __init__(self, credentials=dict):
        self.base_url = credentials.base_url
        self.api_key = credentials.credentials.get('api_key')

    def required_arguments(self):
        return ['min_lat', 'max_lat', 'min_lon', 'max_lon']

    def make_request(self, method='GET', url=None, data=None):
        requests.request(
            method=method,
            url=url,
            data=data
        )
        response = requests.get(url)
        response.raise_for_status()
        return response.content

    def migrate(self, args):
        min_lat = args.get('min_lat')
        max_lat = args.get('max_lat')
        min_lon = args.get('min_lon')
        max_lon = args.get('max_lon')

        places_json = self.make_request(
            method='GET',
            url=f'{self.base_url}/places/bbox?lon_min={min_lon}&lon_max={max_lon}&lat_min={min_lat}&lat_max={max_lat}'
                f'&apikey={self.api_key}'
        )

        places_result = json.loads(places_json).get('features')
        places_ids = list(map(lambda x: x.get('properties').get('xid'), places_result))

        for place_id in places_ids:
            place_json = self.make_request(
                method='GET',
                url=f'{self.base_url}/places/xid/{place_id}?apikey={self.api_key}'
            )
            place_result = json.loads(place_json)

            def get_images():
                if place_result.get('preview') and place_result.get('preview').get('source'):
                    return [place_result.get('preview').get('source')]
                return []

            Activity.objects.update_or_create(
                migration_data__xid=place_id,
                defaults=dict(
                    name=place_result.get('name'),
                    description=place_result.get('wikipedia_extracts') and place_result.get('wikipedia_extracts').get('text'),
                    migration_data=dict(
                        xid=place_id,
                    ),
                    images=get_images(),
                    destination_resource='open_street_map',
                    address=f'{place_result.get('address').get('road')} {place_result.get('address').get('house_number')}',
                    city=place_result.get('address').get('town'),
                    state=place_result.get('address').get('state'),
                    country=place_result.get('address').get('country'),
                    postal_code=place_result.get('address').get('postcode'),
                    latitude=place_result.get('point').get('lat'),
                    longitude=place_result.get('point').get('lon'),
                )
            )

        OpenTripMapServiceData.objects.create(
            min_latitude=min_lat,
            max_latitude=max_lat,
            min_longitude=min_lon,
            max_longitude=max_lon
        )

        pass

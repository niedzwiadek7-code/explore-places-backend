from activities.models import Activity
from data_migration.models import OpenTripMapServiceData
from data_migration.services.migrate.base import DataMigrationService
from services.api_service import APIService
import logging
from time import sleep


class OpenStreetMapMigrationService(DataMigrationService):
    def __init__(self, credentials=dict):
        self.base_url = credentials.base_url
        self.api_key = credentials.credentials.get('api_key')
        self.logger = logging.getLogger(__name__)
        self.api_service = APIService(self.base_url)

    def required_arguments(self):
        return ['min_lat', 'max_lat', 'min_lon', 'max_lon']

    def migrate(self, args):
        min_lat = args.get('min_lat')
        max_lat = args.get('max_lat')
        min_lon = args.get('min_lon')
        max_lon = args.get('max_lon')

        places_result = self.api_service.request(
            method='GET',
            endpoint=f'/places/bbox',
            query_params=dict(
                lon_min=min_lon,
                lon_max=max_lon,
                lat_min=min_lat,
                lat_max=max_lat,
                apikey=self.api_key
            )
        )

        places_ids = list(map(lambda x: x.get('properties').get('xid'), places_result.get('features')))
        self.logger.info(f'Found {len(places_ids)} places')

        i = 0
        # TODO: make all requests at the same time
        for place_id in places_ids:
            sleep(.12)
            i += 1
            self.logger.info(f'Processing place {i}/{len(places_ids)}')
            place_result = self.api_service.request(
                method='GET',
                endpoint=f'/places/xid/{place_id}',
                query_params=dict(
                    apikey=self.api_key
                )
            )

            def get_images():
                if place_result.get('preview') and place_result.get('preview').get('source'):
                    return [place_result.get('preview').get('source')]
                return []

            if not place_result.get('name') or place_result.get('name') == '':
                continue

            # NOTE: If there are no images, skip this activity
            if not get_images():
                continue

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
            self.logger.info(f'Created activity {place_result.get("name")} with xid {place_id}')

        OpenTripMapServiceData.objects.create(
            min_latitude=min_lat,
            max_latitude=max_lat,
            min_longitude=min_lon,
            max_longitude=max_lon
        )

        pass

import asyncio
import numpy as np
import logging

from asgiref.sync import sync_to_async
from django.contrib.gis.geos import Point
from django.db import transaction

from activities.models import Address, ExternalLinks, Entity as ActivityEntity
from data_migration.services.migrate.base import DataMigrationService
from data_migration.models import OpenTripMap as OpenTripMapServiceData
from services.api_service import APIService


class OpenStreetMapMigrationService(DataMigrationService):
    def __init__(self, credentials=dict):
        self.base_url = credentials.base_url
        self.api_key = credentials.credentials.get('api_key')
        self.logger = logging.getLogger(__name__)
        self.api_service = APIService(self.base_url, limit=10, period=1)

    def required_arguments(self):
        return ['min_lat', 'max_lat', 'min_lon', 'max_lon']

    async def fetch_data(self, args):
        min_lat = float(args.get('min_lat'))
        max_lat = float(args.get('max_lat'))
        min_lon = float(args.get('min_lon'))
        max_lon = float(args.get('max_lon'))

        step_lat = 0.1
        step_lon = 0.1

        async def step(min_lat_loc, max_lat_loc, min_lon_loc, max_lon_loc):
            async for field in OpenTripMapServiceData.objects.filter(
                    min_latitude=min_lat_loc,
                    max_latitude=max_lat_loc,
                    min_longitude=min_lon_loc,
                    max_longitude=max_lon_loc
            ):
                self.logger.info(f'Step with lat: {min_lat_loc}-{max_lat_loc} and lon: {min_lon_loc}-{max_lon_loc} was already processed')
                return []

            places_result = self.api_service.request(
                method='GET',
                endpoint=f'/places/bbox',
                query_params=dict(
                    lon_min=min_lon_loc,
                    lon_max=max_lon_loc,
                    lat_min=min_lat_loc,
                    lat_max=max_lat_loc,
                    apikey=self.api_key,
                    rate=3,
                    kinds=f'interesting_places,amusements,adult,foods,transport,accomodations'.replace(',', '%2C')
                )
            )

            places_ids = list(map(lambda x: x.get('properties').get('xid'), places_result.get('features')))
            self.logger.info(
                f'Found {len(places_ids)} places for step with lat: {min_lat_loc}-{max_lat_loc} and lon: {min_lon_loc}-{max_lon_loc}'
            )

            async def fetch_place_data(place_id):
                return self.api_service.request(
                    method='GET',
                    endpoint=f'/places/xid/{place_id}',
                    query_params=dict(apikey=self.api_key)
                )

            place_tasks = [fetch_place_data(place_id) for place_id in places_ids]

            await OpenTripMapServiceData.objects.acreate(
                min_latitude=min_lat_loc,
                max_latitude=max_lat_loc,
                min_longitude=min_lon_loc,
                max_longitude=max_lon_loc
            )

            return await asyncio.gather(*place_tasks)

        step_tasks = [
            step(round(lat, 1), round(lat + step_lat, 1), round(lon, 1), round(lon + step_lon, 1))
            for lat in np.arange(min_lat, max_lat, step_lat)
            for lon in np.arange(min_lon, max_lon, step_lon)
        ]

        for step_result in await asyncio.gather(*step_tasks):
            for data in step_result:
                yield data

    @sync_to_async
    def process_data(self, data):
        try:
            with transaction.atomic():
                address_data = data.get('address', {})

                def get_images():
                    if data.get('preview') and data.get('preview').get('source'):
                        return [data.get('preview').get('source')]
                    if data.get('image'):
                        return [data.get('image')]
                    return []

                def get_point_field():
                    if data.get('point'):
                        return Point(
                            float(data.get('point').get('lon')),
                            float(data.get('point').get('lat')),
                            srid=4326
                        )
                    return None

                def get_tags():
                    if data.get('kinds'):
                        return data.get('kinds').split(',')
                    return []

                if not data.get('name'):
                    return None

                if not get_images():
                    return None

                address, _ = Address.objects.get_or_create(
                    street=f'{address_data.get("road", "")} {address_data.get("house_number", "")}',
                    city=address_data.get('town'),
                    state=address_data.get('state'),
                    country=address_data.get('country'),
                    postal_code=address_data.get('postcode'),
                )

                external_links, _ = ExternalLinks.objects.get_or_create(
                    wikipedia_url=address_data.get('wikipedia'),
                    website_url=address_data.get('url'),
                )

                ActivityEntity.objects.update_or_create(
                    migration_data__xid=data.get('xid'),
                    defaults=dict(
                        name=data.get('name'),
                        description=data.get('wikipedia_extracts', {}).get('text'),
                        migration_data=dict(
                            xid=data.get('xid'),
                        ),
                        images=get_images(),
                        destination_resource='open_street_map',
                        address=address,
                        point_field=get_point_field(),
                        external_links=external_links,
                        tags=get_tags()
                    )
                )

                self.logger.info(f'Place {data.get('xid')} - {data.get("name")} was successfully saved')

        except Exception as err:
            self.logger.error(f'Error processing place {data.get('xid')}: {err}')

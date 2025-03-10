import asyncio
from pydoc import describe

import numpy as np
import logging

from asgiref.sync import sync_to_async
from django.db import transaction

from activities.models import Address, ExternalLinks, Entity as ActivityEntity
from data_migration.services.migrate.base import DataMigrationService
from data_migration.models import OpenTripMap as OpenTripMapServiceData
from services.api_service import APIService
from services.translator import Translator
from utils.geo_utils import Location


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
        max_lat = float(args.get('max_lat')) - 0.001
        min_lon = float(args.get('min_lon'))
        max_lon = float(args.get('max_lon')) - 0.001

        step_lat = 0.1
        step_lon = 0.1

        async def step_was_processed(min_lat_loc, max_lat_loc, min_lon_loc, max_lon_loc):
            async for field in OpenTripMapServiceData.objects.filter(
                    min_latitude=min_lat_loc,
                    max_latitude=max_lat_loc,
                    min_longitude=min_lon_loc,
                    max_longitude=max_lon_loc
            ):
                return True

            return False

        for lat in np.arange(min_lat, max_lat, step_lat):
            for lon in np.arange(min_lon, max_lon, step_lon):
                min_lat_loc = round(lat, 1)
                max_lat_loc = round(lat + step_lat, 1)
                min_lon_loc = round(lon, 1)
                max_lon_loc = round(lon + step_lon, 1)

                if await step_was_processed(min_lat_loc, max_lat_loc, min_lon_loc, max_lon_loc):
                    self.logger.info(f'Step with lat: {min_lat_loc}-{max_lat_loc} and lon: {min_lon_loc}-{max_lon_loc} was already processed')
                    continue

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

                for place_id in places_ids:
                    yield self.api_service.request(
                        method='GET',
                        endpoint=f'/places/xid/{place_id}',
                        query_params=dict(apikey=self.api_key)
                    )

                await OpenTripMapServiceData.objects.acreate(
                    min_latitude=min_lat_loc,
                    max_latitude=max_lat_loc,
                    min_longitude=min_lon_loc,
                    max_longitude=max_lon_loc
                )

    @sync_to_async
    def process_data(self, data):
        try:
            with transaction.atomic():
                address_data = data.get('address', {})

                def get_images():
                    def is_image_available(url):
                        #  try 3 times to get the image
                        for _ in range(3):
                            response = APIService(url).head(headers={'User-Agent': 'Mozilla/5.0'})
                            if response:
                                return response.status_code == 200 and 'image' in response.headers['Content-Type']
                        return False

                    images = []
                    preview_source = data.get('preview', {}).get('source')
                    if preview_source and is_image_available(preview_source):
                        images.append(preview_source)

                    image = data.get('image')
                    if image and is_image_available(image):
                        images.append(image)

                    return images

                def get_point_field():
                    if data.get('point'):
                        return Location(
                            latitude=data.get('point').get('lat'),
                            longitude=data.get('point').get('lon')
                        )
                    return None

                def get_original_language():
                    if data.get('wikipedia_extracts', {}).get('text'):
                        return Translator.detect_language(data.get('wikipedia_extracts', {}).get('text'))
                    return Translator.detect_language(data.get('name'))

                def get_tags():
                    if data.get('kinds'):
                        return data.get('kinds').split(',')
                    return []

                if not data.get('name'):
                    return None

                if not get_images():
                    return None

                if ActivityEntity.objects.filter(
                    destination_resource='open_street_map',
                    name=data.get('name'),
                    images=get_images(),
                    description=data.get('wikipedia_extracts', {}).get('text'),
                ).count() > 0:
                    self.logger.info(f'Place {data.get("xid")} - {data.get("name")} is a duplicate')
                    return None

                location = get_point_field()
                address, _ = Address.objects.get_or_create(
                    street=f'{address_data.get("road", "")} {address_data.get("house_number", "")}',
                    city=address_data.get('town'),
                    state=address_data.get('state'),
                    country=address_data.get('country'),
                    postal_code=address_data.get('postcode'),
                    latitude=location.latitude if location else None,
                    longitude=location.longitude if location else None
                )

                external_links, _ = ExternalLinks.objects.get_or_create(
                    wikipedia_url=data.get('wikipedia'),
                    website_url=data.get('url'),
                )

                activity, _ = ActivityEntity.objects.update_or_create(
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
                        external_links=external_links,
                        tags=get_tags(),
                        original_language=get_original_language()
                    )
                )

                self.logger.info(f'Place {activity.id} - {data.get("name")} was successfully saved')

                return activity

        except Exception as err:
            self.logger.error(f'Error processing place {data.get('xid')}: {err}')


    @transaction.atomic
    def filter_unreachable_photos(self):
        allEntities = ActivityEntity.objects.filter(destination_resource='open_street_map')

        def is_image_available(url):
            #  try 3 times to get the image
            for _ in range(3):
                response = APIService(url).head(headers={'User-Agent': 'Mozilla/5.0'})
                if response:
                    return response.status_code == 200 and 'image' in response.headers['Content-Type']
            return False

        filtered = 0

        for entity in allEntities:
            images = entity.images
            images = list(filter(is_image_available, images))
            entity.images = images

            if len(images) == 0:
                self.logger.info(f'Place {entity.id} - {entity.name} has no reachable images')
                entity.delete()
                filtered += 1

        self.logger.info(f'{filtered} unreachable photos were filtered')
        return True

    @transaction.atomic
    def delete_duplicates(self):
        allEntities = ActivityEntity.objects.filter(destination_resource='open_street_map')

        duplicates = 0

        for entity in allEntities:
            if ActivityEntity.objects.filter(
                name=entity.name,
                images=entity.images,
                description=entity.description,
                destination_resource='open_street_map'
            ).count() > 1:
                self.logger.info(f'Place {entity.id} - {entity.name} is a duplicate')
                entity.delete()
                duplicates += 1

        self.logger.info(f'{duplicates} duplicates were filtered')
        return True

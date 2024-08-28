import numpy as np
import json
import os
import asyncio
from asyncio import Semaphore
from django.db import transaction
from asgiref.sync import sync_to_async
from requests import RequestException
from django.contrib.gis.geos import Point

from activities.models import Entity as ActivityEntity, Address, ExternalLinks
from data_migration.models import OpenTripMap as OpenTripMapServiceData
from data_migration.services.migrate.base import DataMigrationService
from services.api_service import APIService
import logging

from services.translator import Translator
from travel_app_backend.settings import LANGUAGES


def save_migration_data(min_lat, max_lat, min_lon, max_lon):
    OpenTripMapServiceData.objects.create(
        min_latitude=min_lat,
        max_latitude=max_lat,
        min_longitude=min_lon,
        max_longitude=max_lon
    )


class OpenStreetMapMigrationService(DataMigrationService):
    def __init__(self, credentials=dict):
        self.base_url = credentials.base_url
        self.api_key = credentials.credentials.get('api_key')
        self.logger = logging.getLogger(__name__)
        self.api_service = APIService(self.base_url)
        self.semaphore = Semaphore(5)  # Limit to 10 concurrent requests
        self.total_migration_steps = 0
        self.total_places = 0

        def get_language_codes(languages):
            return [code for code, _ in languages]

        language_codes = get_language_codes(LANGUAGES)
        self.translators = {
            code: Translator(target=code)
            for code in language_codes
        }

    def required_arguments(self):
        return ['min_lat', 'max_lat', 'min_lon', 'max_lon']

    async def migrate(self, args):
        min_lat = float(args.get('min_lat'))
        max_lat = float(args.get('max_lat'))
        min_lon = float(args.get('min_lon'))
        max_lon = float(args.get('max_lon'))

        step_lat = 0.05
        step_lon = 0.1

        for lat in np.arange(min_lat, max_lat, step_lat):
            for lon in np.arange(min_lon, max_lon, step_lon):
                await self.step(lat, lat + step_lat, lon, lon + step_lon)

        self.logger.info(f'Total migration steps: {self.total_migration_steps}')
        self.logger.info(f'Total places migrated: {self.total_places}')

    async def step(self, min_lat, max_lat, min_lon, max_lon):
        self.total_migration_steps += 1
        self.logger.info(f'Processing step with lat: {min_lat}-{max_lat} and lon: {min_lon}-{max_lon}')

        @sync_to_async()
        def was_processed():
            return OpenTripMapServiceData.objects.filter(
                min_latitude=min_lat,
                max_latitude=max_lat,
                min_longitude=min_lon,
                max_longitude=max_lon
            ).exists()

        if await was_processed():
            self.logger.info(f'Step with lat: {min_lat}-{max_lat} and lon: {min_lon}-{max_lon} was already processed')
            return

        places_result = self.api_service.request(
            method='GET',
            endpoint=f'/places/bbox',
            query_params=dict(
                lon_min=min_lon,
                lon_max=max_lon,
                lat_min=min_lat,
                lat_max=max_lat,
                apikey=self.api_key,
                rate=3,
                kinds=f'interesting_places,amusements,adult,foods,transport,accomodations'.replace(',', '%2C')
            )
        )

        places_ids = list(map(lambda x: x.get('properties').get('xid'), places_result.get('features')))
        self.logger.info(f'Found {len(places_ids)} places')

        tasks = [self.process_place(place_id, i + 1, len(places_ids)) for i, place_id in enumerate(places_ids)]
        await asyncio.gather(*tasks)

        # Ensure the migration data is saved outside of async context
        await sync_to_async(save_migration_data)(min_lat, max_lat, min_lon, max_lon)
        self.logger.info(f'Saved migration data for lat: {min_lat}-{max_lat} and lon: {min_lon}-{max_lon}')

    async def process_place(self, place_id, index, total):
        try:
            async with self.semaphore:
                self.logger.info(f'Processing place {index}/{total}')
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
                    if place_result.get('image'):
                        return [place_result.get('image')]
                    return []

                def format_tag(tag):
                    base_dir = os.path.dirname(os.path.abspath(__file__))
                    file_path = os.path.join(base_dir, 'open_street_map_tags.json')

                    with open(file_path, 'r', encoding='utf-8') as file:
                        dictionary = json.load(file)

                    return dictionary.get(tag, tag)

                def get_tags():
                    if place_result.get('kinds'):
                        tags = place_result.get('kinds').split(',')
                        return list(map(format_tag, tags))
                    return []

                if not place_result.get('name'):
                    return

                if not get_images():
                    return

                def translate_text(text, dest_lang='pl'):
                    translator = Translator()
                    if text:
                        try:
                            translation = translator.translate(text, dest=dest_lang)
                            return translation.text
                        except Exception as e:
                            return text
                    return text

                def get_translated_description():
                    description = place_result.get('wikipedia_extracts', {}).get('text')
                    return translate_text(description)

                def get_point_field():
                    if place_result.get('point'):
                        return Point(
                            float(place_result.get('point').get('lon')),
                            float(place_result.get('point').get('lat')),
                            srid=4326
                        )
                    return None

                # Synchronize the transaction context and ORM operations
                @sync_to_async
                def save_to_db():
                    with transaction.atomic():
                        address, _ = Address.objects.update_or_create(
                            street=f'{place_result.get("address", {}).get("road", "")} {place_result.get("address", {}).get("house_number", "")}',
                            city=place_result.get('address', {}).get('town'),
                            state=place_result.get('address', {}).get('state'),
                            country=place_result.get('address', {}).get('country'),
                            postal_code=place_result.get('address', {}).get('postcode'),
                        )

                        external_links, _ = ExternalLinks.objects.update_or_create(
                            wikipedia_url=place_result.get('wikipedia'),
                            website_url=place_result.get('url'),
                        )

                        ActivityEntity.objects.update_or_create(
                            migration_data__xid=place_id,
                            defaults=dict(
                                name=place_result.get('name'),
                                description=get_translated_description(),
                                migration_data=dict(
                                    xid=place_id,
                                ),
                                images=get_images(),
                                destination_resource='open_street_map',
                                address=address,
                                point_field=get_point_field(),
                                external_links=external_links,
                                tags=get_tags()
                            )
                        )
                        self.total_places += 1

                # Call the synchronized save_to_db function
                await save_to_db()

                self.logger.info(f'Created activity {place_result.get("name")} with xid {place_id}')

        except RequestException as e:
            self.logger.error(f'Error processing place {place_id}: {e}')
            raise RequestException(e)

        except Exception as err:
            self.logger.error(f'Error processing place {place_id}: {err}')
#

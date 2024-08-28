import asyncio
import numpy as np
import logging

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

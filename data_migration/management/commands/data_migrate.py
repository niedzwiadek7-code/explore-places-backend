import logging
import importlib
from django.core.management.base import BaseCommand
import sys
from django.db import transaction
import asyncio

from data_migration.models import Resource as DataMigrationResource
from utils.decorators.timeit_decorator import timeit_decorator


class Command(BaseCommand):
    help = 'Migrate data from OpenTripMap'
    service_instance = None
    logger = logging.getLogger(__name__)

    def add_arguments(self, parser):
        parser.add_argument(
            'service',
            type=str,
            help='Service to migrate data from'
        )
        service_name = sys.argv[2]

        def create_name_class():
            parts = service_name.split('_')
            return ''.join([part.capitalize() for part in parts]) + 'MigrationService'

        try:
            module = importlib.import_module(f'data_migration.services.migrate.{service_name}')
            service_class = getattr(module, f'{create_name_class()}')

            credentials = DataMigrationResource.objects.filter(name=service_name).first()
            if not credentials:
                self.logger.error(f'Credentials for {service_name} not found')

            self.service_instance = service_class(credentials)
            required_args = self.service_instance.required_arguments()

            for arg in required_args:
                parser.add_argument(
                    f'--{arg}',
                    type=str,
                    help=f'{arg} is required for {service_name} migration'
                )

        except ImportError:
            self.logger.error(f'Service {service_name} not found')
            exit()

    async def main(self, args, kwargs):
        async for data in self.service_instance.fetch_data(kwargs):
            print(data)

    @timeit_decorator
    def handle(self, *args, **kwargs):
        # TODO: move here database logic (if it possible)
        self.logger.info('Starting data migration...')
        try:
            asyncio.run(self.main(args, kwargs))
            # asyncio.run(self.service_instance.migrate(kwargs))
            self.logger.info('Data migration completed successfully')
        except Exception as e:
            self.logger.error(f'Error during migration: {e}')
            raise e

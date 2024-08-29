import httpcore
import logging
import importlib
from django.core.management.base import BaseCommand
import sys
import asyncio

from data_migration.models import Resource as DataMigrationResource
from services.translator import Translator
from travel_app_backend.settings import LANGUAGES
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

    async def translate_activity(self, activity):
        def get_language_codes(languages):
            return [code for code, _ in languages]

        language_codes = get_language_codes(LANGUAGES)

        for code in language_codes:
            translator = Translator(target=code)

            description_name = f'description_{code}'
            name_name = f'name_{code}'

            description = activity.__dict__['description']
            name = activity.__dict__['name']

            try:
                if activity.original_language == code:
                    name_translation = name
                else:
                    name_translation = await asyncio.to_thread(translator.translate, name)

                setattr(activity, name_name, name_translation)

                if activity.original_language == code:
                    description_translation = description
                else:
                    description_translation = await asyncio.to_thread(translator.translate, description)

                setattr(activity, description_name, description_translation)

                await activity.asave(
                    update_fields=[
                        name_name,
                        description_name
                    ]
                )

            except httpcore._exceptions.ProtocolError as e:
                self.logger.error(f'Error translating entity with id {activity.id}: {str(e)}')

            except Exception as e:
                self.logger.error(f'Unexpected error: {str(e)}')

        self.logger.info(f'Activity {activity.id} - {activity.name} has been translated')

    async def main(self, args):
        async def handle_record(data):
            activity = await self.service_instance.process_data(data)
            await self.translate_activity(activity)

        tasks = []
        async for data in self.service_instance.fetch_data(args):
            task = asyncio.create_task(handle_record(data))
            tasks.append(task)

        await asyncio.gather(*tasks)

    @timeit_decorator
    def handle(self, *args, **kwargs):
        # TODO: move here database logic (if it possible)
        self.logger.info('Starting data migration...')
        try:
            asyncio.run(self.main(kwargs))
            self.logger.info('Data migration completed successfully')
        except Exception as e:
            self.logger.error(f'Error during migration: {e}')
            raise e

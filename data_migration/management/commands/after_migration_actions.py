import importlib
import logging

from django.core.management import BaseCommand
from data_migration.models import Resource as DataMigrationResource


class Command(BaseCommand):
    help = 'After migration actions'
    service_instance = None
    logger = logging.getLogger(__name__)

    def add_arguments(self, parser):
        parser.add_argument(
            '--service',
            type=str,
            help='Service to migrate data from',
            required=True
        )

        parser.add_argument(
            '--action',
            type=str,
            help='Action to perform',
            required=True
        )

    def handle(self, *args, **options):
        service_name = options['service']
        action = options['action']

        try:
            def create_name_class():
                parts = service_name.split('_')
                return ''.join([part.capitalize() for part in parts]) + 'MigrationService'

            module = importlib.import_module(f'data_migration.services.migrate.{service_name}')
            service_class = getattr(module, f'{create_name_class()}')

            credentials = DataMigrationResource.objects.filter(name=service_name).first()
            if not credentials:
                self.logger.error(f'Credentials for {service_name} not found')

            self.logger.info(f'Performing {action} action for {service_name} service')

            service_instance = service_class(credentials)
            method = getattr(service_instance, action, None)
            if method is None:
                self.logger.error(f'Action {action} not found for {service_name} service')
                exit()

            method()
            self.logger.info(f'{action} action for {service_name} service performed successfully')

        except ImportError:
            self.logger.error(f'Service {service_name} not found')
            exit()

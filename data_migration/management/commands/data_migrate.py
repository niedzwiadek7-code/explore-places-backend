import importlib
from django.core.management.base import BaseCommand
import sys
from django.db import transaction

from data_migration.models import DataMigrationResource


class Command(BaseCommand):
    help = 'Migrate data from OpenTripMap'
    service_instance = None

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
                self.stdout.write(self.style.ERROR(f'Credentials for {service_name} not found'))

            self.service_instance = service_class(credentials)
            required_args = self.service_instance.required_arguments()

            for arg in required_args:
                parser.add_argument(
                    f'--{arg}',
                    type=str,
                    help=f'{arg} is required for {service_name} migration'
                )

        except ImportError:
            self.stdout.write(self.style.ERROR(f'Service {service_name} not found'))
            exit()

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write('Starting data migration...')
        self.service_instance.migrate(kwargs)
        self.stdout.write(self.style.SUCCESS('Data migration completed successfully'))

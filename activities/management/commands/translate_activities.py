import logging
import asyncio

import httpcore
from django.core.management import BaseCommand
from django.db import transaction

from activities.models import Entity
from services.translator import Translator
from utils.decorators.timeit_decorator import timeit_decorator


class Command(BaseCommand):
    help = 'Translate activities'
    logger = logging.getLogger(__name__)

    def get_translator(self, language):
        return Translator(target=language)

    def add_arguments(self, parser):
        parser.add_argument(
            'language',
            type=str,
            help='Language to translate activities to'
        )

    async def translate(self, entity, language):
        description_name = f'description_{language}'
        name_name = f'name_{language}'

        description = entity.__dict__['description']
        name = entity.__dict__['name']

        translator = self.get_translator(language)

        try:
            if entity.original_language == language:
                name_translation = name
            else:
                name_translation = await asyncio.to_thread(translator.translate, name)

            setattr(entity, name_name, name_translation)

            if entity.original_language == language:
                description_translation = description
            else:
                description_translation = await asyncio.to_thread(translator.translate, description)

            setattr(entity, description_name, description_translation)

            await entity.asave(
                update_fields=[
                    name_name,
                    description_name
                ]
            )
            self.logger.info(f'Activity with id {entity.id} has been translated')

        except httpcore._exceptions.ProtocolError as e:
            self.logger.error(f'Error translating entity with id {entity.id}: {str(e)}')

        except Exception as e:
            self.logger.error(f'Unexpected error: {str(e)}')

    @timeit_decorator
    @transaction.atomic
    def handle(self, *args, **kwargs):
        language = kwargs['language']

        entities = Entity.objects.all()

        loop = asyncio.get_event_loop()
        tasks = [self.translate(entity, language) for entity in entities]
        loop.run_until_complete(asyncio.gather(*tasks))

        self.logger.info('Activities translation completed successfully')

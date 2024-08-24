from modeltranslation.translator import register, TranslationOptions
from .models import Entity


@register(Entity)
class EntityTranslationOptions(TranslationOptions):
    fields = ('name', 'description')

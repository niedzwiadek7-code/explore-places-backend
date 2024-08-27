from deep_translator import GoogleTranslator
from datetime import timedelta
from ratelimit import limits, sleep_and_retry


class Translator:
    def __init__(self, target):
        self.target = target
        self.translator = GoogleTranslator(source='auto', target=target)

    @sleep_and_retry
    @limits(calls=5, period=timedelta(seconds=1).total_seconds())
    def translate(self, text):
        return self.translator.translate(text)

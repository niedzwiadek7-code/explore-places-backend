from abc import ABC, abstractmethod


class DataMigrationService(ABC):
    @abstractmethod
    def __init__(self, credentials=dict):
        pass

    @abstractmethod
    def required_arguments(self):
        pass

    @abstractmethod
    def make_request(self, url, method='GET', data=None):
        pass

    @abstractmethod
    def migrate(self, args):
        pass

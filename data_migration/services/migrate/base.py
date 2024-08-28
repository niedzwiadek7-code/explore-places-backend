from abc import ABC, abstractmethod


class DataMigrationService(ABC):
    @abstractmethod
    def __init__(self, credentials=dict):
        pass

    @abstractmethod
    def required_arguments(self):
        pass

    @abstractmethod
    def fetch_data(self, args):
        pass

    # @abstractmethod
    # def migrate(self, args):
    #     pass

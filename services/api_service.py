import requests
from requests.exceptions import RequestException
import logging


class APIService:
    def __init__(self, base_url):
        self.base_url = base_url
        self.logger = logging.getLogger(__name__)

    def get(self, endpoint, query_params=None):
        try:
            if query_params:
                endpoint += "?" + "&".join([f"{k}={v}" for k, v in query_params.items()])

            self.logger.info(f"Fetching data from {self.base_url + endpoint} - get method")
            response = requests.get(self.base_url + endpoint)
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            self.logger.error(f"Error while fetching data from {self.base_url + endpoint}: {e}")

    def request(self, method, endpoint, query_params=None, data=None):
        # TODO: for each request generate a new uuid
        try:
            if query_params:
                endpoint += "?" + "&".join([f"{k}={v}" for k, v in query_params.items()])

            self.logger.info(f"Fetching data from {self.base_url + endpoint} - {method} method")
            self.logger.info(f"Data: {data}")
            response = requests.request(
                method=method,
                url=self.base_url + endpoint,
                data=data
            )

            self.logger.info(f"Response: {response.json()}")
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            self.logger.error(f"Error while fetching data from {self.base_url + endpoint}: {e}")

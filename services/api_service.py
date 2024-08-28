import requests
from ratelimit import sleep_and_retry, limits
from requests.exceptions import RequestException
import logging


class APIService:
    def __init__(self, base_url, limit=None, period=None):
        self.base_url = base_url
        self.logger = logging.getLogger(__name__)

        def set_rate_limit(method):
            return sleep_and_retry(limits(calls=limit, period=period)(method))

        if limit and period:
            self.get = set_rate_limit(self.get)
            self.request = set_rate_limit(self.request)

    def get(self, endpoint, query_params=None):
        try:
            if query_params:
                endpoint += "?" + "&".join([f"{k}={v}" for k, v in query_params.items()])

            self.logger.debug(f"Fetching data from {self.base_url + endpoint} - get method")
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

            self.logger.debug(f"Fetching data from {self.base_url + endpoint} - {method} method")
            self.logger.debug(f"Data: {data}")
            response = requests.request(
                method=method,
                url=self.base_url + endpoint,
                data=data
            )

            self.logger.debug(f"Response: {response.json()}")
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            self.logger.error(f"Error while fetching data from {self.base_url + endpoint}: {e}")
            raise RequestException(e)

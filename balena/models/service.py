import sys

from ..base_request import BaseRequest
from ..settings import Settings
from .. import exceptions


class Service:
    """
    This class implements service model for balena python SDK.

    """

    def __init__(self):
        self.base_request = BaseRequest()
        self.settings = Settings()

    def __get_by_option(self, key, value):
        """
        Private function to get a specific service using any possible key.

        Args:
            key (str): query field.
            value (str): key's value.

        Returns:
            list: service info.

        """

        params = {
            'filter': key,
            'eq': value
        }

        services = self.base_request.request(
            'service', 'GET', params=params,
            endpoint=self.settings.get('pine_endpoint')
        )

        return services['d']

    def get_all_by_application(self, app_id):
        """
        Get all services from an application.

        Args:
            app_id (str): application id.

        Returns:
            list: service info.

        """

        return self.__get_by_option('application', app_id)

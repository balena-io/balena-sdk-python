import sys

from ..base_request import BaseRequest
from ..settings import Settings
from .. import exceptions


class ServiceInstall:
    """
    This class implements service_install model for balena python SDK.
    This is low level class and is not meant to be used by end users directly.

    """

    def __init__(self):
        self.base_request = BaseRequest()
        self.settings = Settings()

    def __get_by_option(self, key, value):
        """
        Private function to get a specific image_install using any possible key.

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

        return self.base_request.request(
            'service_install', 'GET', params=params,
            endpoint=self.settings.get('pine_endpoint')
        )['d']

    def get_all_by_device(self, device_id):
        """
        Get all service_install from a device.

        Args:
            device_id (str): device id.

        Returns:
            list: service_install info.

        """

        return self.__get_by_option('device', device_id)

import sys
import re

from ..base_request import BaseRequest
from ..settings import Settings


def _normalize_device_type(dev_type):
    if dev_type['state'] is 'DISCONTINUED':
        dev_type['name'] = re.sub(r'\((PREVIEW|EXPERIMENTAL)\)', '(DISCONTINUED)', dev_type['name'])
    if dev_type['state'] == 'PREVIEW':
        dev_type['state'] = 'ALPHA'
        dev_type['name'] = dev_type['name'].replace('(PREVIEW)', '(ALPHA)')
    if dev_type['state'] == 'EXPERIMENTAL':
        dev_type['state'] = 'NEW'
        dev_type['name'] = dev_type['name'].replace('(EXPERIMENTAL)', ('NEW'))
    if dev_type['slug'] == 'raspberry-pi':
        dev_type['name'] = 'Raspberry Pi (v1 or Zero)'
    return dev_type


class Config:
    """
    This class implements configuration model for balena python SDK.

    Attributes:
        _config (dict): caching configuration.

    """

    def __init__(self):
        self.base_request = BaseRequest()
        self.settings = Settings()
        self._config = {}
        self._device_types = None

    def _get_config(self, key):
        if self._config:
            return self._config[key]
        # Load all config again
        self.get_all()
        return self._config[key]

    def get_all(self):
        """
        Get all configuration.

        Returns:
            dict: configuration information.

        Examples:
            >>> balena.models.config.get_all()
            { all configuration details }

        """

        if not self._config:
            self._config = self.base_request.request(
                'config', 'GET', endpoint=self.settings.get('api_endpoint'))
        return self._config

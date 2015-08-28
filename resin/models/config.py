import sys

from ..base_request import BaseRequest
from ..settings import Settings

class Config(object):
	"""
    This class implements configuration model for Resin Python SDK.

    Attributes:
		_config (dict): caching configuration.
    
    """

	def __init__(self):
		self.base_request = BaseRequest()
		self.settings = Settings()
		self._config = None

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

        """

		if self._config is None:
			self._config = self.base_request.request('/config', 'GET', endpoint=self.settings.get('pine_endpoint'))
		return self._config

	def get_pubnub_keys(self):
		"""
        Get PubNub keys from configuration.

        Returns:
            dict: including PubNub subscribe_key and publish_key.

        """

		return self._get_config('pubnub')

	def get_device_types(self):
		"""
        Get device types configuration.

        Returns:
            list: device types information.

        """

		return self._get_config('deviceTypes')

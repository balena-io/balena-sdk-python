from sets import Set
import json

from ..base_request import BaseRequest
from ..settings import Settings
from .. import exceptions

NETWORK_WIFI = 'wifi'
NETWORK_ETHERNET = 'ethernet'

NETWORK_TYPES = [
	NETWORK_WIFI,
	NETWORK_ETHERNET
]

VALID_OPTIONS = [
	'network',
	'appId',
	'wifiSsid',
	'wifiKey',
	'appUpdatePollInterval'
]

class DeviceOs(object):
	"""
    This class implements device os model for Resin Python SDK.
    
    """

	def __init__(self):
		self.base_request = BaseRequest()
		self.settings = Settings()		

	def download(self, raw=None, **data):
		"""
        Download an OS image.

        Args:
            raw (bool): determining function return value.
            **data: os parameters keyword arguments.
            	Details about os parameters can be found in parse_params function

        Returns:
            object: 
            	If raw is True, urllib3.HTTPResponse object is returned.
            	If raw is False, original response object is returned.

        Notes: 
        	default OS image file name can be found in response headers.

        """

		self.params = self.parse_params(**data)
		response = self.base_request.request('download', 'POST', data=data, endpoint=self.settings.get('api_endpoint'), stream=True)
		if raw:
			# return urllib3.HTTPResponse object
			return response.raw
		else:
			return response

	def parse_params(self, **params):
		"""
        Validate parameters for downloading device OS image.

        Args:
            **parameters: os parameters keyword arguments.

        Returns:
        	dict: validated parameters.

       	Raise:
       		MissingOption: if mandatory option are missing.
       		InvalidOption: if appId or network are invalid (appId is not a number or parseable string. network is not in NETWORK_TYPES)
       		NonAllowedOption: if a non supported option is passed. 

        """
        
		if 'appId' not in params:
			raise exceptions.MissingOption('appId')

		try:
			params['appId'] = int(params['appId'])
		except ValueError:
			raise exceptions.InvalidOption('appId')

		if 'network' not in params:
			raise exceptions.MissingOption('network')

		if params['network'] not in NETWORK_TYPES:
			raise exceptions.InvalidOption('network')


		if params['network'] == NETWORK_WIFI:
			if 'wifiSsid' not in params:
				raise exceptions.MissingOption('wifiSsid')

			#if 'wifiKey' not in params:
			#	raise exceptions.MissingOption('wifiKey')

		invalid_params = Set(params).difference(Set(VALID_OPTIONS))
		if invalid_params:
			raise exceptions.NonAllowedOption(list(invalid_params))

		return params

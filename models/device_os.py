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

	def __init__(self):
		self.base_request = BaseRequest()
		self.settings = Settings()		

	def download(self, raw=None, **data):
		self.params = self.parse_params(**data)
		response = self.base_request.request('download', 'POST', data=data, endpoint=self.settings.get('api_endpoint'), stream=True)
		if raw:
			# return urllib3.HTTPResponse object
			return response.raw
		else:
			return response

	def parse_params(self, **params):
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

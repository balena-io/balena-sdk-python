from sets import Set
import json

from ..base_request import BaseRequest
from ..resources import Message
from ..settings import Settings
#import .exceptions as ResinException

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

class Os(object):

	def __init__(self):
		self.base_request = BaseRequest()
		self.settings = Settings()		

	def download(self, **params, raw=None):
		self.params = self.parse_params(**params)
		if raw:
			# return urllib3.HTTPResponse object
			return self.base_request.request('download', 'POST', endpoint=self.settings.get('api_endpoint'),stream=True).raw
		else:
			return self.base_request.request('download', 'POST', endpoint=self.settings.get('api_endpoint'),stream=True)

	def parse_params(self, **params):
		if 'appId' not in params:
			# TODO:raise ResinException.ResinMissingOption('appId')
			pass
		try:
			params['appId'] = int(params['appId'])
		except ValueError:
			# TODO:raise ResinException.ResinInvalidOption('appId', params['appId'])
			pass

		if 'network' not in params:
			# TODO:raise ResinException.ResinMissingOption('network')
			pass

		if params['network'] not in NETWORK_TYPES:
			# TODO: raise ResinException.ResinInvalidOption('network', params['network'])
			pass

		if params['network'] == NETWORK_WIFI:
			if 'wifiSsid' not in params:
				# TODO: raise ResinException.ResinMissingOption('wifiSsid')
				pass
			if 'wifiKey' not in params:
				# TODO: raise ResinException.ResinMissingOption('wifiKey')
				pass

		invalid_params = Set(params).difference(Set(VALID_OPTIONS))
		if invalid_params:
			# TODO: raise ResinException.ResinNonAllowedOption(list(invalid_params))
			pass

		return params
